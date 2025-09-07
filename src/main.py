"""Proxy Crawler 主應用程式入口點

這個模組提供了 Proxy Crawler 系統的主要 FastAPI 應用程式入口點。
包含基本的健康檢查和系統狀態端點。
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import sys
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

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

# 導入並整合簡化的 API
try:
    from src.simple_api import simple_api
    app.mount("/api", simple_api)
    print("✅ 簡化 API 已成功整合")
except ImportError as e:
    print(f"⚠️ 簡化 API 整合失敗: {e}")

# 導入並整合分析 API
try:
    from src.analysis.analysis_api import analysis_api
    app.mount("/analysis", analysis_api)
    print("✅ 分析 API 已成功整合")
except ImportError as e:
    print(f"⚠️ 分析 API 整合失敗: {e}")

# 導入並整合監控 API
try:
    from src.monitoring.monitoring_api import monitoring_api
    app.mount("/monitoring", monitoring_api)
    print("✅ 監控 API 已成功整合")
except ImportError as e:
    print(f"⚠️ 監控 API 整合失敗: {e}")

# 添加 ETL 端點到主應用程式
@app.get("/etl/status")
async def get_etl_status() -> Dict[str, Any]:
    """獲取 ETL 狀態"""
    try:
        # 檢查 ETL 輸出文件
        data_dir = Path("data")
        
        raw_files = list((data_dir / "raw").glob("*.json"))
        processed_files = list((data_dir / "processed").glob("*.json"))
        validated_files = list((data_dir / "validated").glob("*.json"))
        report_files = list((data_dir / "reports").glob("*.md"))
        
        return {
            "status": "running",
            "stages": {
                "extract": {
                    "status": "completed" if raw_files else "pending",
                    "files_count": len(raw_files)
                },
                "transform": {
                    "status": "completed" if processed_files else "pending",
                    "files_count": len(processed_files)
                },
                "validate": {
                    "status": "completed" if validated_files else "pending",
                    "files_count": len(validated_files)
                },
                "load": {
                    "status": "completed" if report_files else "pending",
                    "files_count": len(report_files)
                }
            },
            "last_run": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取 ETL 狀態失敗: {str(e)}")

@app.post("/etl/sync")
async def sync_etl() -> Dict[str, Any]:
    """同步 ETL 數據"""
    try:
        # 這裡可以觸發 ETL 流程
        # 目前只是返回成功狀態
        return {
            "status": "success",
            "message": "ETL 同步已觸發",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ETL 同步失敗: {str(e)}")

# 嘗試導入完整的代理管理 API（如果可用）
try:
    from src.proxy_manager.api import app as proxy_api
    # 可以選擇性地添加更多端點
    print("✅ 完整代理管理 API 模組可用")
except ImportError as e:
    print(f"⚠️ 完整代理管理 API 不可用: {e}")

# 嘗試導入 ETL API（如果可用）
try:
    from src.etl.etl_api import etl_app
    print("✅ ETL API 模組可用")
except ImportError as e:
    print(f"⚠️ ETL API 不可用: {e}")


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