"""任務管理核心模組

這個模組定義了任務管理相關的資料模型、服務介面和業務邏輯。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .base import BaseEntity, TaskStatus, TaskPriority, BaseFilter, BaseService


class Task(BaseEntity):
    """任務實體類別"""
    name: str = Field(..., description="任務名稱")
    description: Optional[str] = Field(None, description="任務描述")
    task_type: str = Field(..., description="任務類型")
    status: TaskStatus = Field(TaskStatus.PENDING, description="任務狀態")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任務優先級")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="執行進度 (0-100)")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    duration: Optional[int] = Field(None, description="執行時長 (秒)")
    result: Optional[Dict[str, Any]] = Field(None, description="執行結果")
    error_message: Optional[str] = Field(None, description="錯誤訊息")
    config: Dict[str, Any] = Field(default_factory=dict, description="任務配置")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="任務元資料")
    parent_task_id: Optional[str] = Field(None, description="父任務 ID")
    retry_count: int = Field(0, description="重試次數")
    max_retries: int = Field(3, description="最大重試次數")
    scheduled_time: Optional[datetime] = Field(None, description="排程時間")
    
    def is_finished(self) -> bool:
        """檢查任務是否已完成"""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
    
    def is_running(self) -> bool:
        """檢查任務是否正在執行"""
        return self.status == TaskStatus.RUNNING
    
    def can_retry(self) -> bool:
        """檢查任務是否可以重試"""
        return self.status == TaskStatus.FAILED and self.retry_count < self.max_retries


class TaskFilter(BaseFilter):
    """任務篩選器"""
    status: Optional[List[TaskStatus]] = Field(None, description="狀態篩選")
    task_type: Optional[List[str]] = Field(None, description="任務類型篩選")
    priority: Optional[List[TaskPriority]] = Field(None, description="優先級篩選")
    start_date: Optional[datetime] = Field(None, description="開始日期篩選")
    end_date: Optional[datetime] = Field(None, description="結束日期篩選")
    parent_task_id: Optional[str] = Field(None, description="父任務 ID 篩選")


class TaskCreateRequest(BaseModel):
    """建立任務請求"""
    name: str = Field(..., description="任務名稱")
    description: Optional[str] = Field(None, description="任務描述")
    task_type: str = Field(..., description="任務類型")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任務優先級")
    config: Dict[str, Any] = Field(default_factory=dict, description="任務配置")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="任務元資料")
    parent_task_id: Optional[str] = Field(None, description="父任務 ID")
    max_retries: int = Field(3, description="最大重試次數")
    scheduled_time: Optional[datetime] = Field(None, description="排程時間")


class TaskUpdateRequest(BaseModel):
    """更新任務請求"""
    name: Optional[str] = Field(None, description="任務名稱")
    description: Optional[str] = Field(None, description="任務描述")
    priority: Optional[TaskPriority] = Field(None, description="任務優先級")
    config: Optional[Dict[str, Any]] = Field(None, description="任務配置")
    metadata: Optional[Dict[str, Any]] = Field(None, description="任務元資料")
    max_retries: Optional[int] = Field(None, description="最大重試次數")
    scheduled_time: Optional[datetime] = Field(None, description="排程時間")


class TaskExecutionRequest(BaseModel):
    """任務執行請求"""
    action: str = Field(..., description="執行動作 (start, pause, resume, cancel, retry)")
    force: bool = Field(False, description="是否強制執行")
    config_override: Optional[Dict[str, Any]] = Field(None, description="配置覆蓋")


class TaskBatchRequest(BaseModel):
    """批量任務操作請求"""
    task_ids: List[str] = Field(..., description="任務 ID 列表")
    action: str = Field(..., description="批量操作動作")
    config: Optional[Dict[str, Any]] = Field(None, description="操作配置")


class TaskStatistics(BaseModel):
    """任務統計資料"""
    total_tasks: int = Field(0, description="總任務數")
    pending_tasks: int = Field(0, description="待執行任務數")
    running_tasks: int = Field(0, description="執行中任務數")
    completed_tasks: int = Field(0, description="已完成任務數")
    failed_tasks: int = Field(0, description="失敗任務數")
    cancelled_tasks: int = Field(0, description="已取消任務數")
    average_duration: float = Field(0.0, description="平均執行時長 (秒)")
    success_rate: float = Field(0.0, description="成功率 (%)")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")


class TaskService(BaseService):
    """任務服務介面
    
    定義任務管理的核心業務邏輯介面。
    """
    
    async def create_task(self, request: TaskCreateRequest) -> Task:
        """建立新任務"""
        raise NotImplementedError
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """取得任務詳情"""
        raise NotImplementedError
    
    async def update_task(self, task_id: str, request: TaskUpdateRequest) -> Task:
        """更新任務"""
        raise NotImplementedError
    
    async def delete_task(self, task_id: str) -> bool:
        """刪除任務"""
        raise NotImplementedError
    
    async def list_tasks(self, filters: TaskFilter) -> List[Task]:
        """列出任務"""
        raise NotImplementedError
    
    async def execute_task(self, task_id: str, request: TaskExecutionRequest) -> Task:
        """執行任務操作"""
        raise NotImplementedError
    
    async def batch_operation(self, request: TaskBatchRequest) -> Dict[str, Any]:
        """批量操作任務"""
        raise NotImplementedError
    
    async def get_statistics(self) -> TaskStatistics:
        """取得任務統計資料"""
        raise NotImplementedError
    
    async def get_task_logs(self, task_id: str) -> List[Dict[str, Any]]:
        """取得任務日誌"""
        raise NotImplementedError