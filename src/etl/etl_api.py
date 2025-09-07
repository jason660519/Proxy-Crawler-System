#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETL API 擴展模組

此模組為代理管理系統提供 ETL 相關的 API 端點，包括：
- ETL 流程管理
- 數據品質監控
- 批量數據處理
- 監控儀表板 API
- 數據驗證和報告

作者: Assistant
創建時間: 2024
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, validator
from loguru import logger

# 導入 ETL 相關模組
from .proxy_etl_pipeline import (
    ProxyETLPipeline, ETLConfig, ETLMetrics, ETLResult,
    ETLStage, DataSource
)
from .data_validator import (
    ProxyDataValidator, ValidationLevel, ValidationResult,
    ValidationReport, ValidationIssue
)
from .monitoring_dashboard import (
    MonitoringDashboard, SystemMetrics, AlertRule, Alert
)
from .database_schema import DatabaseSchemaManager
from ..proxy_manager.models import ProxyNode, ProxyFilter
from database_config import db_config

def get_db_config():
    """獲取數據庫配置"""
    return db_config


# ===== Pydantic 模型定義 =====

class ETLJobRequest(BaseModel):
    """ETL 作業請求模型"""
    job_name: str = Field(..., description="作業名稱")
    data_source: str = Field(..., description="數據來源")
    batch_size: int = Field(1000, ge=1, le=10000, description="批次大小")
    validation_level: str = Field("STANDARD", description="驗證級別")
    enable_monitoring: bool = Field(True, description="啟用監控")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="配置覆蓋")
    
    @validator('validation_level')
    def validate_level(cls, v):
        valid_levels = ['BASIC', 'STANDARD', 'STRICT']
        if v.upper() not in valid_levels:
            raise ValueError(f"驗證級別必須是 {valid_levels} 之一")
        return v.upper()


class ETLJobResponse(BaseModel):
    """ETL 作業回應模型"""
    job_id: str
    job_name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ValidationRequest(BaseModel):
    """數據驗證請求模型"""
    data_source: str = Field(..., description="數據來源")
    validation_level: str = Field("STANDARD", description="驗證級別")
    sample_size: Optional[int] = Field(None, ge=1, le=10000, description="樣本大小")
    include_details: bool = Field(True, description="包含詳細信息")


class ValidationResponse(BaseModel):
    """數據驗證回應模型"""
    validation_id: str
    status: str
    overall_score: float
    total_records: int
    valid_records: int
    invalid_records: int
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    created_at: datetime


class MonitoringMetricsResponse(BaseModel):
    """監控指標回應模型"""
    timestamp: datetime
    system_metrics: Dict[str, Any]
    etl_metrics: Dict[str, Any]
    database_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]


class DataQueryRequest(BaseModel):
    """數據查詢請求模型"""
    query_type: str = Field(..., description="查詢類型")
    filters: Optional[Dict[str, Any]] = Field(None, description="篩選條件")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期範圍")
    aggregation: Optional[str] = Field(None, description="聚合方式")
    limit: int = Field(100, ge=1, le=10000, description="結果限制")
    offset: int = Field(0, ge=0, description="偏移量")


class DataExportRequest(BaseModel):
    """數據導出請求模型"""
    export_type: str = Field(..., description="導出類型")
    format: str = Field("json", description="導出格式")
    filters: Optional[Dict[str, Any]] = Field(None, description="篩選條件")
    date_range: Optional[Dict[str, str]] = Field(None, description="日期範圍")
    include_metadata: bool = Field(True, description="包含元數據")


# ===== ETL API 類別 =====

class ETLAPIManager:
    """ETL API 管理器"""
    
    def __init__(self):
        """初始化 ETL API 管理器"""
        self.etl_pipeline = None
        self.data_validator = None
        self.monitoring_dashboard = None
        self.schema_manager = None
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
        self.job_history: List[Dict[str, Any]] = []
        
    async def initialize(self):
        """初始化所有組件"""
        try:
            # 初始化數據庫配置
            db_config = get_db_config()
            
            # 初始化 ETL 管道
            etl_config = ETLConfig(
                batch_size=1000,
                validation_level=ValidationLevel.STANDARD,
                enable_monitoring=True
            )
            self.etl_pipeline = ProxyETLPipeline(etl_config)
            
            # 初始化數據驗證器
            self.data_validator = ProxyDataValidator()
            
            # 初始化監控儀表板
            self.monitoring_dashboard = MonitoringDashboard()
            await self.monitoring_dashboard.initialize()
            
            # 初始化數據庫架構管理器
            self.schema_manager = DatabaseSchemaManager(db_config)
            
            logger.info("✅ ETL API 管理器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ ETL API 管理器初始化失敗: {e}")
            raise
    
    async def create_etl_job(self, request: ETLJobRequest) -> str:
        """創建 ETL 作業"""
        job_id = str(uuid4())
        
        job_info = {
            "job_id": job_id,
            "job_name": request.job_name,
            "data_source": request.data_source,
            "status": "PENDING",
            "created_at": datetime.now(),
            "config": {
                "batch_size": request.batch_size,
                "validation_level": request.validation_level,
                "enable_monitoring": request.enable_monitoring,
                "config_overrides": request.config_overrides or {}
            },
            "progress": 0.0,
            "metrics": None,
            "error_message": None
        }
        
        self.active_jobs[job_id] = job_info
        logger.info(f"📋 創建 ETL 作業: {job_id} - {request.job_name}")
        
        return job_id
    
    async def start_etl_job(self, job_id: str) -> bool:
        """啟動 ETL 作業"""
        if job_id not in self.active_jobs:
            raise ValueError(f"作業 {job_id} 不存在")
        
        job_info = self.active_jobs[job_id]
        
        try:
            job_info["status"] = "RUNNING"
            job_info["started_at"] = datetime.now()
            
            # 配置 ETL 管道
            config = ETLConfig(
                batch_size=job_info["config"]["batch_size"],
                validation_level=ValidationLevel[job_info["config"]["validation_level"]],
                enable_monitoring=job_info["config"]["enable_monitoring"]
            )
            
            # 執行 ETL 流程
            result = await self.etl_pipeline.process_data(
                data_source=DataSource[job_info["data_source"].upper()],
                config=config
            )
            
            # 更新作業狀態
            job_info["status"] = "COMPLETED" if result.success else "FAILED"
            job_info["completed_at"] = datetime.now()
            job_info["progress"] = 100.0
            job_info["metrics"] = result.metrics.to_dict() if result.metrics else None
            
            if not result.success:
                job_info["error_message"] = result.error_message
            
            # 移動到歷史記錄
            self.job_history.append(job_info.copy())
            del self.active_jobs[job_id]
            
            logger.info(f"✅ ETL 作業完成: {job_id}")
            return True
            
        except Exception as e:
            job_info["status"] = "FAILED"
            job_info["error_message"] = str(e)
            job_info["completed_at"] = datetime.now()
            
            logger.error(f"❌ ETL 作業失敗: {job_id} - {e}")
            return False
    
    async def validate_data(self, request: ValidationRequest) -> ValidationReport:
        """執行數據驗證"""
        try:
            # 模擬獲取數據進行驗證
            # 在實際實現中，這裡會從指定的數據源獲取數據
            sample_data = []  # 這裡應該從數據源獲取實際數據
            
            validation_level = ValidationLevel[request.validation_level]
            
            # 執行驗證
            report = await self.data_validator.validate_batch(
                sample_data,
                validation_level
            )
            
            logger.info(f"📊 數據驗證完成: {request.data_source}")
            return report
            
        except Exception as e:
            logger.error(f"❌ 數據驗證失敗: {e}")
            raise
    
    async def get_monitoring_metrics(self) -> Dict[str, Any]:
        """獲取監控指標"""
        try:
            metrics = await self.monitoring_dashboard.collect_metrics()
            alerts = await self.monitoring_dashboard.check_alerts()
            
            return {
                "timestamp": datetime.now(),
                "system_metrics": metrics.to_dict() if metrics else {},
                "etl_metrics": self._get_etl_metrics(),
                "database_metrics": await self._get_database_metrics(),
                "alerts": [alert.to_dict() for alert in alerts]
            }
            
        except Exception as e:
            logger.error(f"❌ 獲取監控指標失敗: {e}")
            raise
    
    def _get_etl_metrics(self) -> Dict[str, Any]:
        """獲取 ETL 指標"""
        active_jobs_count = len(self.active_jobs)
        completed_jobs_count = len([job for job in self.job_history if job["status"] == "COMPLETED"])
        failed_jobs_count = len([job for job in self.job_history if job["status"] == "FAILED"])
        
        return {
            "active_jobs": active_jobs_count,
            "completed_jobs": completed_jobs_count,
            "failed_jobs": failed_jobs_count,
            "success_rate": completed_jobs_count / max(completed_jobs_count + failed_jobs_count, 1) * 100
        }
    
    async def _get_database_metrics(self) -> Dict[str, Any]:
        """獲取數據庫指標"""
        # 這裡應該實現實際的數據庫指標收集
        return {
            "connection_pool_size": 10,
            "active_connections": 5,
            "query_performance": "good",
            "storage_usage": "75%"
        }


# ===== 全局實例 =====
etl_api_manager = ETLAPIManager()


# ===== 依賴注入函數 =====

async def get_etl_manager() -> ETLAPIManager:
    """獲取 ETL API 管理器實例"""
    if etl_api_manager.etl_pipeline is None:
        await etl_api_manager.initialize()
    return etl_api_manager


# ===== FastAPI 應用實例 =====

etl_app = FastAPI(
    title="代理管理系統 ETL API",
    description="提供 ETL 流程管理、數據驗證和監控功能的 API",
    version="1.0.0",
    docs_url="/etl/docs",
    redoc_url="/etl/redoc"
)


# ===== API 端點定義 =====

@etl_app.post("/api/etl/jobs", response_model=ETLJobResponse, summary="創建 ETL 作業")
async def create_etl_job(
    request: ETLJobRequest,
    background_tasks: BackgroundTasks,
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """創建並啟動新的 ETL 作業"""
    try:
        job_id = await manager.create_etl_job(request)
        
        # 在背景啟動作業
        background_tasks.add_task(manager.start_etl_job, job_id)
        
        job_info = manager.active_jobs[job_id]
        
        return ETLJobResponse(
            job_id=job_id,
            job_name=job_info["job_name"],
            status=job_info["status"],
            created_at=job_info["created_at"],
            progress=job_info["progress"]
        )
        
    except Exception as e:
        logger.error(f"❌ 創建 ETL 作業失敗: {e}")
        raise HTTPException(status_code=500, detail=f"創建作業失敗: {e}")


@etl_app.get("/api/etl/jobs/{job_id}", response_model=ETLJobResponse, summary="獲取 ETL 作業狀態")
async def get_etl_job(
    job_id: str,
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """獲取指定 ETL 作業的狀態和進度"""
    try:
        # 檢查活躍作業
        if job_id in manager.active_jobs:
            job_info = manager.active_jobs[job_id]
        else:
            # 檢查歷史記錄
            job_info = next(
                (job for job in manager.job_history if job["job_id"] == job_id),
                None
            )
            
        if not job_info:
            raise HTTPException(status_code=404, detail="作業不存在")
        
        return ETLJobResponse(
            job_id=job_info["job_id"],
            job_name=job_info["job_name"],
            status=job_info["status"],
            created_at=job_info["created_at"],
            started_at=job_info.get("started_at"),
            completed_at=job_info.get("completed_at"),
            progress=job_info["progress"],
            metrics=job_info["metrics"],
            error_message=job_info.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取作業狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取作業狀態失敗: {e}")


@etl_app.get("/api/etl/jobs", response_model=List[ETLJobResponse], summary="獲取所有 ETL 作業")
async def list_etl_jobs(
    status: Optional[str] = Query(None, description="篩選狀態"),
    limit: int = Query(50, ge=1, le=200, description="結果限制"),
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """獲取所有 ETL 作業列表"""
    try:
        all_jobs = list(manager.active_jobs.values()) + manager.job_history
        
        # 狀態篩選
        if status:
            all_jobs = [job for job in all_jobs if job["status"].upper() == status.upper()]
        
        # 按創建時間排序（最新的在前）
        all_jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        # 限制結果數量
        all_jobs = all_jobs[:limit]
        
        return [
            ETLJobResponse(
                job_id=job["job_id"],
                job_name=job["job_name"],
                status=job["status"],
                created_at=job["created_at"],
                started_at=job.get("started_at"),
                completed_at=job.get("completed_at"),
                progress=job["progress"],
                metrics=job["metrics"],
                error_message=job.get("error_message")
            )
            for job in all_jobs
        ]
        
    except Exception as e:
        logger.error(f"❌ 獲取作業列表失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取作業列表失敗: {e}")


@etl_app.post("/api/etl/validate", response_model=ValidationResponse, summary="執行數據驗證")
async def validate_data(
    request: ValidationRequest,
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """對指定數據源執行數據品質驗證"""
    try:
        validation_id = str(uuid4())
        
        # 執行驗證
        report = await manager.validate_data(request)
        
        return ValidationResponse(
            validation_id=validation_id,
            status="COMPLETED",
            overall_score=report.overall_score,
            total_records=report.total_records,
            valid_records=report.valid_records,
            invalid_records=report.invalid_records,
            issues=[issue.to_dict() for issue in report.issues],
            recommendations=report.recommendations,
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"❌ 數據驗證失敗: {e}")
        raise HTTPException(status_code=500, detail=f"數據驗證失敗: {e}")


@etl_app.get("/api/etl/monitoring/metrics", response_model=MonitoringMetricsResponse, summary="獲取監控指標")
async def get_monitoring_metrics(
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """獲取系統監控指標和警報信息"""
    try:
        metrics = await manager.get_monitoring_metrics()
        
        return MonitoringMetricsResponse(
            timestamp=metrics["timestamp"],
            system_metrics=metrics["system_metrics"],
            etl_metrics=metrics["etl_metrics"],
            database_metrics=metrics["database_metrics"],
            alerts=metrics["alerts"]
        )
        
    except Exception as e:
        logger.error(f"❌ 獲取監控指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取監控指標失敗: {e}")


@etl_app.post("/api/etl/data/query", summary="查詢數據")
async def query_data(
    request: DataQueryRequest,
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """執行數據查詢操作"""
    try:
        # 這裡應該實現實際的數據查詢邏輯
        # 根據查詢類型和篩選條件從數據庫獲取數據
        
        result = {
            "query_id": str(uuid4()),
            "query_type": request.query_type,
            "total_count": 0,
            "data": [],
            "metadata": {
                "filters_applied": request.filters or {},
                "date_range": request.date_range,
                "aggregation": request.aggregation,
                "limit": request.limit,
                "offset": request.offset
            },
            "execution_time_ms": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ 數據查詢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"數據查詢失敗: {e}")


@etl_app.post("/api/etl/data/export", summary="導出數據")
async def export_data(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """導出數據到文件"""
    try:
        export_id = str(uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{request.export_type}_{timestamp}.{request.format}"
        
        # 在背景執行導出任務
        # background_tasks.add_task(perform_data_export, request, filename)
        
        return {
            "export_id": export_id,
            "filename": filename,
            "status": "PROCESSING",
            "download_url": f"/api/etl/data/download/{filename}",
            "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 數據導出失敗: {e}")
        raise HTTPException(status_code=500, detail=f"數據導出失敗: {e}")


@etl_app.get("/api/etl/data/download/{filename}", summary="下載導出文件")
async def download_export_file(filename: str):
    """下載導出的數據文件"""
    try:
        file_path = Path("data/exports") / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 文件下載失敗: {e}")
        raise HTTPException(status_code=500, detail=f"文件下載失敗: {e}")


@etl_app.get("/api/etl/health", summary="健康檢查")
async def health_check(
    manager: ETLAPIManager = Depends(get_etl_manager)
):
    """ETL 系統健康檢查"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "etl_pipeline": "operational" if manager.etl_pipeline else "unavailable",
                "data_validator": "operational" if manager.data_validator else "unavailable",
                "monitoring_dashboard": "operational" if manager.monitoring_dashboard else "unavailable",
                "schema_manager": "operational" if manager.schema_manager else "unavailable"
            },
            "active_jobs": len(manager.active_jobs),
            "total_jobs_processed": len(manager.job_history)
        }
        
        # 檢查是否有任何組件不可用
        if any(status == "unavailable" for status in health_status["components"].values()):
            health_status["status"] = "degraded"
        
        return health_status
        
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# ===== 錯誤處理 =====

@etl_app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 異常處理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


@etl_app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用異常處理器"""
    logger.error(f"❌ 未處理的異常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "內部服務器錯誤",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # 啟動 ETL API 服務器
    uvicorn.run(
        "src.etl.etl_api:etl_app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )