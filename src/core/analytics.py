"""數據分析核心模組

這個模組定義了數據分析相關的資料模型、服務介面和業務邏輯。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

from .base import BaseEntity, BaseFilter, BaseService


class MetricType(str, Enum):
    """指標類型列舉"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TimeRange(str, Enum):
    """時間範圍列舉"""
    LAST_HOUR = "1h"
    LAST_6_HOURS = "6h"
    LAST_24_HOURS = "24h"
    LAST_7_DAYS = "7d"
    LAST_30_DAYS = "30d"
    LAST_90_DAYS = "90d"
    CUSTOM = "custom"


class AggregationType(str, Enum):
    """聚合類型列舉"""
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


class MetricDataPoint(BaseModel):
    """指標資料點"""
    timestamp: datetime = Field(..., description="時間戳")
    value: Union[int, float] = Field(..., description="數值")
    labels: Dict[str, str] = Field(default_factory=dict, description="標籤")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元資料")


class Metric(BaseEntity):
    """指標實體類別"""
    name: str = Field(..., description="指標名稱")
    display_name: str = Field(..., description="顯示名稱")
    description: Optional[str] = Field(None, description="指標描述")
    metric_type: MetricType = Field(..., description="指標類型")
    unit: Optional[str] = Field(None, description="單位")
    labels: List[str] = Field(default_factory=list, description="標籤列表")
    data_points: List[MetricDataPoint] = Field(default_factory=list, description="資料點")
    retention_days: int = Field(30, description="保留天數")
    enabled: bool = Field(True, description="是否啟用")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")


class SystemOverview(BaseModel):
    """系統概覽"""
    total_proxies: int = Field(0, description="總代理數")
    active_proxies: int = Field(0, description="活躍代理數")
    proxy_success_rate: float = Field(0.0, description="代理成功率 (%)")
    average_response_time: float = Field(0.0, description="平均回應時間 (ms)")
    total_tasks: int = Field(0, description="總任務數")
    running_tasks: int = Field(0, description="執行中任務數")
    completed_tasks: int = Field(0, description="已完成任務數")
    failed_tasks: int = Field(0, description="失敗任務數")
    task_success_rate: float = Field(0.0, description="任務成功率 (%)")
    system_uptime: int = Field(0, description="系統運行時間 (秒)")
    cpu_usage: float = Field(0.0, description="CPU 使用率 (%)")
    memory_usage: float = Field(0.0, description="記憶體使用率 (%)")
    disk_usage: float = Field(0.0, description="磁碟使用率 (%)")
    network_in: int = Field(0, description="網路輸入 (bytes)")
    network_out: int = Field(0, description="網路輸出 (bytes)")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")


class AnalyticsFilter(BaseFilter):
    """分析篩選器"""
    metric_names: Optional[List[str]] = Field(None, description="指標名稱篩選")
    metric_types: Optional[List[MetricType]] = Field(None, description="指標類型篩選")
    time_range: TimeRange = Field(TimeRange.LAST_24_HOURS, description="時間範圍")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    labels: Optional[Dict[str, str]] = Field(None, description="標籤篩選")
    aggregation: AggregationType = Field(AggregationType.AVG, description="聚合類型")
    interval: Optional[str] = Field(None, description="聚合間隔")


class MetricRequest(BaseModel):
    """指標請求"""
    metric_name: str = Field(..., description="指標名稱")
    filters: Optional[AnalyticsFilter] = Field(None, description="篩選條件")
    group_by: Optional[List[str]] = Field(None, description="分組欄位")
    limit: Optional[int] = Field(None, description="結果限制")


class AnalyticsResponse(BaseModel):
    """分析回應"""
    metric_name: str = Field(..., description="指標名稱")
    data_points: List[MetricDataPoint] = Field(default_factory=list, description="資料點")
    summary: Dict[str, Union[int, float]] = Field(default_factory=dict, description="摘要統計")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元資料")
    generated_at: datetime = Field(default_factory=datetime.now, description="生成時間")


class Dashboard(BaseEntity):
    """儀表板實體類別"""
    name: str = Field(..., description="儀表板名稱")
    description: Optional[str] = Field(None, description="儀表板描述")
    layout: Dict[str, Any] = Field(..., description="佈局配置")
    widgets: List[Dict[str, Any]] = Field(default_factory=list, description="小工具列表")
    filters: Optional[AnalyticsFilter] = Field(None, description="預設篩選器")
    refresh_interval: int = Field(300, description="刷新間隔 (秒)")
    is_public: bool = Field(False, description="是否公開")
    owner_id: Optional[str] = Field(None, description="擁有者 ID")
    tags: List[str] = Field(default_factory=list, description="標籤")


class Report(BaseEntity):
    """報告實體類別"""
    name: str = Field(..., description="報告名稱")
    description: Optional[str] = Field(None, description="報告描述")
    report_type: str = Field(..., description="報告類型")
    template: Dict[str, Any] = Field(..., description="報告模板")
    data: Dict[str, Any] = Field(default_factory=dict, description="報告資料")
    filters: Optional[AnalyticsFilter] = Field(None, description="篩選條件")
    schedule: Optional[str] = Field(None, description="排程 (cron 表達式)")
    format: str = Field("json", description="輸出格式")
    recipients: List[str] = Field(default_factory=list, description="收件人列表")
    last_generated: Optional[datetime] = Field(None, description="最後生成時間")
    next_generation: Optional[datetime] = Field(None, description="下次生成時間")
    enabled: bool = Field(True, description="是否啟用")


class Alert(BaseEntity):
    """警報實體類別"""
    name: str = Field(..., description="警報名稱")
    description: Optional[str] = Field(None, description="警報描述")
    metric_name: str = Field(..., description="監控指標")
    condition: Dict[str, Any] = Field(..., description="觸發條件")
    threshold: Union[int, float] = Field(..., description="閾值")
    severity: str = Field("medium", description="嚴重程度")
    enabled: bool = Field(True, description="是否啟用")
    notification_channels: List[str] = Field(default_factory=list, description="通知管道")
    cooldown_minutes: int = Field(5, description="冷卻時間 (分鐘)")
    last_triggered: Optional[datetime] = Field(None, description="最後觸發時間")
    trigger_count: int = Field(0, description="觸發次數")


class AnalyticsService(BaseService):
    """分析服務介面
    
    定義數據分析的核心業務邏輯介面。
    """
    
    async def get_system_overview(self) -> SystemOverview:
        """取得系統概覽"""
        raise NotImplementedError
    
    async def get_metric_data(self, request: MetricRequest) -> AnalyticsResponse:
        """取得指標資料"""
        raise NotImplementedError
    
    async def list_metrics(self, filters: Optional[AnalyticsFilter] = None) -> List[Metric]:
        """列出指標"""
        raise NotImplementedError
    
    async def create_metric(self, metric: Metric) -> Metric:
        """建立指標"""
        raise NotImplementedError
    
    async def update_metric(self, metric_id: str, updates: Dict[str, Any]) -> Metric:
        """更新指標"""
        raise NotImplementedError
    
    async def delete_metric(self, metric_id: str) -> bool:
        """刪除指標"""
        raise NotImplementedError
    
    async def record_metric(self, metric_name: str, value: Union[int, float], 
                          labels: Optional[Dict[str, str]] = None) -> bool:
        """記錄指標資料"""
        raise NotImplementedError
    
    async def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        """建立儀表板"""
        raise NotImplementedError
    
    async def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """取得儀表板"""
        raise NotImplementedError
    
    async def list_dashboards(self) -> List[Dashboard]:
        """列出儀表板"""
        raise NotImplementedError
    
    async def update_dashboard(self, dashboard_id: str, updates: Dict[str, Any]) -> Dashboard:
        """更新儀表板"""
        raise NotImplementedError
    
    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """刪除儀表板"""
        raise NotImplementedError
    
    async def generate_report(self, report_id: str) -> Dict[str, Any]:
        """生成報告"""
        raise NotImplementedError
    
    async def create_report(self, report: Report) -> Report:
        """建立報告"""
        raise NotImplementedError
    
    async def list_reports(self) -> List[Report]:
        """列出報告"""
        raise NotImplementedError
    
    async def create_alert(self, alert: Alert) -> Alert:
        """建立警報"""
        raise NotImplementedError
    
    async def list_alerts(self) -> List[Alert]:
        """列出警報"""
        raise NotImplementedError
    
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """檢查警報"""
        raise NotImplementedError