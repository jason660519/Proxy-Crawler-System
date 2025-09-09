"""日誌管理核心模組

這個模組定義了日誌管理相關的資料模型、服務介面和業務邏輯。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseEntity, LogLevel, BaseFilter, BaseService


class LogEntry(BaseEntity):
    """日誌條目實體類別"""
    timestamp: datetime = Field(default_factory=datetime.now, description="日誌時間戳")
    level: LogLevel = Field(..., description="日誌等級")
    source: str = Field(..., description="日誌來源")
    module: Optional[str] = Field(None, description="模組名稱")
    function: Optional[str] = Field(None, description="函數名稱")
    line_number: Optional[int] = Field(None, description="行號")
    message: str = Field(..., description="日誌訊息")
    details: Optional[Dict[str, Any]] = Field(None, description="詳細資訊")
    trace_id: Optional[str] = Field(None, description="追蹤 ID")
    user_id: Optional[str] = Field(None, description="使用者 ID")
    session_id: Optional[str] = Field(None, description="會話 ID")
    request_id: Optional[str] = Field(None, description="請求 ID")
    tags: List[str] = Field(default_factory=list, description="標籤")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元資料")
    
    def is_error(self) -> bool:
        """檢查是否為錯誤日誌"""
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]
    
    def is_warning(self) -> bool:
        """檢查是否為警告日誌"""
        return self.level == LogLevel.WARNING


class LogFilter(BaseFilter):
    """日誌篩選器"""
    level: Optional[List[LogLevel]] = Field(None, description="日誌等級篩選")
    source: Optional[List[str]] = Field(None, description="日誌來源篩選")
    module: Optional[List[str]] = Field(None, description="模組篩選")
    start_time: Optional[datetime] = Field(None, description="開始時間篩選")
    end_time: Optional[datetime] = Field(None, description="結束時間篩選")
    trace_id: Optional[str] = Field(None, description="追蹤 ID 篩選")
    user_id: Optional[str] = Field(None, description="使用者 ID 篩選")
    session_id: Optional[str] = Field(None, description="會話 ID 篩選")
    request_id: Optional[str] = Field(None, description="請求 ID 篩選")
    tags: Optional[List[str]] = Field(None, description="標籤篩選")
    has_details: Optional[bool] = Field(None, description="是否包含詳細資訊")


class LogSearchRequest(BaseModel):
    """日誌搜尋請求"""
    query: str = Field(..., description="搜尋查詢")
    filters: Optional[LogFilter] = Field(None, description="篩選條件")
    highlight: bool = Field(True, description="是否高亮顯示")
    max_results: int = Field(100, ge=1, le=1000, description="最大結果數")


class LogExportRequest(BaseModel):
    """日誌匯出請求"""
    filters: LogFilter = Field(..., description="篩選條件")
    format: str = Field("json", description="匯出格式 (json, csv, txt)")
    include_details: bool = Field(True, description="是否包含詳細資訊")
    compress: bool = Field(False, description="是否壓縮")
    filename: Optional[str] = Field(None, description="檔案名稱")


class LogStatistics(BaseModel):
    """日誌統計資料"""
    total_logs: int = Field(0, description="總日誌數")
    debug_logs: int = Field(0, description="除錯日誌數")
    info_logs: int = Field(0, description="資訊日誌數")
    warning_logs: int = Field(0, description="警告日誌數")
    error_logs: int = Field(0, description="錯誤日誌數")
    critical_logs: int = Field(0, description="嚴重錯誤日誌數")
    sources: Dict[str, int] = Field(default_factory=dict, description="來源統計")
    modules: Dict[str, int] = Field(default_factory=dict, description="模組統計")
    hourly_distribution: Dict[str, int] = Field(default_factory=dict, description="小時分佈")
    daily_distribution: Dict[str, int] = Field(default_factory=dict, description="日分佈")
    error_rate: float = Field(0.0, description="錯誤率 (%)")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")


class LogSource(BaseModel):
    """日誌來源資訊"""
    name: str = Field(..., description="來源名稱")
    display_name: str = Field(..., description="顯示名稱")
    description: Optional[str] = Field(None, description="來源描述")
    enabled: bool = Field(True, description="是否啟用")
    log_level: LogLevel = Field(LogLevel.INFO, description="最低日誌等級")
    retention_days: int = Field(30, description="保留天數")
    max_size_mb: int = Field(100, description="最大檔案大小 (MB)")
    config: Dict[str, Any] = Field(default_factory=dict, description="來源配置")
    last_activity: Optional[datetime] = Field(None, description="最後活動時間")
    log_count: int = Field(0, description="日誌數量")


class LogAlert(BaseModel):
    """日誌警報"""
    id: str = Field(..., description="警報 ID")
    name: str = Field(..., description="警報名稱")
    description: Optional[str] = Field(None, description="警報描述")
    enabled: bool = Field(True, description="是否啟用")
    conditions: Dict[str, Any] = Field(..., description="觸發條件")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="警報動作")
    last_triggered: Optional[datetime] = Field(None, description="最後觸發時間")
    trigger_count: int = Field(0, description="觸發次數")
    created_at: datetime = Field(default_factory=datetime.now, description="建立時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")


class LogStreamConfig(BaseModel):
    """日誌串流配置"""
    enabled: bool = Field(True, description="是否啟用串流")
    buffer_size: int = Field(1000, description="緩衝區大小")
    flush_interval: int = Field(5, description="刷新間隔 (秒)")
    filters: Optional[LogFilter] = Field(None, description="串流篩選器")
    max_connections: int = Field(100, description="最大連接數")
    heartbeat_interval: int = Field(30, description="心跳間隔 (秒)")


class LogService(BaseService):
    """日誌服務介面
    
    定義日誌管理的核心業務邏輯介面。
    """
    
    async def create_log(self, log_entry: LogEntry) -> LogEntry:
        """建立日誌條目"""
        raise NotImplementedError
    
    async def get_log(self, log_id: str) -> Optional[LogEntry]:
        """取得日誌詳情"""
        raise NotImplementedError
    
    async def list_logs(self, filters: LogFilter) -> List[LogEntry]:
        """列出日誌"""
        raise NotImplementedError
    
    async def search_logs(self, request: LogSearchRequest) -> List[LogEntry]:
        """搜尋日誌"""
        raise NotImplementedError
    
    async def export_logs(self, request: LogExportRequest) -> str:
        """匯出日誌"""
        raise NotImplementedError
    
    async def get_statistics(self, filters: Optional[LogFilter] = None) -> LogStatistics:
        """取得日誌統計資料"""
        raise NotImplementedError
    
    async def get_sources(self) -> List[LogSource]:
        """取得日誌來源列表"""
        raise NotImplementedError
    
    async def update_source(self, source_name: str, config: Dict[str, Any]) -> LogSource:
        """更新日誌來源配置"""
        raise NotImplementedError
    
    async def delete_logs(self, filters: LogFilter) -> int:
        """刪除日誌"""
        raise NotImplementedError
    
    async def create_alert(self, alert: LogAlert) -> LogAlert:
        """建立日誌警報"""
        raise NotImplementedError
    
    async def get_alerts(self) -> List[LogAlert]:
        """取得警報列表"""
        raise NotImplementedError
    
    async def start_stream(self, config: LogStreamConfig) -> str:
        """啟動日誌串流"""
        raise NotImplementedError
    
    async def stop_stream(self, stream_id: str) -> bool:
        """停止日誌串流"""
        raise NotImplementedError