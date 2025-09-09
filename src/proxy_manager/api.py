"""Legacy api.py now serves mainly as an aggregator bootstrapping the modular route files.

Most endpoints have been migrated to dedicated route modules:
- routes_proxies.py
- routes_stats.py
- routes_maintenance.py
- routes_health_etl.py
- routes_database.py

Only shared exception handlers and /metrics endpoint remain here.
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

from fastapi import APIRouter
from . import routes_proxies, routes_stats, routes_maintenance, routes_health_etl, routes_database
from .api_shared import (
    require_api_key,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    get_proxy_manager,
    proxy_manager as GLOBAL_PROXY_MANAGER_REF,
)
# 延遲導入 ProxyManager 以避免循環引用; 僅型別檢查時引用
from typing import TYPE_CHECKING
if TYPE_CHECKING:  # pragma: no cover
    from .manager import ProxyManager

# Create app instance (re-added after refactor)
async def _lifespan(app: FastAPI):
    # Initialize global proxy manager if not already
    from .api_shared import proxy_manager as pm_ref
    # 讀取 git commit hash
    commit_hash = None
    try:
        import subprocess, pathlib
        result = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=pathlib.Path(__file__).parent.parent.parent)
        if result.returncode == 0:
            commit_hash = result.stdout.strip()
    except Exception:
        pass
    app.state.commit_hash = commit_hash
    if pm_ref is None:
        from .manager import ProxyManager  # 延遲導入
        mgr = ProxyManager()
        try:
            await mgr.start()
            from . import api_shared
            api_shared.proxy_manager = mgr
            logging.getLogger(__name__).info("✅ ProxyManager initialized in lifespan")
        except Exception as e:
            logging.getLogger(__name__).error(f"❌ Failed to start ProxyManager: {e}")
            raise
    yield
    # Shutdown logic
    from .api_shared import proxy_manager as pm_ref_shutdown
    if pm_ref_shutdown:
        try:
            await pm_ref_shutdown.stop()
        except Exception:
            pass

app = FastAPI(title="Proxy Manager API", version="1.0.0", lifespan=_lifespan)

# Mount modular routers
app.include_router(routes_proxies.router)
app.include_router(routes_stats.router)
app.include_router(routes_maintenance.router)
app.include_router(routes_health_etl.router)
app.include_router(routes_database.router)

# ---------------------------------------------------------------------------
# Root & convenience endpoints
# ---------------------------------------------------------------------------
from fastapi.responses import RedirectResponse  # local import (FastAPI already present)

@app.get("/", include_in_schema=False)
async def root_index():
    """Root index: provide quick links instead of 404."""
    return {
        "service": "Proxy Manager API",
        "version": app.version,
    "commit": getattr(app.state, 'commit_hash', None),
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/health",
        "metrics": "/metrics",
        "endpoints_prefix": "/api/*",
        "message": "See /docs for interactive API documentation"
    }

@app.get("/health", include_in_schema=False)
async def root_health_redirect():
    """Redirect /health -> /api/health for convenience (browser friendly)."""
    return RedirectResponse(url="/api/health")

@app.get("/api/system/health", summary="系統整體狀態")
async def system_health():
    """彙總 ProxyManager (若可用) 與基本服務狀態。"""
    from .api_shared import proxy_manager as pm
    base = {
        "service": "Proxy Manager API",
        "version": app.version,
        "commit": getattr(app.state, 'commit_hash', None),
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }
    if pm is None:
        base["proxy_manager"] = {"initialized": False}
    else:
        try:
            stats = pm.get_stats()  # type: ignore[attr-defined]
            base["proxy_manager"] = {
                "initialized": True,
                "total_fetched": stats.get('total_fetched'),
                "total_active": stats.get('total_active'),
                "running": stats.get('start_time') is not None,
            }
        except Exception as e:
            base["proxy_manager"] = {"initialized": True, "error": str(e)}
    return base


## Stats & pools endpoints moved to routes_stats / routes_health_etl


@app.post("/api/etl/sync", summary="同步代理數據到 ETL 系統", dependencies=[Depends(require_api_key)])
async def sync_to_etl(
    background_tasks: BackgroundTasks,
    pool_types: Optional[str] = Query("hot,warm,cold", description="要同步的池類型"),
    manager = Depends(get_proxy_manager)
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


## ETL endpoints moved to routes_health_etl


@app.get("/api/metrics/summary", summary="獲取系統指標摘要")
async def get_metrics_summary(manager = Depends(get_proxy_manager)):
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


## Metrics trends moved to routes_stats


## Batch validate moved to routes_maintenance


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

async def _sync_data_to_etl(manager, pool_types: List[str]):
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


## Background tasks relocated or will be reimplemented in dedicated modules


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
    # 使用純文本 Content-Type，避免某些代理誤解析
    data = generate_latest()
    from fastapi import Response
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    # 配置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 啟動服務器
    start_server(reload=True)