"""Proxy Crawler 主應用程式入口點

這個模組提供了 Proxy Crawler 系統的主要 FastAPI 應用程式入口點。
包含基本的健康檢查和系統狀態端點。
"""

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse, Response
import os
import sys
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from config.settings import settings
from datetime import datetime
from typing import Dict, Any

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

proxy_manager_instance = None  # global placeholder

@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - startup/shutdown orchestration
    global proxy_manager_instance
    print("[LIFESPAN] startup begin")
    try:
        from src.proxy_manager.manager import ProxyManager, ProxyManagerConfig
        cfg = ProxyManagerConfig()
        proxy_manager_instance = ProxyManager(cfg)
        await proxy_manager_instance.start()
        # inject to proxy_manager.api module global
        try:
            import src.proxy_manager.api as proxy_api_module
            proxy_api_module.proxy_manager = proxy_manager_instance  # type: ignore
        except Exception as ie:  # noqa: BLE001
            print(f"[LIFESPAN] inject proxy manager failed: {ie}")
        print("[LIFESPAN] proxy manager started")
    except Exception as e:  # noqa: BLE001
        print(f"[LIFESPAN] startup error: {e}")
    yield
    print("[LIFESPAN] shutdown begin")
    try:
        if proxy_manager_instance:
            await proxy_manager_instance.stop()
            print("[LIFESPAN] proxy manager stopped")
    except Exception as e:  # noqa: BLE001
        print(f"[LIFESPAN] shutdown error: {e}")

app = FastAPI(
    title="Proxy Crawler & Management System",
    description="專業的代理伺服器爬取與管理系統",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 基本指標
REQUEST_COUNTER = Counter("http_requests_total", "Total HTTP requests", ["method", "path"])
POOL_GAUGE = Gauge("proxy_pool_active_total", "Active proxies per pool", ["pool"])


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):  # pragma: no cover
    response = await call_next(request)
    try:
        REQUEST_COUNTER.labels(method=request.method, path=request.url.path).inc()
    except Exception:  # noqa: BLE001
        pass
    return response

# 導入並掛載代理管理器 API
try:
    from src.proxy_manager import api as proxy_api_module  # import module to access app
    for route in proxy_api_module.app.routes:  # merge without submount
        app.routes.append(route)
    print("✅ 代理管理器 API 路由已合併")
except ImportError as e:
    print(f"⚠️ 無法載入代理管理器 API: {e}")

## Removed deprecated on_event startup in favor of lifespan

# 導入並掛載 ETL API
try:
    from src.etl.etl_api import etl_app
    app.mount("/etl", etl_app)
    print("✅ ETL API 已掛載到 /etl")
except ImportError as e:
    print(f"⚠️ 無法載入 ETL API: {e}")

# 導入並掛載 HTML to Markdown API
try:
    from src.html_to_markdown.api_server import app as html2md_api
    app.mount("/html2md", html2md_api)
    print("✅ HTML to Markdown API 已掛載到 /html2md")
except ImportError as e:
    print(f"⚠️ 無法載入 HTML to Markdown API: {e}")


@app.get("/")
async def root() -> Dict[str, Any]:
    """根路徑端點
    
    Returns:
        Dict[str, Any]: 包含系統基本資訊的字典
    """
    return {
        "message": "Proxy Crawler & Management System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": settings.environment
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康檢查端點
    
    Returns:
        Dict[str, Any]: 系統健康狀態資訊
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": "connected",  # 實際應用中應檢查資料庫連接
            "redis": "connected",     # 實際應用中應檢查 Redis 連接
            "crawler": "ready"
        }
    }


@app.get("/status")
async def system_status() -> Dict[str, Any]:
    """系統狀態端點
    
    Returns:
        Dict[str, Any]: 詳細的系統狀態資訊
    """
    return {
        "system": {
            "python_version": sys.version,
            "environment": settings.environment,
            "working_directory": os.getcwd(),
            "timestamp": datetime.now().isoformat()
        },
        "configuration": {
            # 脫敏：僅顯示是否設定，不顯示實際敏感值
            "database_configured": bool(os.getenv("DB_USER")) and bool(os.getenv("DB_NAME")),
            "redis_configured": bool(os.getenv("REDIS_SERVICE")),
            "metrics_enabled": settings.enable_metrics
        }
    }


@app.get("/metrics")
async def metrics():  # pragma: no cover
    if not settings.enable_metrics:
        return JSONResponse(status_code=404, content={"detail": "Metrics disabled"})
    try:
        from src.proxy_manager.api import proxy_manager  # type: ignore
        if proxy_manager:
            stats = proxy_manager.pool_manager.get_summary()
            for pool_name, pool_stats in stats.items():
                POOL_GAUGE.labels(pool=pool_name).set(pool_stats.get("active_count", 0))
    except Exception:  # noqa: BLE001
        pass
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    
    # 開發模式啟動
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )