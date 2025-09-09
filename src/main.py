"""Proxy Crawler 主應用程式入口點

這個模組提供了 Proxy Crawler 系統的主要 FastAPI 應用程式入口點。
包含基本的健康檢查和系統狀態端點。
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from datetime import datetime
from typing import Dict, Any

# 添加專案根目錄到 Python 路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 創建 FastAPI 應用程式實例
app = FastAPI(
    title="Proxy Crawler & Management System",
    description="專業的代理伺服器爬取與管理系統",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加 CORS 中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 導入並掛載代理管理器 API
try:
    from src.proxy_manager.api import app as proxy_api, proxy_manager
    # 直接將所有路由添加到主應用
    for route in proxy_api.routes:
        app.routes.append(route)
    print("代理管理器 API 已掛載到 /api")
except ImportError as e:
    print(f"無法載入代理管理器 API: {e}")

# 添加啟動事件來初始化代理管理器
@app.on_event("startup")
async def startup_event():
    """主應用啟動事件"""
    print("[DEBUG] 主應用 startup_event 被調用")
    
    # 初始化代理管理器
    try:
        from src.proxy_manager.manager import ProxyManager, ProxyManagerConfig
        
        print("[DEBUG] 開始創建代理管理器配置")
        config = ProxyManagerConfig()
        print("[DEBUG] 配置創建成功")
        
        print("[DEBUG] 開始創建代理管理器")
        manager = ProxyManager(config)
        print("[DEBUG] 代理管理器創建成功，開始啟動")
        
        await manager.start()
        print("[DEBUG] 代理管理器啟動成功")
        
        # 將管理器設置到 proxy_api 模組中
        import src.proxy_manager.api as proxy_api_module
        proxy_api_module.proxy_manager = manager
        
        print("代理管理器在主應用中初始化成功")
        
    except Exception as e:
        print(f"[DEBUG] 代理管理器初始化失敗: {e}")
        import traceback
        error_details = traceback.format_exc()
        print(f"[DEBUG] 詳細錯誤信息: {error_details}")
        # 不要 raise，讓服務繼續運行
    
    # 初始化任務管理器
    try:
        from src.core.task_manager import TaskManager
        
        print("[DEBUG] 開始創建任務管理器")
        task_manager = TaskManager()
        print("[DEBUG] 任務管理器創建成功，開始初始化")
        
        await task_manager.initialize()
        print("[DEBUG] 任務管理器初始化成功")
        
        # 將任務管理器設置到全局變量中
        import src.api.task_queue_api as task_queue_api_module
        task_queue_api_module._task_manager_instance = task_manager
        
        print("任務管理器在主應用中初始化成功")
        
    except Exception as e:
        print(f"[DEBUG] 任務管理器初始化失敗: {e}")
        import traceback
        error_details = traceback.format_exc()
        print(f"[DEBUG] 詳細錯誤信息: {error_details}")
        # 不要 raise，讓服務繼續運行

# 導入並掛載 ETL API
try:
    from src.etl.etl_api import etl_app
    app.mount("/etl", etl_app)
    print("ETL API 已掛載到 /etl")
except ImportError as e:
    print(f"無法載入 ETL API: {e}")

# 導入並掛載 HTML to Markdown API
try:
    from src.html_to_markdown.api_server import app as html2md_api
    app.mount("/html2md", html2md_api)
    print("HTML to Markdown API 已掛載到 /html2md")
except ImportError as e:
    print(f"無法載入 HTML to Markdown API: {e}")

# 導入並掛載 URL2Parquet API（新一代內容管線）
try:
    from src.url2parquet.api.router import router as url2parquet_router
    app.include_router(url2parquet_router)
    print("URL2Parquet API 已掛載到 /api/url2parquet")
except ImportError as e:
    print(f"無法載入 URL2Parquet API: {e}")

# 導入並掛載任務佇列管理 API
try:
    from src.api.task_queue import router as task_queue_router
    app.include_router(task_queue_router, prefix="/api/tasks", tags=["任務佇列"])
    print("任務佇列管理 API 已掛載到 /api/tasks")
except ImportError as e:
    print(f"無法載入任務佇列管理 API: {e}")

# 導入並掛載系統日誌管理 API
try:
    from src.api.system_logs import router as system_logs_router
    app.include_router(system_logs_router, prefix="/api/logs", tags=["系統日誌"])
    print("系統日誌管理 API 已掛載到 /api/logs")
except ImportError as e:
    print(f"無法載入系統日誌管理 API: {e}")

# 導入並掛載數據分析 API
try:
    from src.api.data_analytics import router as data_analytics_router
    app.include_router(data_analytics_router, prefix="/api/analytics", tags=["數據分析"])
    print("數據分析 API 已掛載到 /api/analytics")
except ImportError as e:
    print(f"無法載入數據分析 API: {e}")


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
        "environment": os.getenv("ENVIRONMENT", "development")
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
            "environment": os.getenv("ENVIRONMENT", "development"),
            "working_directory": os.getcwd(),
            "timestamp": datetime.now().isoformat()
        },
        "configuration": {
            "db_user": os.getenv("DB_USER", "not_set"),
            "db_name": os.getenv("DB_NAME", "not_set"),
            "redis_service": os.getenv("REDIS_SERVICE", "redis_cache")
        }
    }


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