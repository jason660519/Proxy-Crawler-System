"""日誌模型定義

定義日誌相關的數據模型和枚舉類型。
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


class LogLevel(str, Enum):
    """日誌級別枚舉"""
    DEBUG = "debug"          # 調試
    INFO = "info"            # 信息
    WARNING = "warning"      # 警告
    ERROR = "error"          # 錯誤
    CRITICAL = "critical"    # 嚴重錯誤


@dataclass
class LogEntry:
    """日誌條目數據模型"""
    id: str
    timestamp: datetime
    level: LogLevel
    message: str
    module: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None
    task_id: Optional[str] = None
    proxy_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def formatted_message(self) -> str:
        """格式化的日誌消息"""
        parts = []
        if self.module:
            parts.append(f"[{self.module}]")
        if self.function:
            parts.append(f"{self.function}()")
        if self.line_number:
            parts.append(f"line {self.line_number}")
        
        prefix = " ".join(parts)
        if prefix:
            return f"{prefix}: {self.message}"
        return self.message
    
    @property
    def is_error(self) -> bool:
        """檢查是否為錯誤級別"""
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]