"""Proxy Crawler 主應用程式入口點

這個模組提供了 Proxy Crawler 系統的主要 FastAPI 應用程式入口點。
包含基本的健康檢查和系統狀態端點。
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
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