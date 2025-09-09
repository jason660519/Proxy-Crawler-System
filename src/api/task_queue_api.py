"""任務佇列管理 API 模組

提供任務佇列的完整管理功能，包括：
- 任務建立與排程
- 任務狀態追蹤
- 任務佇列管理
- 任務執行控制
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field, validator
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from ..core.task_manager import TaskManager
from ..models.task import Task, TaskStatus, TaskPriority, TaskType
from ..utils.pagination import PaginationParams, PaginatedResponse
from ..utils.logging import get_logger

# ============= 路由器設定 =============

router = APIRouter(prefix="/api/task-queue", tags=["任務佇列"])
logger = get_logger(__name__)

# ============= 枚舉定義 =============

class TaskAction(str, Enum):
    """任務操作類型"""
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    RETRY = "retry"
    DELETE = "delete"

class QueueAction(str, Enum):
    """佇列操作類型"""
    START_ALL = "start_all"
    PAUSE_ALL = "pause_all"
    CLEAR_COMPLETED = "clear_completed"
    CLEAR_FAILED = "clear_failed"
    CLEAR_ALL = "clear_all"

# ============= 請求模型 =============

class TaskFilters(BaseModel):
    """任務篩選參數"""
    status: Optional[List[TaskStatus]] = Field(None, description="狀態篩選")
    task_type: Optional[List[TaskType]] = Field(None, description="任務類型篩選")
    priority: Optional[List[TaskPriority]] = Field(None, description="優先級篩選")
    search: Optional[str] = Field(None, description="搜尋關鍵字")
    created_after: Optional[datetime] = Field(None, description="建立時間起始")
    created_before: Optional[datetime] = Field(None, description="建立時間結束")
    assigned_to: Optional[str] = Field(None, description="指派給特定執行者")
    has_errors: Optional[bool] = Field(None, description="是否有錯誤")
    tags: Optional[List[str]] = Field(None, description="標籤篩選")

class TaskCreateRequest(BaseModel):
    """建立任務請求"""
    name: str = Field(..., min_length=1, max_length=200, description="任務名稱")
    task_type: TaskType = Field(..., description="任務類型")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="優先級")
    description: Optional[str] = Field(None, max_length=1000, description="任務描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="任務配置")
    scheduled_at: Optional[datetime] = Field(None, description="排程執行時間")
    timeout: Optional[int] = Field(None, ge=1, description="超時時間 (秒)")
    max_retries: Optional[int] = Field(3, ge=0, le=10, description="最大重試次數")
    tags: Optional[List[str]] = Field(default_factory=list, description="標籤")
    dependencies: Optional[List[str]] = Field(default_factory=list, description="依賴任務 ID")
    
    @validator('scheduled_at')
    def validate_scheduled_at(cls, v):
        if v and v <= datetime.now():
            raise ValueError('排程時間必須在未來')
        return v

class TaskUpdateRequest(BaseModel):
    """更新任務請求"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="任務名稱")
    priority: Optional[TaskPriority] = Field(None, description="優先級")
    description: Optional[str] = Field(None, max_length=1000, description="任務描述")
    config: Optional[Dict[str, Any]] = Field(None, description="任務配置")
    scheduled_at: Optional[datetime] = Field(None, description="排程執行時間")
    timeout: Optional[int] = Field(None, ge=1, description="超時時間 (秒)")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="最大重試次數")
    tags: Optional[List[str]] = Field(None, description="標籤")

class TaskActionRequest(BaseModel):
    """任務操作請求"""
    action: TaskAction = Field(..., description="操作類型")
    reason: Optional[str] = Field(None, max_length=500, description="操作原因")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作選項")

class BatchTaskRequest(BaseModel):
    """批量任務操作請求"""
    task_ids: List[str] = Field(..., min_items=1, description="任務 ID 列表")
    action: TaskAction = Field(..., description="操作類型")
    reason: Optional[str] = Field(None, max_length=500, description="操作原因")

class QueueOperationRequest(BaseModel):
    """佇列操作請求"""
    action: QueueAction = Field(..., description="操作類型")
    filters: Optional[TaskFilters] = Field(None, description="篩選條件")
    reason: Optional[str] = Field(None, max_length=500, description="操作原因")

# ============= 回應模型 =============

class TaskResponse(BaseModel):
    """任務回應模型"""
    id: str
    name: str
    task_type: TaskType
    status: TaskStatus
    priority: TaskPriority
    description: Optional[str]
    config: Dict[str, Any]
    progress: float
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    scheduled_at: Optional[datetime]
    timeout: Optional[int]
    max_retries: int
    retry_count: int
    tags: List[str]
    dependencies: List[str]
    assigned_to: Optional[str]
    execution_time: Optional[float]
    estimated_completion: Optional[datetime]

class TaskLogEntry(BaseModel):
    """任務日誌條目"""
    timestamp: datetime
    level: str
    message: str
    details: Optional[Dict[str, Any]]

class TaskStatistics(BaseModel):
    """任務統計信息"""
    total: int
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
    by_type: Dict[str, int]
    by_priority: Dict[str, int]
    average_execution_time: Optional[float]
    success_rate: Optional[float]
    queue_length: int
    active_workers: int
    last_updated: datetime

class QueueStatus(BaseModel):
    """佇列狀態"""
    is_running: bool
    worker_count: int
    pending_tasks: int
    running_tasks: int
    max_concurrent: int
    throughput: float  # 每分鐘處理任務數
    average_wait_time: Optional[float]  # 平均等待時間 (秒)
    last_processed: Optional[datetime]

class BatchOperationResult(BaseModel):
    """批量操作結果"""
    success: bool
    total: int
    processed: int
    failed: int
    errors: List[str]
    task_results: List[Dict[str, Any]]
    message: str

# ============= 依賴注入 =============

# 全域任務管理器實例
_task_manager_instance = None

async def get_task_manager() -> TaskManager:
    """獲取任務管理器實例（單例模式）"""
    global _task_manager_instance
    if _task_manager_instance is None:
        _task_manager_instance = TaskManager()
        # 啟動佇列處理
        await _task_manager_instance.start_queue_processing()
    return _task_manager_instance

# ============= API 端點 =============

@router.get("/tasks", response_model=PaginatedResponse[TaskResponse])
async def get_tasks(
    pagination: PaginationParams = Depends(),
    filters: TaskFilters = Depends(),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """獲取任務列表
    
    支援分頁、排序和多種篩選條件
    """
    try:
        logger.info(f"獲取任務列表，分頁: {pagination}, 篩選: {filters}")
        
        # 構建查詢條件
        query_params = {k: v for k, v in filters.dict().items() if v is not None}
        
        # 執行查詢
        result = await task_manager.get_tasks_paginated(
            page=pagination.page,
            size=pagination.size,
            sort_by=pagination.sort_by,
            sort_order=pagination.sort_order,
            **query_params
        )
        
        return PaginatedResponse(
            data=[TaskResponse.from_orm(task) for task in result.data],
            pagination=result.pagination,
            success=True,
            message="任務列表獲取成功"
        )
        
    except Exception as e:
        logger.error(f"獲取任務列表失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務列表失敗: {str(e)}")

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """獲取單個任務詳情"""
    try:
        task = await task_manager.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        return TaskResponse.from_orm(task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取任務詳情失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務詳情失敗: {str(e)}")

@router.post("/tasks", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """建立新任務"""
    try:
        # 驗證依賴任務
        if request.dependencies:
            for dep_id in request.dependencies:
                dep_task = await task_manager.get_task_by_id(dep_id)
                if not dep_task:
                    raise HTTPException(status_code=400, detail=f"依賴任務不存在: {dep_id}")
        
        # 建立任務
        task_data = request.dict()
        task = await task_manager.create_task(task_data)
        
        # 如果是立即執行的任務，加入背景處理
        if not request.scheduled_at:
            background_tasks.add_task(task_manager.schedule_task, task.id)
        
        logger.info(f"建立任務成功: {task.name} ({task.id})")
        return TaskResponse.from_orm(task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"建立任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立任務失敗: {str(e)}")

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """更新任務信息"""
    try:
        # 檢查任務是否存在
        existing = await task_manager.get_task_by_id(task_id)
        if not existing:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 檢查任務狀態是否允許更新
        if existing.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED]:
            raise HTTPException(status_code=400, detail="任務狀態不允許更新")
        
        # 更新任務
        update_data = request.dict(exclude_unset=True)
        task = await task_manager.update_task(task_id, update_data)
        
        logger.info(f"更新任務成功: {task_id}")
        return TaskResponse.from_orm(task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新任務失敗: {str(e)}")

@router.post("/tasks/{task_id}/action")
async def task_action(
    task_id: str,
    request: TaskActionRequest,
    background_tasks: BackgroundTasks,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """執行任務操作"""
    try:
        # 檢查任務是否存在
        task = await task_manager.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 執行操作
        result = await task_manager.execute_task_action(
            task_id=task_id,
            action=request.action,
            reason=request.reason,
            options=request.options
        )
        
        # 如果是啟動操作，加入背景處理
        if request.action == TaskAction.START:
            background_tasks.add_task(task_manager.execute_task, task_id)
        
        logger.info(f"任務操作成功: {task_id} - {request.action}")
        return {
            "success": True,
            "message": f"任務 {request.action} 操作成功",
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"任務操作失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"任務操作失敗: {str(e)}")

@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    force: bool = Query(False, description="強制刪除（即使任務正在執行）"),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """刪除任務"""
    try:
        # 檢查任務是否存在
        task = await task_manager.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 檢查是否可以刪除
        if task.status == TaskStatus.RUNNING and not force:
            raise HTTPException(status_code=400, detail="任務正在執行，請先停止或使用強制刪除")
        
        # 刪除任務
        await task_manager.delete_task(task_id, force=force)
        
        logger.info(f"刪除任務成功: {task_id}")
        return {"success": True, "message": "任務刪除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除任務失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"刪除任務失敗: {str(e)}")

@router.post("/tasks/batch", response_model=BatchOperationResult)
async def batch_task_operation(
    request: BatchTaskRequest,
    background_tasks: BackgroundTasks,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """批量任務操作"""
    try:
        logger.info(f"執行批量任務操作: {request.action}，影響 {len(request.task_ids)} 個任務")
        
        # 執行批量操作
        result = await task_manager.batch_task_operation(
            task_ids=request.task_ids,
            action=request.action,
            reason=request.reason
        )
        
        # 如果是啟動操作，加入背景處理
        if request.action == TaskAction.START:
            for task_id in result.get("successful_tasks", []):
                background_tasks.add_task(task_manager.execute_task, task_id)
        
        return BatchOperationResult(
            success=result["success"],
            total=len(request.task_ids),
            processed=result["processed"],
            failed=result["failed"],
            errors=result.get("errors", []),
            task_results=result.get("task_results", []),
            message=result["message"]
        )
        
    except Exception as e:
        logger.error(f"批量任務操作失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量任務操作失敗: {str(e)}")

@router.get("/tasks/{task_id}/logs", response_model=List[TaskLogEntry])
async def get_task_logs(
    task_id: str,
    limit: int = Query(100, ge=1, le=1000, description="日誌條目數量限制"),
    level: Optional[str] = Query(None, description="日誌等級篩選"),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """獲取任務執行日誌"""
    try:
        # 檢查任務是否存在
        task = await task_manager.get_task_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 獲取日誌
        logs = await task_manager.get_task_logs(task_id, limit=limit, level=level)
        
        return [
            TaskLogEntry(
                timestamp=log["timestamp"],
                level=log["level"],
                message=log["message"],
                details=log.get("details")
            )
            for log in logs
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取任務日誌失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務日誌失敗: {str(e)}")

@router.get("/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    task_manager: TaskManager = Depends(get_task_manager)
):
    """獲取任務統計信息"""
    try:
        stats = await task_manager.get_statistics()
        
        return TaskStatistics(
            total=stats["total"],
            pending=stats["pending"],
            running=stats["running"],
            completed=stats["completed"],
            failed=stats["failed"],
            cancelled=stats["cancelled"],
            by_type=stats["by_type"],
            by_priority=stats["by_priority"],
            average_execution_time=stats.get("average_execution_time"),
            success_rate=stats.get("success_rate"),
            queue_length=stats["queue_length"],
            active_workers=stats["active_workers"],
            last_updated=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"獲取任務統計失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務統計失敗: {str(e)}")

@router.get("/queue/status", response_model=QueueStatus)
async def get_queue_status(
    task_manager: TaskManager = Depends(get_task_manager)
):
    """獲取佇列狀態"""
    try:
        status = await task_manager.get_queue_status()
        
        return QueueStatus(
            is_running=status["is_running"],
            worker_count=status["worker_count"],
            pending_tasks=status["pending_tasks"],
            running_tasks=status["running_tasks"],
            max_concurrent=status["max_concurrent"],
            throughput=status["throughput"],
            average_wait_time=status.get("average_wait_time"),
            last_processed=status.get("last_processed")
        )
        
    except Exception as e:
        logger.error(f"獲取佇列狀態失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取佇列狀態失敗: {str(e)}")

@router.post("/queue/operation")
async def queue_operation(
    request: QueueOperationRequest,
    background_tasks: BackgroundTasks,
    task_manager: TaskManager = Depends(get_task_manager)
):
    """執行佇列操作"""
    try:
        logger.info(f"執行佇列操作: {request.action}")
        
        # 執行佇列操作
        result = await task_manager.execute_queue_operation(
            action=request.action,
            filters=request.filters.dict() if request.filters else None,
            reason=request.reason
        )
        
        # 如果是啟動操作，加入背景處理
        if request.action == QueueAction.START_ALL:
            background_tasks.add_task(task_manager.start_queue_processing)
        
        return {
            "success": True,
            "message": f"佇列 {request.action} 操作成功",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"佇列操作失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"佇列操作失敗: {str(e)}")

@router.get("/types")
async def get_task_types(
    task_manager: TaskManager = Depends(get_task_manager)
):
    """獲取可用任務類型"""
    try:
        types = await task_manager.get_available_task_types()
        return {"task_types": types}
        
    except Exception as e:
        logger.error(f"獲取任務類型失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務類型失敗: {str(e)}")

@router.get("/templates")
async def get_task_templates(
    task_type: Optional[TaskType] = Query(None, description="任務類型篩選"),
    task_manager: TaskManager = Depends(get_task_manager)
):
    """獲取任務模板"""
    try:
        templates = await task_manager.get_task_templates(task_type=task_type)
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"獲取任務模板失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"獲取任務模板失敗: {str(e)}")