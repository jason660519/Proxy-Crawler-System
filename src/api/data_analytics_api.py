"""數據分析 API 模組

提供系統數據的完整分析功能，包括：
- 代理性能分析
- 任務執行分析
- 系統健康監控
- 自定義報告生成
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from ..core.analytics_engine import AnalyticsEngine
from ..models.analytics import (
    MetricType, TimeRange, AggregationType, 
    AnalyticsReport, ChartType, ReportFormat
)
from ..utils.pagination import PaginationParams, PaginatedResponse
from ..utils.logging import get_logger

# ============= 路由器設定 =============

router = APIRouter(prefix="/api/data-analytics", tags=["數據分析"])
logger = get_logger(__name__)

# ============= 枚舉定義 =============

class AnalysisType(str, Enum):
    """分析類型"""
    PROXY_PERFORMANCE = "proxy_performance"
    TASK_EXECUTION = "task_execution"
    SYSTEM_HEALTH = "system_health"
    USER_ACTIVITY = "user_activity"
    ERROR_ANALYSIS = "error_analysis"
    TREND_ANALYSIS = "trend_analysis"
    COMPARATIVE = "comparative"
    PREDICTIVE = "predictive"

class MetricCategory(str, Enum):
    """指標類別"""
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    USAGE = "usage"
    ERROR = "error"
    BUSINESS = "business"
    CUSTOM = "custom"

class AlertSeverity(str, Enum):
    """警報嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# ============= 請求模型 =============

class AnalyticsFilters(BaseModel):
    """分析篩選參數"""
    time_range: TimeRange = Field(..., description="時間範圍")
    start_time: Optional[datetime] = Field(None, description="自定義開始時間")
    end_time: Optional[datetime] = Field(None, description="自定義結束時間")
    proxy_ids: Optional[List[str]] = Field(None, description="代理 ID 篩選")
    task_types: Optional[List[str]] = Field(None, description="任務類型篩選")
    components: Optional[List[str]] = Field(None, description="組件篩選")
    countries: Optional[List[str]] = Field(None, description="國家篩選")
    status_codes: Optional[List[int]] = Field(None, description="狀態碼篩選")
    user_ids: Optional[List[str]] = Field(None, description="用戶 ID 篩選")
    tags: Optional[List[str]] = Field(None, description="標籤篩選")
    
    @validator('end_time')
    def validate_time_range(cls, v, values):
        if v and 'start_time' in values and values['start_time']:
            if v <= values['start_time']:
                raise ValueError('結束時間必須晚於開始時間')
        return v

class MetricRequest(BaseModel):
    """指標查詢請求"""
    metrics: List[MetricType] = Field(..., description="指標類型列表")
    filters: AnalyticsFilters = Field(..., description="篩選條件")
    aggregation: AggregationType = Field(AggregationType.AVERAGE, description="聚合方式")
    group_by: Optional[List[str]] = Field(None, description="分組欄位")
    resolution: Optional[str] = Field("1h", description="時間解析度")
    include_forecast: bool = Field(False, description="是否包含預測")

class ReportRequest(BaseModel):
    """報告生成請求"""
    name: str = Field(..., min_length=1, max_length=200, description="報告名稱")
    description: Optional[str] = Field(None, max_length=1000, description="報告描述")
    analysis_type: AnalysisType = Field(..., description="分析類型")
    filters: AnalyticsFilters = Field(..., description="篩選條件")
    metrics: List[MetricType] = Field(..., description="包含的指標")
    charts: List[ChartType] = Field(..., description="圖表類型")
    format: ReportFormat = Field(ReportFormat.PDF, description="報告格式")
    schedule: Optional[str] = Field(None, description="排程設定 (cron 表達式)")
    recipients: Optional[List[str]] = Field(None, description="收件人列表")
    auto_insights: bool = Field(True, description="是否自動生成洞察")

class DashboardRequest(BaseModel):
    """儀表板配置請求"""
    name: str = Field(..., min_length=1, max_length=100, description="儀表板名稱")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    layout: Dict[str, Any] = Field(..., description="布局配置")
    widgets: List[Dict[str, Any]] = Field(..., description="小部件配置")
    refresh_interval: int = Field(300, ge=30, le=3600, description="刷新間隔 (秒)")
    is_public: bool = Field(False, description="是否公開")
    tags: Optional[List[str]] = Field(None, description="標籤")

class AlertRuleRequest(BaseModel):
    """警報規則請求"""
    name: str = Field(..., min_length=1, max_length=100, description="規則名稱")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    metric: MetricType = Field(..., description="監控指標")
    condition: str = Field(..., description="觸發條件")
    threshold: float = Field(..., description="閾值")
    severity: AlertSeverity = Field(..., description="嚴重程度")
    time_window: int = Field(..., ge=60, le=3600, description="時間窗口 (秒)")
    filters: Optional[AnalyticsFilters] = Field(None, description="篩選條件")
    notification_channels: List[str] = Field(..., description="通知渠道")
    enabled: bool = Field(True, description="是否啟用")
    cooldown: int = Field(300, ge=60, description="冷卻時間 (秒)")

class CustomMetricRequest(BaseModel):
    """自定義指標請求"""
    name: str = Field(..., min_length=1, max_length=100, description="指標名稱")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    category: MetricCategory = Field(..., description="指標類別")
    query: str = Field(..., description="查詢語句")
    unit: Optional[str] = Field(None, description="單位")
    aggregation: AggregationType = Field(..., description="聚合方式")
    tags: Optional[List[str]] = Field(None, description="標籤")

# ============= 回應模型 =============

class MetricDataPoint(BaseModel):
    """指標數據點"""
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]]

class MetricSeries(BaseModel):
    """指標時間序列"""
    metric: MetricType
    label: str
    unit: Optional[str]
    data_points: List[MetricDataPoint]
    aggregation: AggregationType
    summary: Dict[str, float]  # min, max, avg, sum, count

class AnalyticsResponse(BaseModel):
    """分析回應"""
    analysis_type: AnalysisType
    time_range: Dict[str, datetime]
    metrics: List[MetricSeries]
    insights: List[str]
    recommendations: List[str]
    anomalies: List[Dict[str, Any]]
    forecast: Optional[List[MetricDataPoint]]
    generated_at: datetime

class ReportResponse(BaseModel):
    """報告回應"""
    id: str
    name: str
    status: str
    progress: float
    created_at: datetime
    completed_at: Optional[datetime]
    file_url: Optional[str]
    file_size: Optional[int]
    error: Optional[str]

class DashboardResponse(BaseModel):
    """儀表板回應"""
    id: str
    name: str
    description: Optional[str]
    layout: Dict[str, Any]
    widgets: List[Dict[str, Any]]
    refresh_interval: int
    is_public: bool
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    last_accessed: Optional[datetime]
    access_count: int

class AlertResponse(BaseModel):
    """警報回應"""
    id: str
    rule_name: str
    metric: MetricType
    current_value: float
    threshold: float
    severity: AlertSeverity
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime]
    message: str
    details: Dict[str, Any]

class SystemOverview(BaseModel):
    """系統概覽"""
    total_proxies: int
    active_proxies: int
    total_tasks: int
    running_tasks: int
    success_rate: float
    average_response_time: float
    error_rate: float
    uptime: float
    last_24h_requests: int
    top_countries: List[Dict[str, Any]]
    recent_alerts: List[AlertResponse]
    system_health: str
    last_updated: datetime

class TrendAnalysis(BaseModel):
    """趨勢分析"""
    metric: MetricType
    trend_direction: str  # up, down, stable
    trend_strength: float  # 0-1
    change_percentage: float
    seasonal_patterns: List[Dict[str, Any]]
    anomaly_score: float
    forecast_confidence: float
    insights: List[str]

class ComparativeAnalysis(BaseModel):
    """對比分析"""
    baseline_period: Dict[str, datetime]
    comparison_period: Dict[str, datetime]
    metrics_comparison: List[Dict[str, Any]]
    significant_changes: List[Dict[str, Any]]
    performance_delta: Dict[str, float]
    insights: List[str]

# ============= 依賴注入 =============

async def get_analytics_engine() -> AnalyticsEngine:
    """獲取分析引擎實例"""
    return AnalyticsEngine()

# ============= API 端點 =============

@router.get("/overview", response_model=SystemOverview)
async def get_system_overview(
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """獲取系統概覽"""
    try:
        overview = await analytics_engine.get_system_overview()
        
        return SystemOverview(
            total_proxies=overview["total_proxies"],
            active_proxies=overview["active_proxies"],
            total_tasks=overview["total_tasks"],
            running_tasks=overview["running_tasks"],
            success_rate=overview["success_rate"],
            average_response_time=overview["average_response_time"],
            error_rate=overview["error_rate"],
            uptime=overview["uptime"],
            last_24h_requests=overview["last_24h_requests"],
            top_countries=overview["top_countries"],
            recent_alerts=[AlertResponse(**alert) for alert in overview["recent_alerts"]],
            system_health=overview["system_health"],
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"獲取系統概覽失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取系統概覽失敗: {str(e)}")

@router.post("/metrics", response_model=AnalyticsResponse)
async def get_metrics(
    request: MetricRequest,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """獲取指標數據"""
    try:
        logger.info(f"獲取指標數據: {request.metrics}")
        
        # 執行指標查詢
        result = await analytics_engine.get_metrics(
            metrics=request.metrics,
            filters=request.filters.dict(),
            aggregation=request.aggregation,
            group_by=request.group_by,
            resolution=request.resolution,
            include_forecast=request.include_forecast
        )
        
        return AnalyticsResponse(
            analysis_type=AnalysisType.PROXY_PERFORMANCE,  # 根據指標類型動態設定
            time_range=result["time_range"],
            metrics=[MetricSeries(**series) for series in result["metrics"]],
            insights=result["insights"],
            recommendations=result["recommendations"],
            anomalies=result["anomalies"],
            forecast=result.get("forecast"),
            generated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"獲取指標數據失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取指標數據失敗: {str(e)}")

@router.post("/analysis/{analysis_type}", response_model=AnalyticsResponse)
async def perform_analysis(
    analysis_type: AnalysisType,
    filters: AnalyticsFilters,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """執行特定類型的分析"""
    try:
        logger.info(f"執行分析: {analysis_type}")
        
        # 執行分析
        result = await analytics_engine.perform_analysis(
            analysis_type=analysis_type,
            filters=filters.dict()
        )
        
        return AnalyticsResponse(
            analysis_type=analysis_type,
            time_range=result["time_range"],
            metrics=[MetricSeries(**series) for series in result["metrics"]],
            insights=result["insights"],
            recommendations=result["recommendations"],
            anomalies=result["anomalies"],
            forecast=result.get("forecast"),
            generated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"執行分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"執行分析失敗: {str(e)}")

@router.post("/reports", response_model=ReportResponse)
async def create_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """建立分析報告"""
    try:
        logger.info(f"建立報告: {request.name}")
        
        # 建立報告任務
        report = await analytics_engine.create_report(request.dict())
        
        # 加入背景處理
        background_tasks.add_task(
            analytics_engine.generate_report,
            report["id"]
        )
        
        return ReportResponse(
            id=report["id"],
            name=report["name"],
            status=report["status"],
            progress=report["progress"],
            created_at=report["created_at"],
            completed_at=report.get("completed_at"),
            file_url=report.get("file_url"),
            file_size=report.get("file_size"),
            error=report.get("error")
        )
        
    except Exception as e:
        logger.error(f"建立報告失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立報告失敗: {str(e)}")

@router.get("/reports", response_model=PaginatedResponse[ReportResponse])
async def get_reports(
    pagination: PaginationParams = Depends(),
    status: Optional[str] = Query(None, description="狀態篩選"),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """獲取報告列表"""
    try:
        result = await analytics_engine.get_reports(
            page=pagination.page,
            size=pagination.size,
            status=status
        )
        
        return PaginatedResponse(
            data=[ReportResponse(**report) for report in result.data],
            pagination=result.pagination,
            success=True,
            message="報告列表獲取成功"
        )
        
    except Exception as e:
        logger.error(f"獲取報告列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取報告列表失敗: {str(e)}")

@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """獲取報告詳情"""
    try:
        report = await analytics_engine.get_report_by_id(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="報告不存在")
        
        return ReportResponse(**report)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取報告詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取報告詳情失敗: {str(e)}")

@router.post("/dashboards", response_model=DashboardResponse)
async def create_dashboard(
    request: DashboardRequest,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """建立儀表板"""
    try:
        dashboard = await analytics_engine.create_dashboard(request.dict())
        
        logger.info(f"建立儀表板成功: {request.name}")
        return DashboardResponse(**dashboard)
        
    except Exception as e:
        logger.error(f"建立儀表板失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立儀表板失敗: {str(e)}")

@router.get("/dashboards", response_model=List[DashboardResponse])
async def get_dashboards(
    is_public: Optional[bool] = Query(None, description="是否公開"),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """獲取儀表板列表"""
    try:
        dashboards = await analytics_engine.get_dashboards(is_public=is_public)
        return [DashboardResponse(**dashboard) for dashboard in dashboards]
        
    except Exception as e:
        logger.error(f"獲取儀表板列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取儀表板列表失敗: {str(e)}")

@router.post("/trends", response_model=List[TrendAnalysis])
async def analyze_trends(
    metrics: List[MetricType],
    filters: AnalyticsFilters,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """趨勢分析"""
    try:
        logger.info(f"執行趨勢分析: {metrics}")
        
        trends = await analytics_engine.analyze_trends(
            metrics=metrics,
            filters=filters.dict()
        )
        
        return [TrendAnalysis(**trend) for trend in trends]
        
    except Exception as e:
        logger.error(f"趨勢分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"趨勢分析失敗: {str(e)}")

@router.post("/compare", response_model=ComparativeAnalysis)
async def comparative_analysis(
    baseline_filters: AnalyticsFilters,
    comparison_filters: AnalyticsFilters,
    metrics: List[MetricType],
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """對比分析"""
    try:
        logger.info("執行對比分析")
        
        result = await analytics_engine.comparative_analysis(
            baseline_filters=baseline_filters.dict(),
            comparison_filters=comparison_filters.dict(),
            metrics=metrics
        )
        
        return ComparativeAnalysis(**result)
        
    except Exception as e:
        logger.error(f"對比分析失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"對比分析失敗: {str(e)}")

@router.post("/alerts/rules", response_model=Dict[str, Any])
async def create_alert_rule(
    request: AlertRuleRequest,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """建立警報規則"""
    try:
        rule = await analytics_engine.create_alert_rule(request.dict())
        
        logger.info(f"建立警報規則成功: {request.name}")
        return {
            "success": True,
            "rule_id": rule["id"],
            "message": "警報規則建立成功"
        }
        
    except Exception as e:
        logger.error(f"建立警報規則失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立警報規則失敗: {str(e)}")

@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[AlertSeverity] = Query(None, description="嚴重程度篩選"),
    status: Optional[str] = Query(None, description="狀態篩選"),
    limit: int = Query(100, ge=1, le=1000, description="數量限制"),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """獲取警報列表"""
    try:
        alerts = await analytics_engine.get_alerts(
            severity=severity,
            status=status,
            limit=limit
        )
        
        return [AlertResponse(**alert) for alert in alerts]
        
    except Exception as e:
        logger.error(f"獲取警報列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取警報列表失敗: {str(e)}")

@router.post("/metrics/custom", response_model=Dict[str, Any])
async def create_custom_metric(
    request: CustomMetricRequest,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """建立自定義指標"""
    try:
        metric = await analytics_engine.create_custom_metric(request.dict())
        
        logger.info(f"建立自定義指標成功: {request.name}")
        return {
            "success": True,
            "metric_id": metric["id"],
            "message": "自定義指標建立成功"
        }
        
    except Exception as e:
        logger.error(f"建立自定義指標失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立自定義指標失敗: {str(e)}")

@router.get("/metrics/available")
async def get_available_metrics(
    category: Optional[MetricCategory] = Query(None, description="類別篩選"),
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """獲取可用指標列表"""
    try:
        metrics = await analytics_engine.get_available_metrics(category=category)
        return {"metrics": metrics}
        
    except Exception as e:
        logger.error(f"獲取可用指標失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取可用指標失敗: {str(e)}")

@router.get("/export/{report_id}")
async def download_report(
    report_id: str,
    analytics_engine: AnalyticsEngine = Depends(get_analytics_engine)
):
    """下載報告文件"""
    try:
        report_file = await analytics_engine.get_report_file(report_id)
        if not report_file:
            raise HTTPException(status_code=404, detail="報告文件不存在")
        
        return StreamingResponse(
            iter([report_file["content"]]),
            media_type=report_file["content_type"],
            headers={
                "Content-Disposition": f"attachment; filename={report_file['filename']}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下載報告失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下載報告失敗: {str(e)}")