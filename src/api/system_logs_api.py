"""系統日誌管理 API 模組

提供系統日誌的完整管理功能，包括：
- 日誌查詢與篩選
- 即時日誌串流
- 日誌分析與統計
- 日誌導出與歸檔
"""

from typing import List, Optional, Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Query, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
from ..core.log_manager import LogManager
from ..models.log import LogEntry, LogLevel, LogSource
from ..utils.pagination import PaginationParams, PaginatedResponse
from ..utils.logging import get_logger

# ============= 路由器設定 =============

router = APIRouter(prefix="/api/system-logs", tags=["系統日誌"])
logger = get_logger(__name__)

# ============= 枚舉定義 =============

class LogExportFormat(str, Enum):
    """日誌導出格式"""
    JSON = "json"
    CSV = "csv"
    TXT = "txt"
    XML = "xml"

class LogAggregation(str, Enum):
    """日誌聚合方式"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

# ============= 請求模型 =============

class LogFilters(BaseModel):
    """日誌篩選參數"""
    level: Optional[List[LogLevel]] = Field(None, description="日誌等級篩選")
    source: Optional[List[LogSource]] = Field(None, description="日誌來源篩選")
    search: Optional[str] = Field(None, description="搜尋關鍵字")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    component: Optional[List[str]] = Field(None, description="組件篩選")
    user_id: Optional[str] = Field(None, description="用戶 ID 篩選")
    session_id: Optional[str] = Field(None, description="會話 ID 篩選")
    request_id: Optional[str] = Field(None, description="請求 ID 篩選")
    has_error: Optional[bool] = Field(None, description="是否包含錯誤")
    ip_address: Optional[str] = Field(None, description="IP 地址篩選")
    tags: Optional[List[str]] = Field(None, description="標籤篩選")
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('結束時間必須晚於開始時間')
        return v

class LogSearchRequest(BaseModel):
    """日誌搜尋請求"""
    query: str = Field(..., min_length=1, description="搜尋查詢")
    filters: Optional[LogFilters] = Field(None, description="篩選條件")
    highlight: bool = Field(True, description="是否高亮搜尋結果")
    context_lines: int = Field(0, ge=0, le=10, description="上下文行數")

class LogExportRequest(BaseModel):
    """日誌導出請求"""
    format: LogExportFormat = Field(..., description="導出格式")
    filters: Optional[LogFilters] = Field(None, description="篩選條件")
    max_records: Optional[int] = Field(10000, ge=1, le=100000, description="最大記錄數")
    include_metadata: bool = Field(True, description="是否包含元數據")
    compress: bool = Field(False, description="是否壓縮")

class LogAnalysisRequest(BaseModel):
    """日誌分析請求"""
    filters: Optional[LogFilters] = Field(None, description="篩選條件")
    aggregation: LogAggregation = Field(LogAggregation.HOUR, description="聚合方式")
    metrics: List[str] = Field(default_factory=lambda: ["count", "error_rate"], description="分析指標")
    group_by: Optional[List[str]] = Field(None, description="分組欄位")

class LogAlertRule(BaseModel):
    """日誌警報規則"""
    name: str = Field(..., min_length=1, max_length=100, description="規則名稱")
    description: Optional[str] = Field(None, max_length=500, description="規則描述")
    filters: LogFilters = Field(..., description="觸發條件")
    threshold: int = Field(..., ge=1, description="閾值")
    time_window: int = Field(..., ge=1, le=3600, description="時間窗口 (秒)")
    enabled: bool = Field(True, description="是否啟用")
    notification_channels: List[str] = Field(default_factory=list, description="通知渠道")

# ============= 回應模型 =============

class LogResponse(BaseModel):
    """日誌回應模型"""
    id: str
    timestamp: datetime
    level: LogLevel
    source: LogSource
    component: str
    message: str
    details: Optional[Dict[str, Any]]
    user_id: Optional[str]
    session_id: Optional[str]
    request_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    tags: List[str]
    stack_trace: Optional[str]
    duration: Optional[float]
    status_code: Optional[int]
    method: Optional[str]
    url: Optional[str]
    created_at: datetime

class LogStatistics(BaseModel):
    """日誌統計信息"""
    total_logs: int
    by_level: Dict[str, int]
    by_source: Dict[str, int]
    by_component: Dict[str, int]
    error_rate: float
    average_response_time: Optional[float]
    top_errors: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    time_range: Dict[str, datetime]
    last_updated: datetime

class LogAnalysisResult(BaseModel):
    """日誌分析結果"""
    aggregation: LogAggregation
    time_series: List[Dict[str, Any]]
    summary: Dict[str, Any]
    trends: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    recommendations: List[str]

class LogSearchResult(BaseModel):
    """日誌搜尋結果"""
    total_matches: int
    logs: List[LogResponse]
    highlights: Dict[str, List[str]]
    facets: Dict[str, Dict[str, int]]
    query_time: float

class LogAlertStatus(BaseModel):
    """日誌警報狀態"""
    rule_id: str
    rule_name: str
    status: str
    last_triggered: Optional[datetime]
    trigger_count: int
    current_value: int
    threshold: int
    enabled: bool

# ============= 依賴注入 =============

async def get_log_manager() -> LogManager:
    """獲取日誌管理器實例"""
    return LogManager()

# ============= WebSocket 連接管理 =============

class ConnectionManager:
    """WebSocket 連接管理器"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.log_filters: Dict[WebSocket, LogFilters] = {}
    
    async def connect(self, websocket: WebSocket, filters: Optional[LogFilters] = None):
        """建立連接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        if filters:
            self.log_filters[websocket] = filters
        logger.info(f"WebSocket 連接建立，當前連接數: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """斷開連接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.log_filters:
            del self.log_filters[websocket]
        logger.info(f"WebSocket 連接斷開，當前連接數: {len(self.active_connections)}")
    
    async def broadcast_log(self, log_entry: LogEntry):
        """廣播日誌到所有連接"""
        if not self.active_connections:
            return
        
        log_data = LogResponse.from_orm(log_entry).dict()
        message = json.dumps({
            "type": "log",
            "data": log_data
        })
        
        disconnected = []
        for connection in self.active_connections:
            try:
                # 檢查篩選條件
                if connection in self.log_filters:
                    filters = self.log_filters[connection]
                    if not self._matches_filters(log_entry, filters):
                        continue
                
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"廣播日誌失敗: {str(e)}")
                disconnected.append(connection)
        
        # 清理斷開的連接
        for connection in disconnected:
            self.disconnect(connection)
    
    def _matches_filters(self, log_entry: LogEntry, filters: LogFilters) -> bool:
        """檢查日誌是否符合篩選條件"""
        if filters.level and log_entry.level not in filters.level:
            return False
        if filters.source and log_entry.source not in filters.source:
            return False
        if filters.component and log_entry.component not in filters.component:
            return False
        if filters.search and filters.search.lower() not in log_entry.message.lower():
            return False
        return True

manager = ConnectionManager()

# ============= API 端點 =============

@router.get("/logs", response_model=PaginatedResponse[LogResponse])
async def get_logs(
    pagination: PaginationParams = Depends(),
    filters: LogFilters = Depends(),
    log_manager: LogManager = Depends(get_log_manager)
):
    """獲取日誌列表
    
    支援分頁、排序和多種篩選條件
    """
    try:
        logger.info(f"獲取日誌列表，分頁: {pagination}, 篩選: {filters}")
        
        # 構建查詢條件
        query_params = {k: v for k, v in filters.dict().items() if v is not None}
        
        # 執行查詢
        result = await log_manager.get_logs_paginated(
            page=pagination.page,
            size=pagination.size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            **query_params
        )
        
        return PaginatedResponse(
            data=[LogResponse.from_orm(log) for log in result.data],
            pagination=result.pagination,
            success=True,
            message="日誌列表獲取成功"
        )
        
    except Exception as e:
        logger.error(f"獲取日誌列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取日誌列表失敗: {str(e)}")

@router.get("/logs/{log_id}", response_model=LogResponse)
async def get_log(
    log_id: str,
    log_manager: LogManager = Depends(get_log_manager)
):
    """獲取單個日誌詳情"""
    try:
        log_entry = await log_manager.get_log_by_id(log_id)
        if not log_entry:
            raise HTTPException(status_code=404, detail="日誌不存在")
        
        return LogResponse.from_orm(log_entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取日誌詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取日誌詳情失敗: {str(e)}")

@router.post("/search", response_model=LogSearchResult)
async def search_logs(
    request: LogSearchRequest,
    pagination: PaginationParams = Depends(),
    log_manager: LogManager = Depends(get_log_manager)
):
    """搜尋日誌"""
    try:
        logger.info(f"搜尋日誌: {request.query}")
        
        # 執行搜尋
        result = await log_manager.search_logs(
            query=request.query,
            filters=request.filters.dict() if request.filters else None,
            page=pagination.page,
            size=pagination.size,
            highlight=request.highlight,
            context_lines=request.context_lines
        )
        
        return LogSearchResult(
            total_matches=result["total"],
            logs=[LogResponse.from_orm(log) for log in result["logs"]],
            highlights=result.get("highlights", {}),
            facets=result.get("facets", {}),
            query_time=result["query_time"]
        )
        
    except Exception as e:
        logger.error(f"搜尋日誌失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜尋日誌失敗: {str(e)}")

@router.get("/statistics", response_model=LogStatistics)
async def get_log_statistics(
    filters: LogFilters = Depends(),
    log_manager: LogManager = Depends(get_log_manager)
):
    """獲取日誌統計信息"""
    try:
        query_params = {k: v for k, v in filters.dict().items() if v is not None}
        stats = await log_manager.get_statistics(**query_params)
        
        return LogStatistics(
            total_logs=stats["total_logs"],
            by_level=stats["by_level"],
            by_source=stats["by_source"],
            by_component=stats["by_component"],
            error_rate=stats["error_rate"],
            average_response_time=stats.get("average_response_time"),
            top_errors=stats["top_errors"],
            recent_activity=stats["recent_activity"],
            time_range=stats["time_range"],
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"獲取日誌統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取日誌統計失敗: {str(e)}")

@router.post("/analysis", response_model=LogAnalysisResult)
async def analyze_logs(
    request: LogAnalysisRequest,
    log_manager: LogManager = Depends(get_log_manager)
):
    """分析日誌"""
    try:
        logger.info(f"分析日誌，聚合方式: {request.aggregation}")
        
        # 執行分析
        result = await log_manager.analyze_logs(
            filters=request.filters.dict() if request.filters else None,
            aggregation=request.aggregation,
            metrics=request.metrics,
            group_by=request.group_by
        )
        
        return LogAnalysisResult(
            aggregation=request.aggregation,
            time_series=result["time_series"],
            summary=result["summary"],
            trends=result["trends"],
            anomalies=result["anomalies"],
            recommendations=result["recommendations"]
        )
        
    except Exception as e:
        logger.error(f"分析日誌失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析日誌失敗: {str(e)}")

@router.post("/export")
async def export_logs(
    request: LogExportRequest,
    log_manager: LogManager = Depends(get_log_manager)
):
    """導出日誌"""
    try:
        logger.info(f"導出日誌，格式: {request.format}")
        
        # 生成導出數據
        export_data = await log_manager.export_logs(
            format=request.format,
            filters=request.filters.dict() if request.filters else None,
            max_records=request.max_records,
            include_metadata=request.include_metadata,
            compress=request.compress
        )
        
        # 設定回應標頭
        filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{request.format}"
        if request.compress:
            filename += ".gz"
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": export_data["content_type"]
        }
        
        return StreamingResponse(
            iter([export_data["content"]]),
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"導出日誌失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"導出日誌失敗: {str(e)}")

@router.websocket("/stream")
async def log_stream(
    websocket: WebSocket,
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    component: Optional[str] = Query(None)
):
    """即時日誌串流"""
    # 建立篩選條件
    filters = None
    if level or source or component:
        filters = LogFilters(
            level=[LogLevel(level)] if level else None,
            source=[LogSource(source)] if source else None,
            component=[component] if component else None
        )
    
    await manager.connect(websocket, filters)
    
    try:
        while True:
            # 保持連接活躍
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket 錯誤: {str(e)}")
        manager.disconnect(websocket)

@router.delete("/logs")
async def delete_logs(
    filters: LogFilters = Depends(),
    confirm: bool = Query(False, description="確認刪除"),
    log_manager: LogManager = Depends(get_log_manager)
):
    """刪除日誌"""
    if not confirm:
        raise HTTPException(status_code=400, detail="請確認刪除操作")
    
    try:
        query_params = {k: v for k, v in filters.dict().items() if v is not None}
        
        # 執行刪除
        result = await log_manager.delete_logs(**query_params)
        
        logger.info(f"刪除日誌成功，刪除數量: {result['deleted_count']}")
        return {
            "success": True,
            "deleted_count": result["deleted_count"],
            "message": "日誌刪除成功"
        }
        
    except Exception as e:
        logger.error(f"刪除日誌失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刪除日誌失敗: {str(e)}")

@router.get("/sources")
async def get_log_sources(
    log_manager: LogManager = Depends(get_log_manager)
):
    """獲取可用日誌來源"""
    try:
        sources = await log_manager.get_available_sources()
        return {"sources": sources}
        
    except Exception as e:
        logger.error(f"獲取日誌來源失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取日誌來源失敗: {str(e)}")

@router.get("/components")
async def get_log_components(
    source: Optional[LogSource] = Query(None, description="按來源篩選"),
    log_manager: LogManager = Depends(get_log_manager)
):
    """獲取可用組件列表"""
    try:
        components = await log_manager.get_available_components(source=source)
        return {"components": components}
        
    except Exception as e:
        logger.error(f"獲取組件列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取組件列表失敗: {str(e)}")

@router.post("/alerts/rules", response_model=Dict[str, Any])
async def create_alert_rule(
    request: LogAlertRule,
    log_manager: LogManager = Depends(get_log_manager)
):
    """建立日誌警報規則"""
    try:
        rule = await log_manager.create_alert_rule(request.dict())
        
        logger.info(f"建立警報規則成功: {request.name}")
        return {
            "success": True,
            "rule_id": rule["id"],
            "message": "警報規則建立成功"
        }
        
    except Exception as e:
        logger.error(f"建立警報規則失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立警報規則失敗: {str(e)}")

@router.get("/alerts/status", response_model=List[LogAlertStatus])
async def get_alert_status(
    log_manager: LogManager = Depends(get_log_manager)
):
    """獲取警報狀態"""
    try:
        alerts = await log_manager.get_alert_status()
        
        return [
            LogAlertStatus(
                rule_id=alert["rule_id"],
                rule_name=alert["rule_name"],
                status=alert["status"],
                last_triggered=alert.get("last_triggered"),
                trigger_count=alert["trigger_count"],
                current_value=alert["current_value"],
                threshold=alert["threshold"],
                enabled=alert["enabled"]
            )
            for alert in alerts
        ]
        
    except Exception as e:
        logger.error(f"獲取警報狀態失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取警報狀態失敗: {str(e)}")