"""任務模型定義

定義任務相關的數據模型和枚舉類型。
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class TaskStatus(str, Enum):
    """任務狀態枚舉"""
    PENDING = "pending"      # 待執行
    RUNNING = "running"      # 執行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失敗
    CANCELLED = "cancelled"  # 已取消
    PAUSED = "paused"        # 暫停


class TaskPriority(str, Enum):
    """任務優先級枚舉"""
    LOW = "low"              # 低優先級
    MEDIUM = "medium"        # 中優先級
    HIGH = "high"            # 高優先級
    URGENT = "urgent"        # 緊急


class TaskType(str, Enum):
    """任務類型枚舉"""
    CRAWL = "crawl"          # 爬蟲任務
    ANALYSIS = "analysis"    # 分析任務
    EXPORT = "export"        # 導出任務
    CLEANUP = "cleanup"      # 清理任務
    SYSTEM = "system"        # 系統任務


@dataclass
class Task:
    """任務數據模型"""
    id: str
    name: str
    description: str = ""
    task_type: TaskType = TaskType.CRAWL
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    progress: float = 0.0
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    parent_task_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    scheduled_time: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def duration(self) -> Optional[float]:
        """計算任務執行時長（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    @property
    def is_finished(self) -> bool:
        """檢查任務是否已結束"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    @property
    def can_retry(self) -> bool:
        """檢查任務是否可以重試"""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries


# 為了向後兼容，創建別名
TaskModel = Task