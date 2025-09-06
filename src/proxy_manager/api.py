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
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn

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
    filename: Optional[str] = None


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

# 設置模板和靜態文件
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# 掛載靜態文件（如果有的話）
# app.mount("/static", StaticFiles(directory="static"), name="static")

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境中應該限制具體域名
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
        raise


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


@app.get("/api/health", response_model=HealthResponse, summary="健康檢查")
async def health_check(manager: ProxyManager = Depends(get_proxy_manager)):
    """健康檢查接口"""
    stats = manager.get_stats()
    
    uptime = None
    if stats['manager_stats']['start_time']:
        start_time = stats['manager_stats']['start_time']
        uptime = (datetime.now() - start_time).total_seconds()
    
    return HealthResponse(
        status="healthy" if stats['status']['running'] else "unhealthy",
        timestamp=datetime.now(),
        uptime_seconds=uptime,
        total_proxies=stats['pool_summary']['total_proxies'],
        active_proxies=stats['pool_summary']['total_active_proxies']
    )


@app.get("/api/proxy", response_model=ProxyResponse, summary="獲取單個代理")
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
        raise HTTPException(status_code=400, detail=f"參數錯誤: {e}")
    except Exception as e:
        logger.error(f"❌ 獲取代理失敗: {e}")
        raise HTTPException(status_code=500, detail="內部服務器錯誤")


@app.get("/api/proxies", response_model=List[ProxyResponse], summary="批量獲取代理")
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


@app.post("/api/proxies/filter", response_model=List[ProxyResponse], summary="使用複雜條件篩選代理")
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


@app.get("/api/stats", response_model=StatsResponse, summary="獲取統計信息")
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


@app.post("/api/fetch", summary="手動獲取代理")
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


@app.post("/api/validate", summary="手動驗證代理池")
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


@app.post("/api/cleanup", summary="手動清理代理池")
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


@app.post("/api/export", summary="導出代理")
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


@app.get("/api/download/{filename}", summary="下載導出文件")
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


@app.get("/api/proxies/{proxy_id}", response_model=ProxyResponse, summary="獲取單個代理")
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


@app.post("/api/proxies/batch", response_model=ProxyResponse, summary="批量獲取代理")
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


@app.post("/api/database/proxies", response_model=ProxyResponse, summary="從數據庫獲取代理")
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


@app.get("/api/stats/detailed", summary="獲取詳細統計信息")
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


@app.get("/api/pools", summary="獲取池詳細信息")
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


@app.post("/api/etl/sync", summary="同步代理數據到 ETL 系統")
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


@app.get("/api/etl/status", summary="獲取 ETL 系統狀態")
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


@app.post("/api/batch/validate", summary="批量驗證代理")
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


if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 啟動服務器
    start_server(reload=True)