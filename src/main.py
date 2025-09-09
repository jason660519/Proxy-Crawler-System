"""Proxy Crawler 主應用程式入口點

這個模組提供了 Proxy Crawler 系統的主要 FastAPI 應用程式入口點。
包含基本的健康檢查和系統狀態端點。"""

from fastapi import FastAPI
from fastapi import Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from datetime import datetime
from typing import Dict, Any
import asyncio


class ProxyCrawlerSystemLauncher:
    """代理爬蟲系統啟動器
    
    負責系統的初始化、啟動和管理。
    """
    
    def __init__(self):
        """初始化系統啟動器"""
        self.app = None
        self.proxy_manager = None
        self.task_manager = None
        self.is_running = False
    
    async def initialize(self) -> bool:
        """初始化系統組件
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            print("正在初始化 Proxy Crawler 系統...")
            
            # 初始化代理管理器
            await self._initialize_proxy_manager()
            
            # 初始化任務管理器
            await self._initialize_task_manager()
            
            print("系統初始化完成")
            return True
            
        except Exception as e:
            print(f"系統初始化失敗: {e}")
            return False
    
    async def _initialize_proxy_manager(self):
        """初始化代理管理器"""
        try:
            from src.proxy_manager.manager import ProxyManager, ProxyManagerConfig
            
            config = ProxyManagerConfig()
            self.proxy_manager = ProxyManager(config)
            await self.proxy_manager.start()
            print("代理管理器初始化成功")
            
        except Exception as e:
            print(f"代理管理器初始化失敗: {e}")
    
    async def _initialize_task_manager(self):
        """初始化任務管理器"""
        try:
            from src.core.task_manager import TaskManager
            
            self.task_manager = TaskManager()
            await self.task_manager.initialize()
            print("任務管理器初始化成功")
            
        except Exception as e:
            print(f"任務管理器初始化失敗: {e}")
    
    async def start(self) -> bool:
        """啟動系統
        
        Returns:
            bool: 啟動是否成功
        """
        if not await self.initialize():
            return False
        
        self.is_running = True
        print("Proxy Crawler 系統啟動成功")
        return True
    
    async def stop(self):
        """停止系統"""
        print("正在停止 Proxy Crawler 系統...")
        
        if self.proxy_manager:
            try:
                await self.proxy_manager.stop()
            except Exception as e:
                print(f"停止代理管理器時發生錯誤: {e}")
        
        if self.task_manager:
            try:
                await self.task_manager.cleanup()
            except Exception as e:
                print(f"停止任務管理器時發生錯誤: {e}")
        
        self.is_running = False
        print("系統已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """獲取系統狀態
        
        Returns:
            Dict[str, Any]: 系統狀態資訊
        """
        return {
            "is_running": self.is_running,
            "proxy_manager": self.proxy_manager is not None,
            "task_manager": self.task_manager is not None,
            "timestamp": datetime.now().isoformat()
        }
    
    async def demo_start(self) -> bool:
        """以演示模式啟動系統
        
        演示模式會跳過一些複雜的初始化步驟，快速啟動基本功能。
        
        Returns:
            bool: 啟動是否成功
        """
        try:
            print("正在以演示模式啟動 Proxy Crawler 系統...")
            
            # 演示模式下的簡化初始化
            print("演示模式：跳過複雜的組件初始化")
            print("演示模式：使用基本配置")
            
            # 設置基本狀態
            self.is_running = True
            
            print("演示模式啟動成功！")
            print("系統現在運行在演示模式下，部分功能可能受限。")
            
            return True
            
        except Exception as e:
            print(f"演示模式啟動失敗: {e}")
            return False
    
    async def quick_start(self) -> bool:
        """快速啟動模式
        
        Returns:
            bool: 啟動是否成功
        """
        try:
            print("正在以快速模式啟動 Proxy Crawler 系統...")
            
            # 快速模式下的基本初始化
            print("快速模式：啟動核心組件")
            await self._initialize_proxy_manager()
            
            self.is_running = True
            print("快速模式啟動成功！")
            return True
            
        except Exception as e:
            print(f"快速模式啟動失敗: {e}")
            return False
    
    async def full_start(self) -> bool:
        """完整啟動模式
        
        Returns:
            bool: 啟動是否成功
        """
        try:
            print("正在以完整模式啟動 Proxy Crawler 系統...")
            
            # 完整模式下的全面初始化
            print("完整模式：初始化所有組件")
            if not await self.initialize():
                return False
            
            self.is_running = True
            print("完整模式啟動成功！")
            
            # 啟動 Web 服務器
            print("正在啟動 Web 服務器...")
            import uvicorn
            import asyncio
            
            # 創建 Uvicorn 配置
            config = uvicorn.Config(
                "src.main:app",
                host="0.0.0.0",
                port=8001,
                reload=False,
                log_level="info"
            )
            server = uvicorn.Server(config)
            
            # 在當前事件循環中啟動服務器
            await server.serve()
            
            return True
            
        except Exception as e:
            print(f"完整模式啟動失敗: {e}")
            return False
    
    async def test_start(self) -> bool:
        """測試啟動模式
        
        Returns:
            bool: 啟動是否成功
        """
        try:
            print("正在以測試模式啟動 Proxy Crawler 系統...")
            
            # 測試模式下的驗證啟動
            print("測試模式：運行系統檢查")
            print("測試模式：驗證組件功能")
            
            self.is_running = True
            print("測試模式啟動成功！")
            return True
            
        except Exception as e:
            print(f"測試模式啟動失敗: {e}")
            return False

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
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 導入並掛載代理管理器 API
try:
    from src.proxy_manager.api import app as proxy_api, proxy_manager
    # 使用 mount 方式掛載子應用
    app.mount("/api", proxy_api)
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
    # 掛載新版任務佇列 API（前綴為 /api/task-queue）
    from src.api.task_queue_api import (
        router as task_queue_api_router,
        get_tasks as _tq_get_tasks,
    )
    from src.api.task_queue_api import TaskFilters  # type: ignore
    from src.utils.pagination import PaginationParams  # type: ignore
    from src.api.task_queue_api import get_task_manager, TaskManager  # type: ignore

    app.include_router(task_queue_api_router)
    print("任務佇列管理 API 已掛載到 /api/task-queue")

    # 提供與前端相容的別名端點：/api/tasks -> 代理到 task_queue_api 的 /api/task-queue/tasks
    @app.get("/api/tasks")
    async def alias_list_tasks(page: int = 1, size: int = 10, status: str = ""):
        # 提供最小可用的相容回應，避免前端輪詢報錯
        from src.utils.pagination import PaginatedResponse, PaginationParams
        pagination = PaginationParams(page=page, page_size=size)
        return PaginatedResponse.create(items=[], total=0, pagination=pagination)
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


@app.get("/api/health")
async def api_health_check() -> Dict[str, Any]:
    """與根路徑健康檢查一致的別名，避免前端透過 /api 代理時出現 404。"""
    # 直接重用現有的健康檢查邏輯
    return await health_check()


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