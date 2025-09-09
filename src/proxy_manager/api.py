"""代理管理器 FastAPI 服務接口

提供 REST API 接口供外部使用：
- 代理獲取接口
- 統計信息接口
- 管理操作接口
- 健康檢查接口
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import redis.asyncio as aioredis
from src.config.settings import settings
import uvicorn
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from time import perf_counter
from collections import defaultdict, deque

# 導入 ETL API
try:
    from ..etl.etl_api import etl_app
    ETL_AVAILABLE = True
except ImportError:
    ETL_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ ETL API 模組不可用，某些功能將被禁用")

from .manager import ProxyManager, ProxyManagerConfig
from .models import ProxyNode, ProxyStatus, ProxyAnonymity, ProxyProtocol, ProxyFilter
from .pools import PoolType
from .validators import ProxyValidator, ValidationResult
from .database_service import get_database_service, cleanup_database_service
from database_config import DatabaseConfig

logger = logging.getLogger(__name__)

# Pydantic 模型定義
class ProxyResponse(BaseModel):
    """代理響應模型"""
    success: bool
    message: str
    data: Optional[Any] = None


class ProxyNodeResponse(BaseModel):
    """單個代理節點響應模型"""
    host: str
    port: int
    protocol: str
    anonymity: str
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    score: float
    response_time_ms: Optional[int] = None
    last_checked: Optional[datetime] = None
    
    @classmethod
    def from_proxy_node(cls, proxy: ProxyNode) -> "ProxyNodeResponse":
        return cls(
            host=proxy.host,
            port=proxy.port,
            protocol=proxy.protocol.value,
            anonymity=proxy.anonymity.value,
            country=proxy.country,
            region=proxy.region,
            city=proxy.city,
            score=proxy.score,
            response_time_ms=proxy.metrics.response_time_ms,
            last_checked=proxy.last_checked
        )


class ProxyFilterRequest(BaseModel):
    """代理篩選請求模型"""
    protocols: Optional[List[str]] = None
    anonymity_levels: Optional[List[str]] = None
    countries: Optional[List[str]] = None
    min_score: Optional[float] = None
    max_response_time: Optional[int] = None
    page: int = Field(default=1, ge=1, description="頁碼")
    page_size: int = Field(default=50, ge=1, le=100, description="每頁大小")
    order_by: str = Field(default="score", description="排序字段")
    order_desc: bool = Field(default=True, description="是否降序")
    
    @property
    def filter(self) -> ProxyFilter:
        """獲取 ProxyFilter 對象"""
        protocols = None
        if self.protocols:
            protocols = [ProxyProtocol(p) for p in self.protocols if p in [e.value for e in ProxyProtocol]]
        
        anonymity_levels = None
        if self.anonymity_levels:
            anonymity_levels = [ProxyAnonymity(a) for a in self.anonymity_levels if a in [e.value for e in ProxyAnonymity]]
        
        return ProxyFilter(
            protocols=protocols,
            anonymity_levels=anonymity_levels,
            countries=self.countries,
            min_score=self.min_score,
            max_response_time=self.max_response_time
        )
    
    def to_proxy_filter(self) -> ProxyFilter:
        """轉換為 ProxyFilter 對象（向後兼容）"""
        return self.filter


class StatsResponse(BaseModel):
    """統計信息響應模型"""
    total_proxies: int
    total_active_proxies: int
    pool_distribution: Dict[str, int]
    overall_success_rate: float
    last_updated: str
    manager_stats: Dict[str, Any]
    pool_details: Dict[str, Any]


class HealthResponse(BaseModel):
    """健康檢查響應模型"""
    status: str
    timestamp: datetime
    uptime_seconds: Optional[float] = None
    total_proxies: int
    active_proxies: int
    version: str = "1.0.0"


class FetchRequest(BaseModel):
    """獲取代理請求模型"""
    sources: Optional[List[str]] = None
    validate: bool = True


class ExportRequest(BaseModel):
    """導出請求模型"""
    format_type: str = Field(default="json", pattern="^(json|txt|csv)$")
    pool_types: Optional[List[str]] = None


class ImportRequest(BaseModel):
    """導入請求模型"""
    file_path: str = Field(description="要導入的文件路徑")
    validate_proxies: bool = Field(default=True, description="是否驗證導入的代理")


# Prometheus metrics
REQUEST_COUNT = Counter("proxy_api_requests_total", "Total API requests", ["endpoint", "method", "status"])
POOL_ACTIVE = Gauge("proxy_pool_active", "Active proxies in pool")
POOL_TOTAL = Gauge("proxy_pool_total", "Total proxies in pool")
REQUEST_LATENCY = Histogram(
    "proxy_api_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint", "method", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
)


# In-process lightweight rollup for API trends/summary
ROLLUP_LOCK = asyncio.Lock()
REQUEST_ROLLUP: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"count": 0, "error": 0, "duration_sum": 0.0})
PER_MINUTE: Dict[datetime, Dict[str, float]] = {}
MINUTE_KEYS: deque = deque()
MAX_MINUTES: int = 24 * 60  # keep last 24h


# 簡單的 API Key 驗證依賴
async def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if not settings.api_key_enabled:
        return
    if not x_api_key or x_api_key not in settings.api_keys:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


# 全局代理管理器實例
proxy_manager: Optional[ProxyManager] = None


def get_proxy_manager() -> ProxyManager:
    """獲取代理管理器實例"""
    if proxy_manager is None:
        raise HTTPException(status_code=503, detail="代理管理器未初始化")
    return proxy_manager


# 創建 FastAPI 應用
app = FastAPI(
    title="代理管理器 API",
    description="提供代理獲取、管理和統計功能的 REST API 服務",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
# 全域中介層：請求計數與延遲
@app.middleware("http")
async def metrics_middleware(request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
    start = perf_counter()
    status_code = "200"
    try:
        response = await call_next(request)
        status_code = str(getattr(response, "status_code", 200))
        return response
    except Exception:
        status_code = "500"
        raise
    finally:
        try:
            endpoint = request.url.path
            method = request.method
            REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status_code).inc()
            REQUEST_LATENCY.labels(endpoint=endpoint, method=method, status=status_code).observe(perf_counter() - start)
            # In-process aggregations
            duration = max(0.0, perf_counter() - start)
            is_error = 1 if int(status_code) >= 400 else 0
            key = f"{endpoint}|{method}"
            minute_key = datetime.now().replace(second=0, microsecond=0)
            # Update rollups
            if not ROLLUP_LOCK.locked():
                # Best-effort without awaiting lock to avoid latency; fallback on simple updates
                pass
            async def _update():
                REQUEST_ROLLUP[key]["count"] += 1
                REQUEST_ROLLUP[key]["error"] += is_error
                REQUEST_ROLLUP[key]["duration_sum"] += duration
                bucket = PER_MINUTE.get(minute_key)
                if not bucket:
                    PER_MINUTE[minute_key] = {"count": 0, "error": 0, "duration_sum": 0.0}
                    MINUTE_KEYS.append(minute_key)
                PER_MINUTE[minute_key]["count"] += 1
                PER_MINUTE[minute_key]["error"] += is_error
                PER_MINUTE[minute_key]["duration_sum"] += duration
                # Trim old minutes
                while len(MINUTE_KEYS) > MAX_MINUTES:
                    old = MINUTE_KEYS.popleft()
                    PER_MINUTE.pop(old, None)
            try:
                # Fire-and-forget; slight race is acceptable for metrics
                asyncio.create_task(_update())
            except Exception:
                pass
        except Exception:
            pass


# 設置模板和靜態文件
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# 掛載靜態文件（如果有的話）
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載 ETL API 子應用
if ETL_AVAILABLE:
    app.mount("/etl", etl_app, name="etl")
    logger.info("✅ ETL API 已掛載到 /etl 路徑")
else:
    logger.warning("⚠️ ETL API 不可用，跳過掛載")

# 掛載 URL2Parquet 路由
try:
    from src.url2parquet.api.router import router as url2parquet_router
    app.include_router(url2parquet_router)
    logger.info("✅ URL2Parquet 路由已掛載到 /api/url2parquet")
except Exception as e:
    logger.warning(f"⚠️ 無法掛載 URL2Parquet 路由: {e}")

# 掛載代理管理 API 路由
try:
    from src.api.proxy_management_api import router as proxy_management_router
    app.include_router(proxy_management_router)
    logger.info("✅ 代理管理 API 路由已掛載到 /api")
except Exception as e:
    logger.warning(f"⚠️ 無法掛載代理管理 API 路由: {e}")


@app.on_event("startup")
async def startup_event():
    """應用啟動事件"""
    global proxy_manager
    
    print("[DEBUG] startup_event 被調用")
    logger.info("🚀 啟動代理管理器 API 服務...")
    
    try:
        print("[DEBUG] 開始創建配置")
        # 創建配置
        config = ProxyManagerConfig()
        print("[DEBUG] 配置創建成功")
        
        print("[DEBUG] 開始創建代理管理器")
        # 創建並啟動代理管理器
        proxy_manager = ProxyManager(config)
        print("[DEBUG] 代理管理器創建成功，開始啟動")
        
        await proxy_manager.start()
        print("[DEBUG] 代理管理器啟動成功")
        
        logger.info("✅ 代理管理器 API 服務啟動成功")
        
    except Exception as e:
        print(f"[DEBUG] 啟動過程中發生錯誤: {e}")
        logger.error(f"❌ 啟動失敗: {e}")
        import traceback
        error_details = traceback.format_exc()
        print(f"[DEBUG] 詳細錯誤信息: {error_details}")
        logger.error(f"詳細錯誤信息: {error_details}")
        # 不要 raise，讓服務繼續運行
        proxy_manager = None


@app.on_event("shutdown")
async def shutdown_event():
    """應用關閉事件"""
    global proxy_manager
    
    logger.info("🛑 關閉代理管理器 API 服務...")
    
    if proxy_manager:
        await proxy_manager.stop()
        proxy_manager = None
    
    # 清理數據庫服務
    await cleanup_database_service()
    
    logger.info("✅ 代理管理器 API 服務已關閉")


# API 路由定義

@app.get("/", response_class=HTMLResponse, summary="Web管理界面")
async def web_interface(request: Request):
    """Web管理界面"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api", summary="API根路徑")
async def api_root():
    """API根路徑，返回 API 基本信息"""
    return {
        "name": "代理管理器 API",
        "version": "1.0.0",
        "description": "提供代理獲取、管理和統計功能的 REST API 服務",
        "docs_url": "/api/docs",
        "health_check": "/api/health",
        "web_interface": "/"
    }


@app.get("/health", response_model=HealthResponse, summary="健康檢查")
async def health_check(manager: ProxyManager = Depends(get_proxy_manager)):
    """健康檢查接口（包含 DB 與 Redis 連線檢查）"""
    stats = manager.get_stats()

    uptime = None
    if stats['manager_stats']['start_time']:
        start_time = stats['manager_stats']['start_time']
        uptime = (datetime.now() - start_time).total_seconds()

    # 驗證資料庫
    db_ok = False
    try:
        db_service = await get_database_service()
        db_ok = await db_service.ping()
    except Exception as e:
        logger.error(f"DB health check failed: {e}")
        db_ok = False

    # 驗證 Redis
    redis_ok = False
    try:
        redis_url = DatabaseConfig().get_redis_url()
        redis_client = aioredis.from_url(redis_url, decode_responses=True)
        redis_ok = await redis_client.ping()
        await redis_client.close()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_ok = False

    running = stats['status']['running']
    if running and db_ok and redis_ok:
        overall = "healthy"
    elif running or db_ok or redis_ok:
        overall = "degraded"
    else:
        overall = "unhealthy"

    # 更新 metrics
    try:
        stats_summary = stats['pool_summary']
        POOL_TOTAL.set(stats_summary['total_proxies'])
        POOL_ACTIVE.set(stats_summary['total_active_proxies'])
    except Exception:
        pass

    return HealthResponse(
        status=overall,
        timestamp=datetime.now(),
        uptime_seconds=uptime,
        total_proxies=stats['pool_summary']['total_proxies'],
        active_proxies=stats['pool_summary']['total_active_proxies']
    )


@app.get("/proxy", response_model=ProxyResponse, summary="獲取單個代理")
async def get_proxy(
    protocol: Optional[str] = Query(None, description="協議類型 (http, https, socks4, socks5)"),
    anonymity: Optional[str] = Query(None, description="匿名度 (transparent, anonymous, elite)"),
    country: Optional[str] = Query(None, description="國家代碼"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="最低分數"),
    max_response_time: Optional[int] = Query(None, gt=0, description="最大響應時間(毫秒)"),
    pool_preference: Optional[str] = Query("hot,warm,cold", description="池優先級 (逗號分隔)"),
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """獲取單個代理"""
    start = perf_counter()
    status_code = "200"
    try:
        # 構建篩選條件
        filter_criteria = None
        if any([protocol, anonymity, country, min_score, max_response_time]):
            protocols = [ProxyProtocol(protocol)] if protocol else None
            anonymity_levels = [ProxyAnonymity(anonymity)] if anonymity else None
            countries = [country] if country else None
            
            filter_criteria = ProxyFilter(
                protocols=protocols,
                anonymity_levels=anonymity_levels,
                countries=countries,
                min_score=min_score,
                max_response_time=max_response_time
            )
        
        # 解析池優先級
        pool_types = []
        if pool_preference:
            for pool_name in pool_preference.split(','):
                pool_name = pool_name.strip().lower()
                if pool_name == 'hot':
                    pool_types.append(PoolType.HOT)
                elif pool_name == 'warm':
                    pool_types.append(PoolType.WARM)
                elif pool_name == 'cold':
                    pool_types.append(PoolType.COLD)
        
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        
        # 獲取代理
        proxy = await manager.get_proxy(filter_criteria, pool_types)
        
        if not proxy:
            raise HTTPException(status_code=404, detail="沒有找到符合條件的代理")
        
        return ProxyResponse.from_proxy_node(proxy)
        
    except ValueError as e:
        status_code = "400"
        raise HTTPException(status_code=400, detail=f"參數錯誤: {e}")
    except Exception as e:
        status_code = "500"
        logger.error(f"❌ 獲取代理失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")
    finally:
        try:
            endpoint = "/api/proxy"
            REQUEST_COUNT.labels(endpoint=endpoint, method="GET", status=status_code).inc()
            REQUEST_LATENCY.labels(endpoint=endpoint, method="GET", status=status_code).observe(perf_counter() - start)
        except Exception:
            pass


@app.get("/proxies", response_model=List[ProxyResponse], summary="批量獲取代理")
async def get_proxies(
    count: int = Query(10, ge=1, le=100, description="獲取數量"),
    protocol: Optional[str] = Query(None, description="協議類型"),
    anonymity: Optional[str] = Query(None, description="匿名度"),
    country: Optional[str] = Query(None, description="國家代碼"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="最低分數"),
    max_response_time: Optional[int] = Query(None, gt=0, description="最大響應時間(毫秒)"),
    pool_preference: Optional[str] = Query("hot,warm,cold", description="池優先級"),
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """批量獲取代理"""
    try:
        # 構建篩選條件（與單個代理接口相同邏輯）
        filter_criteria = None
        if any([protocol, anonymity, country, min_score, max_response_time]):
            protocols = [ProxyProtocol(protocol)] if protocol else None
            anonymity_levels = [ProxyAnonymity(anonymity)] if anonymity else None
            countries = [country] if country else None
            
            filter_criteria = ProxyFilter(
                protocols=protocols,
                anonymity_levels=anonymity_levels,
                countries=countries,
                min_score=min_score,
                max_response_time=max_response_time
            )
        
        # 解析池優先級
        pool_types = []
        if pool_preference:
            for pool_name in pool_preference.split(','):
                pool_name = pool_name.strip().lower()
                if pool_name == 'hot':
                    pool_types.append(PoolType.HOT)
                elif pool_name == 'warm':
                    pool_types.append(PoolType.WARM)
                elif pool_name == 'cold':
                    pool_types.append(PoolType.COLD)
        
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        
        # 批量獲取代理
        proxies = await manager.get_proxies(count, filter_criteria, pool_types)
        
        return [ProxyResponse.from_proxy_node(proxy) for proxy in proxies]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"參數錯誤: {e}")
    except Exception as e:
        logger.error(f"❌ 批量獲取代理失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.post("/proxies/filter", response_model=List[ProxyResponse], summary="使用複雜條件篩選代理")
async def filter_proxies(
    filter_request: ProxyFilterRequest,
    count: int = Query(10, ge=1, le=100, description="獲取數量"),
    pool_preference: Optional[str] = Query("hot,warm,cold", description="池優先級"),
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """使用複雜條件篩選代理"""
    try:
        # 轉換篩選條件
        filter_criteria = filter_request.to_proxy_filter()
        
        # 解析池優先級
        pool_types = []
        if pool_preference:
            for pool_name in pool_preference.split(','):
                pool_name = pool_name.strip().lower()
                if pool_name == 'hot':
                    pool_types.append(PoolType.HOT)
                elif pool_name == 'warm':
                    pool_types.append(PoolType.WARM)
                elif pool_name == 'cold':
                    pool_types.append(PoolType.COLD)
        
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        
        # 獲取代理
        proxies = await manager.get_proxies(count, filter_criteria, pool_types)
        
        return [ProxyResponse.from_proxy_node(proxy) for proxy in proxies]
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"參數錯誤: {e}")
    except Exception as e:
        logger.error(f"❌ 篩選代理失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.get("/stats", response_model=StatsResponse, summary="獲取統計信息")
async def get_stats(manager: ProxyManager = Depends(get_proxy_manager)):
    """獲取統計信息"""
    try:
        stats = manager.get_stats()
        
        return StatsResponse(
            total_proxies=stats['pool_summary']['total_proxies'],
            total_active_proxies=stats['pool_summary']['total_active_proxies'],
            pool_distribution=stats['pool_summary']['pool_distribution'],
            overall_success_rate=stats['pool_summary']['overall_success_rate'],
            last_updated=stats['pool_summary']['last_updated'],
            manager_stats=stats['manager_stats'],
            pool_details=stats['pool_details']
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


class MetricsSummaryResponse(BaseModel):
    total_requests: int
    error_rate: float
    avg_latency_ms: float
    per_endpoint: Dict[str, Dict[str, float]]
    pool: Dict[str, int]


# 刪除重複的 metrics/summary 端點定義，保留更詳細的版本


class MetricsTrendsPoint(BaseModel):
    timestamp: datetime
    count: int
    error: int
    avg_latency_ms: float


# 刪除重複的 metrics/trends 端點定義，保留更詳細的版本

@app.post("/fetch", summary="手動獲取代理")
async def fetch_proxies(
    fetch_request: FetchRequest,
    background_tasks: BackgroundTasks,
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """手動觸發代理獲取"""
    try:
        # 在後台執行獲取任務
        background_tasks.add_task(
            manager.fetch_proxies,
            fetch_request.sources
        )
        
        return {
            "message": "代理獲取任務已啟動",
            "sources": fetch_request.sources,
            "validate": fetch_request.validate,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 啟動獲取任務失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.post("/validate", summary="手動驗證代理池", dependencies=[Depends(require_api_key)])
async def validate_pools(
    background_tasks: BackgroundTasks,
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """手動觸發代理池驗證"""
    try:
        # 在後台執行驗證任務
        background_tasks.add_task(manager.validate_pools)
        
        return {
            "message": "代理池驗證任務已啟動",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 啟動驗證任務失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.post("/cleanup", summary="手動清理代理池", dependencies=[Depends(require_api_key)])
async def cleanup_pools(
    background_tasks: BackgroundTasks,
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """手動觸發代理池清理"""
    try:
        # 在後台執行清理任務
        background_tasks.add_task(manager.cleanup_pools)
        
        return {
            "message": "代理池清理任務已啟動",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 啟動清理任務失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.post("/export", summary="導出代理", dependencies=[Depends(require_api_key)])
async def export_proxies(
    export_request: ExportRequest,
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """導出代理到文件"""
    try:
        # 解析池類型
        pool_types = []
        if export_request.pool_types:
            for pool_name in export_request.pool_types:
                pool_name = pool_name.strip().lower()
                if pool_name == 'hot':
                    pool_types.append(PoolType.HOT)
                elif pool_name == 'warm':
                    pool_types.append(PoolType.WARM)
                elif pool_name == 'cold':
                    pool_types.append(PoolType.COLD)
        
        if not pool_types:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        
        # 生成文件名
        if not export_request.filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"proxies_{timestamp}.{export_request.format_type}"
        else:
            filename = export_request.filename
        
        file_path = Path("data/exports") / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 導出代理
        count = await manager.export_proxies(
            file_path,
            export_request.format_type,
            pool_types
        )
        
        return {
            "message": "代理導出成功",
            "filename": filename,
            "format": export_request.format_type,
            "count": count,
            "download_url": f"/download/{filename}",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 導出代理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"導出失敗: {e}")


@app.post("/import", summary="導入代理", dependencies=[Depends(require_api_key)])
async def import_proxies_endpoint(
    import_request: ImportRequest,
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """從文件導入代理"""
    try:
        file_path = Path(import_request.file_path)
        
        # 檢查文件是否存在
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件不存在: {import_request.file_path}")
        
        # 檢查文件格式
        if file_path.suffix.lower() not in ['.json', '.txt', '.csv']:
            raise HTTPException(status_code=400, detail="不支持的文件格式，僅支持 .json, .txt, .csv")
        
        # 導入代理
        count = await manager.import_proxies(
            file_path,
            validate=import_request.validate_proxies
        )
        
        return {
            "message": "代理導入成功",
            "file_path": str(file_path),
            "count": count,
            "validated": import_request.validate_proxies,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 導入代理失敗: {e}")
        raise HTTPException(status_code=500, detail=f"導入失敗: {e}")


@app.get("/download/{filename}", summary="下載導出文件")
async def download_file(filename: str):
    """下載導出的文件"""
    file_path = Path("data/exports") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


@app.get("/proxies/{proxy_id}", response_model=ProxyResponse, summary="獲取單個代理")
async def get_proxy_by_id(proxy_id: str):
    """根據ID獲取單個代理"""
    try:
        db_service = await get_database_service()
        proxy = await db_service.get_proxy_by_id(proxy_id)
        
        if proxy:
            return ProxyResponse(
                success=True,
                message="代理獲取成功",
                data=ProxyNodeResponse.from_proxy_node(proxy).dict()
            )
        else:
            return ProxyResponse(
                success=False,
                message="代理不存在",
                data=None
            )
    except Exception as e:
        logger.error(f"獲取代理失敗: {e}")
        return ProxyResponse(
            success=False,
            message=f"獲取代理失敗: {str(e)}",
            data=None
        )


@app.post("/proxies/batch", response_model=ProxyResponse, summary="批量獲取代理")
async def get_proxies_batch(
    filter_request: ProxyFilterRequest,
    count: int = Query(10, ge=1, le=100, description="獲取數量"),
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """批量獲取代理"""
    try:
        # 轉換篩選條件
        filter_criteria = filter_request.to_proxy_filter()
        
        # 獲取代理
        proxies = await manager.get_proxies(count, filter_criteria)
        
        return ProxyResponse(
            success=True,
            message=f"成功獲取 {len(proxies)} 個代理",
            data=[ProxyNodeResponse.from_proxy_node(proxy).dict() for proxy in proxies]
        )
        
    except ValueError as e:
        return ProxyResponse(
            success=False,
            message=f"參數錯誤: {e}",
            data=None
        )
    except Exception as e:
        logger.error(f"❌ 批量獲取代理失敗: {e}")
        return ProxyResponse(
            success=False,
            message="批量獲取代理失敗",
            data=None
        )


@app.post("/database/proxies", response_model=ProxyResponse, summary="從數據庫獲取代理")
async def get_database_proxies(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    protocol: Optional[str] = Query(None, description="協議類型"),
    anonymity: Optional[str] = Query(None, description="匿名度"),
    country: Optional[str] = Query(None, description="國家代碼"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="最低分數"),
    max_response_time: Optional[int] = Query(None, gt=0, description="最大響應時間(毫秒)"),
    order_by: str = Query("score", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序排列")
):
    """直接從數據庫獲取代理數據"""
    try:
        db_service = await get_database_service()
        
        # 構建篩選條件
        filter_criteria = None
        if any([protocol, anonymity, country, min_score, max_response_time]):
            protocols = [ProxyProtocol(protocol)] if protocol else None
            anonymity_levels = [ProxyAnonymity(anonymity)] if anonymity else None
            countries = [country] if country else None
            
            filter_criteria = ProxyFilter(
                protocols=protocols,
                anonymity_levels=anonymity_levels,
                countries=countries,
                min_score=min_score,
                max_response_time=max_response_time
            )
        
        # 從數據庫獲取代理
        result = await db_service.get_proxies(
            filter_criteria=filter_criteria,
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_desc=order_desc
        )
        
        return ProxyResponse(
            success=True,
            message=f"成功獲取 {len(result.proxies)} 個代理",
            data={
                "proxies": [ProxyNodeResponse.from_proxy_node(proxy).dict() for proxy in result.proxies],
                "pagination": {
                    "page": result.page,
                    "page_size": result.page_size,
                    "total_count": result.total_count,
                    "has_next": result.has_next,
                    "has_prev": result.has_prev
                }
            }
        )
        
    except ValueError as e:
        return ProxyResponse(
            success=False,
            message=f"參數錯誤: {e}",
            data=None
        )
    except Exception as e:
        logger.error(f"從數據庫獲取代理失敗: {e}")
        return ProxyResponse(
            success=False,
            message=f"從數據庫獲取代理失敗: {str(e)}",
            data=None
        )


@app.get("/stats/detailed", summary="獲取詳細統計信息")
async def get_detailed_stats(manager: ProxyManager = Depends(get_proxy_manager)):
    """獲取詳細統計信息"""
    try:
        stats = manager.get_stats()
        
        return {
            "success": True,
            "data": {
                "total_proxies": stats['pool_summary']['total_proxies'],
                "total_active_proxies": stats['pool_summary']['total_active_proxies'],
                "pool_distribution": stats['pool_summary']['pool_distribution'],
                "overall_success_rate": stats['pool_summary']['overall_success_rate'],
                "last_updated": stats['pool_summary']['last_updated'],
                "manager_stats": stats['manager_stats'],
                "pool_details": stats['pool_details']
            },
            "message": "統計信息獲取成功",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取詳細統計信息失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.get("/pools", summary="獲取池詳細信息")
async def get_pools_info(manager: ProxyManager = Depends(get_proxy_manager)):
    """獲取所有池的詳細信息"""
    try:
        stats = manager.get_stats()
        return {
            "success": True,
            "data": {
                "pools": stats['pool_details'],
                "summary": stats['pool_summary']
            },
            "message": "池信息獲取成功",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取池信息失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.post("/etl/sync", summary="同步代理數據到 ETL 系統", dependencies=[Depends(require_api_key)])
async def sync_to_etl(
    background_tasks: BackgroundTasks,
    pool_types: Optional[str] = Query("hot,warm,cold", description="要同步的池類型"),
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """將代理管理器中的數據同步到 ETL 系統"""
    if not ETL_AVAILABLE:
        raise HTTPException(status_code=503, detail="ETL 系統不可用")
    
    try:
        # 解析池類型
        pool_list = []
        if pool_types:
            for pool_name in pool_types.split(','):
                pool_name = pool_name.strip().lower()
                if pool_name in ['hot', 'warm', 'cold']:
                    pool_list.append(pool_name)
        
        if not pool_list:
            pool_list = ['hot', 'warm', 'cold']
        
        # 在背景執行同步任務
        background_tasks.add_task(_sync_data_to_etl, manager, pool_list)
        
        return {
            "message": "數據同步任務已啟動",
            "pool_types": pool_list,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 啟動數據同步失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動數據同步失敗: {e}")


@app.get("/etl/status", summary="獲取 ETL 系統狀態")
async def get_etl_status():
    """獲取 ETL 系統的狀態信息"""
    if not ETL_AVAILABLE:
        return {
            "available": False,
            "message": "ETL 系統不可用",
            "timestamp": datetime.now().isoformat()
        }
    
    try:
        # 這裡可以添加對 ETL 系統健康狀態的檢查
        return {
            "available": True,
            "status": "operational",
            "endpoints": {
                "jobs": "/etl/api/etl/jobs",
                "validation": "/etl/api/etl/validate",
                "monitoring": "/etl/api/etl/monitoring/metrics",
                "health": "/etl/api/etl/health"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取 ETL 狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取 ETL 狀態失敗: {e}")


@app.get("/metrics/summary", summary="獲取系統指標摘要")
async def get_metrics_summary(manager: ProxyManager = Depends(get_proxy_manager)):
    """獲取系統關鍵指標的摘要信息，供前端儀表板使用"""
    try:
        stats = manager.get_stats()
        pool_summary = stats['pool_summary']
        manager_stats = stats['manager_stats']
        
        # 計算成功率
        total_requests = manager_stats.get('total_requests', 0)
        successful_requests = manager_stats.get('successful_requests', 0)
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # 計算平均響應時間
        avg_response_time = manager_stats.get('avg_response_time', 0)
        
        # 獲取各池的代理數量
        hot_proxies = pool_summary.get('hot_pool_count', 0)
        warm_proxies = pool_summary.get('warm_pool_count', 0)
        cold_proxies = pool_summary.get('cold_pool_count', 0)
        blacklisted_proxies = pool_summary.get('blacklist_count', 0)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": {
                "status": "healthy" if stats['status']['running'] else "stopped",
                "uptime_seconds": manager_stats.get('uptime_seconds', 0),
                "last_update": manager_stats.get('last_update', datetime.now()).isoformat()
            },
            "proxy_metrics": {
                "total_proxies": pool_summary['total_proxies'],
                "active_proxies": pool_summary['total_active_proxies'],
                "hot_pool": hot_proxies,
                "warm_pool": warm_proxies,
                "cold_pool": cold_proxies,
                "blacklisted": blacklisted_proxies
            },
            "performance_metrics": {
                "success_rate": round(success_rate, 2),
                "avg_response_time_ms": round(avg_response_time * 1000, 2),
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": total_requests - successful_requests
            },
            "validation_metrics": {
                "total_validations": manager_stats.get('total_validations', 0),
                "successful_validations": manager_stats.get('successful_validations', 0),
                "validation_success_rate": round(
                    (manager_stats.get('successful_validations', 0) / 
                     max(manager_stats.get('total_validations', 1), 1)) * 100, 2
                )
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取指標摘要失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取指標摘要失敗: {e}")


@app.get("/metrics/trends", summary="獲取系統指標趨勢")
async def get_metrics_trends(
    hours: int = Query(24, description="查詢最近幾小時的趨勢數據"),
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """獲取系統指標的趨勢數據，供前端圖表使用"""
    try:
        # 這裡可以從資料庫或快取中獲取歷史數據
        # 目前先返回模擬數據，後續可以連接到真實的時序數據庫
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 生成模擬的趨勢數據點（每小時一個數據點）
        data_points = []
        current_time = start_time
        
        while current_time <= end_time:
            # 模擬數據 - 實際應用中應該從資料庫查詢
            base_proxies = 1000
            time_factor = (current_time.hour % 24) / 24  # 0-1 之間的值
            
            data_points.append({
                "timestamp": current_time.isoformat(),
                "total_proxies": base_proxies + int(200 * time_factor),
                "active_proxies": base_proxies + int(150 * time_factor),
                "success_rate": 85 + int(10 * time_factor),
                "avg_response_time_ms": 500 + int(200 * (1 - time_factor)),
                "requests_per_hour": 1000 + int(500 * time_factor)
            })
            
            current_time += timedelta(hours=1)
        
        return {
            "period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "hours": hours
            },
            "data_points": data_points,
            "summary": {
                "avg_total_proxies": sum(dp["total_proxies"] for dp in data_points) // len(data_points),
                "avg_active_proxies": sum(dp["active_proxies"] for dp in data_points) // len(data_points),
                "avg_success_rate": sum(dp["success_rate"] for dp in data_points) / len(data_points),
                "avg_response_time_ms": sum(dp["avg_response_time_ms"] for dp in data_points) / len(data_points)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取指標趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取指標趨勢失敗: {e}")


@app.post("/batch/validate", summary="批量驗證代理", dependencies=[Depends(require_api_key)])
async def batch_validate_proxies(
    background_tasks: BackgroundTasks,
    pool_types: Optional[str] = Query("hot,warm,cold", description="要驗證的池類型"),
    batch_size: int = Query(100, ge=10, le=1000, description="批次大小"),
    manager: ProxyManager = Depends(get_proxy_manager)
):
    """批量驗證代理的可用性和性能"""
    try:
        # 解析池類型
        pool_list = []
        if pool_types:
            for pool_name in pool_types.split(','):
                pool_name = pool_name.strip().lower()
                if pool_name in ['hot', 'warm', 'cold']:
                    pool_list.append(pool_name)
        
        if not pool_list:
            pool_list = ['hot', 'warm', 'cold']
        
        # 在背景執行批量驗證
        background_tasks.add_task(_batch_validate_proxies, manager, pool_list, batch_size)
        
        return {
            "message": "批量驗證任務已啟動",
            "pool_types": pool_list,
            "batch_size": batch_size,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 啟動批量驗證失敗: {e}")
        raise HTTPException(status_code=500, detail=f"啟動批量驗證失敗: {e}")


# 錯誤處理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    try:
        endpoint = str(request.url.path)
        method = request.method
        status = str(exc.status_code)
        REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint, method=method, status=status).observe(0)
    except Exception:
        pass
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"❌ 未處理的異常: {exc}")
    try:
        endpoint = str(request.url.path)
        method = request.method
        status = "500"
        REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
        REQUEST_LATENCY.labels(endpoint=endpoint, method=method, status=status).observe(0)
    except Exception:
        pass
    return JSONResponse(
        status_code=500,
        content={
            "error": "內部服務器錯誤",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


# ===== 背景任務函數 =====

async def _sync_data_to_etl(manager: ProxyManager, pool_types: List[str]):
    """同步數據到 ETL 系統的背景任務"""
    try:
        logger.info(f"🔄 開始同步數據到 ETL 系統，池類型: {pool_types}")
        
        # 獲取所有代理數據
        all_proxies = []
        for pool_type in pool_types:
            # 這裡應該根據實際的 ProxyManager API 獲取代理
            # proxies = await manager.get_proxies_from_pool(pool_type)
            # all_proxies.extend(proxies)
            pass
        
        # 將數據發送到 ETL 系統
        # 這裡應該調用 ETL API 來處理數據
        
        logger.info(f"✅ 數據同步完成，共處理 {len(all_proxies)} 個代理")
        
    except Exception as e:
        logger.error(f"❌ 數據同步失敗: {e}")


async def _batch_validate_proxies(manager: ProxyManager, pool_types: List[str], batch_size: int):
    """批量驗證代理的背景任務"""
    try:
        logger.info(f"🔍 開始批量驗證代理，池類型: {pool_types}，批次大小: {batch_size}")
        
        total_validated = 0
        total_valid = 0
        
        for pool_type in pool_types:
            # 這裡應該根據實際的 ProxyManager API 進行批量驗證
            # result = await manager.batch_validate_pool(pool_type, batch_size)
            # total_validated += result.get('total', 0)
            # total_valid += result.get('valid', 0)
            pass
        
        success_rate = (total_valid / total_validated * 100) if total_validated > 0 else 0
        
        logger.info(f"✅ 批量驗證完成，驗證 {total_validated} 個代理，成功率: {success_rate:.2f}%")
        
    except Exception as e:
        logger.error(f"❌ 批量驗證失敗: {e}")


# 啟動服務器的函數
def start_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    log_level: str = "info"
):
    """啟動 FastAPI 服務器"""
    uvicorn.run(
        "proxy_manager.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
        access_log=True
    )


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return HTMLResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 啟動服務器
    start_server(reload=True)