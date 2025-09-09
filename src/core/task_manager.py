"""任務管理器實作模組

提供任務佇列管理的完整實作，包括：
- 任務生命週期管理
- 任務排程與執行
- 任務狀態追蹤
- 批量操作支援
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from collections import defaultdict
from enum import Enum
import logging

from .tasks import (
    Task, TaskFilter, TaskCreateRequest, TaskUpdateRequest, 
    TaskExecutionRequest, TaskBatchRequest, TaskStatistics, TaskService
)
from .base import TaskStatus, TaskPriority
from ..utils.pagination import PaginationParams, PaginatedResponse


class TaskType(str, Enum):
    """任務類型枚舉"""
    CRAWL = "crawl"
    PROXY_CHECK = "proxy_check"
    DATA_EXPORT = "data_export"
    SYSTEM_MAINTENANCE = "system_maintenance"
    CUSTOM = "custom"


class TaskAction(str, Enum):
    """任務操作類型"""
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    RETRY = "retry"
    DELETE = "delete"


class TaskManager(TaskService):
    """任務管理器實作
    
    負責管理任務的完整生命週期，包括建立、執行、監控和清理。
    """
    
    def __init__(self):
        """初始化任務管理器"""
        self.logger = logging.getLogger(__name__)
        self._tasks: Dict[str, Task] = {}
        self._task_queue: List[str] = []  # 待執行任務佇列
        self._running_tasks: Dict[str, asyncio.Task] = {}  # 正在執行的任務
        self._max_concurrent = 5  # 最大並發任務數
        self._is_running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._statistics_cache: Optional[TaskStatistics] = None
        self._cache_expiry: Optional[datetime] = None
        
    async def initialize(self) -> None:
        """初始化服務"""
        self.logger.info("初始化任務管理器服務")
        # 啟動佇列處理
        await self.start_queue_processing()
        
    async def cleanup(self) -> None:
        """清理服務資源"""
        self.logger.info("清理任務管理器資源")
        # 停止佇列處理
        await self.stop_queue_processing()
        # 取消所有執行中的任務
        for task_id, task in self._running_tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"取消任務: {task_id}")
        # 清空任務列表
        self._tasks.clear()
        self._task_queue.clear()
        self._running_tasks.clear()
        
    async def create_task(self, request: TaskCreateRequest) -> Task:
        """建立新任務
        
        Args:
            request: 任務建立請求
            
        Returns:
            建立的任務物件
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = Task(
            id=task_id,
            name=request.name,
            description=request.description,
            task_type=request.task_type,
            status=TaskStatus.PENDING,
            priority=request.priority,
            config=request.config,
            metadata=request.metadata,
            parent_task_id=request.parent_task_id,
            max_retries=request.max_retries,
            scheduled_time=request.scheduled_time,
            created_at=now,
            updated_at=now
        )
        
        self._tasks[task_id] = task
        
        # 如果是立即執行的任務，加入佇列
        if not request.scheduled_time or request.scheduled_time <= now:
            self._add_to_queue(task_id)
        
        self.logger.info(f"建立任務: {task.name} ({task_id})")
        self._invalidate_cache()
        
        return task
    
    async def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根據 ID 獲取任務
        
        Args:
            task_id: 任務 ID
            
        Returns:
            任務物件或 None
        """
        return self._tasks.get(task_id)
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """取得任務詳情（TaskService 介面實作）"""
        return await self.get_task_by_id(task_id)
    
    async def update_task(self, task_id: str, request: TaskUpdateRequest) -> Task:
        """更新任務
        
        Args:
            task_id: 任務 ID
            request: 更新請求
            
        Returns:
            更新後的任務物件
            
        Raises:
            ValueError: 任務不存在或狀態不允許更新
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"任務不存在: {task_id}")
        
        # 檢查任務狀態是否允許更新
        if task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED]:
            raise ValueError("任務狀態不允許更新")
        
        # 更新任務屬性
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(task, field):
                setattr(task, field, value)
        
        task.updated_at = datetime.now()
        self.logger.info(f"更新任務: {task_id}")
        self._invalidate_cache()
        
        return task
    
    async def delete_task(self, task_id: str, force: bool = False) -> bool:
        """刪除任務
        
        Args:
            task_id: 任務 ID
            force: 是否強制刪除
            
        Returns:
            是否成功刪除
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        # 檢查是否可以刪除
        if task.status == TaskStatus.RUNNING and not force:
            raise ValueError("任務正在執行，請先停止或使用強制刪除")
        
        # 如果任務正在執行，先停止
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
        
        # 從佇列中移除
        if task_id in self._task_queue:
            self._task_queue.remove(task_id)
        
        # 刪除任務
        del self._tasks[task_id]
        
        self.logger.info(f"刪除任務: {task_id}")
        self._invalidate_cache()
        
        return True
    
    async def list_tasks(self, filters: TaskFilter) -> List[Task]:
        """列出任務（TaskService 介面實作）"""
        tasks = list(self._tasks.values())
        
        # 應用篩選條件
        if filters.status:
            tasks = [t for t in tasks if t.status in filters.status]
        
        if filters.task_type:
            tasks = [t for t in tasks if t.task_type in filters.task_type]
        
        if filters.priority:
            tasks = [t for t in tasks if t.priority in filters.priority]
        
        if filters.start_date:
            tasks = [t for t in tasks if t.created_at >= filters.start_date]
        
        if filters.end_date:
            tasks = [t for t in tasks if t.created_at <= filters.end_date]
        
        if filters.parent_task_id:
            tasks = [t for t in tasks if t.parent_task_id == filters.parent_task_id]
        
        if filters.search:
            search_lower = filters.search.lower()
            tasks = [t for t in tasks if 
                    search_lower in t.name.lower() or 
                    (t.description and search_lower in t.description.lower())]
        
        return tasks
    
    async def get_tasks_paginated(
        self, 
        page: int = 1, 
        size: int = 20, 
        sort_by: str = "created_at", 
        sort_order: str = "desc",
        **filters
    ) -> PaginatedResponse[Task]:
        """獲取分頁任務列表
        
        Args:
            page: 頁碼
            size: 每頁大小
            sort_by: 排序欄位
            sort_order: 排序順序
            **filters: 篩選條件
            
        Returns:
            分頁回應
        """
        # 建立篩選器
        task_filter = TaskFilter(**filters)
        tasks = await self.list_tasks(task_filter)
        
        # 排序
        reverse = sort_order.lower() == "desc"
        if hasattr(Task, sort_by):
            tasks.sort(key=lambda x: getattr(x, sort_by, None) or datetime.min, reverse=reverse)
        
        # 分頁
        total = len(tasks)
        start = (page - 1) * size
        end = start + size
        page_tasks = tasks[start:end]
        
        return PaginatedResponse(
            data=page_tasks,
            pagination={
                "page": page,
                "size": size,
                "total": total,
                "pages": (total + size - 1) // size
            },
            success=True,
            message="任務列表獲取成功"
        )
    
    async def execute_task_action(
        self, 
        task_id: str, 
        action: Union[str, TaskAction], 
        reason: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """執行任務操作
        
        Args:
            task_id: 任務 ID
            action: 操作類型
            reason: 操作原因
            options: 操作選項
            
        Returns:
            操作結果
        """
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"任務不存在: {task_id}")
        
        action_str = action.value if isinstance(action, TaskAction) else action
        
        if action_str == TaskAction.START:
            return await self._start_task(task_id)
        elif action_str == TaskAction.PAUSE:
            return await self._pause_task(task_id)
        elif action_str == TaskAction.RESUME:
            return await self._resume_task(task_id)
        elif action_str == TaskAction.CANCEL:
            return await self._cancel_task(task_id)
        elif action_str == TaskAction.RETRY:
            return await self._retry_task(task_id)
        else:
            raise ValueError(f"不支援的操作: {action_str}")
    
    async def execute_task(self, request: TaskExecutionRequest) -> Task:
        """執行任務操作（TaskService 介面實作）"""
        # 這個方法需要 task_id，但介面定義中沒有，需要調整
        raise NotImplementedError("請使用 execute_task_action 方法")
    
    async def batch_task_operation(
        self, 
        task_ids: List[str], 
        action: Union[str, TaskAction],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """批量任務操作
        
        Args:
            task_ids: 任務 ID 列表
            action: 操作類型
            reason: 操作原因
            
        Returns:
            批量操作結果
        """
        results = []
        errors = []
        successful_tasks = []
        
        for task_id in task_ids:
            try:
                result = await self.execute_task_action(task_id, action, reason)
                results.append({"task_id": task_id, "result": result})
                successful_tasks.append(task_id)
            except Exception as e:
                error_msg = f"任務 {task_id} 操作失敗: {str(e)}"
                errors.append(error_msg)
                self.logger.error(error_msg)
        
        return {
            "success": len(errors) == 0,
            "processed": len(successful_tasks),
            "failed": len(errors),
            "errors": errors,
            "task_results": results,
            "successful_tasks": successful_tasks,
            "message": f"批量操作完成，成功: {len(successful_tasks)}, 失敗: {len(errors)}"
        }
    
    async def batch_operation(self, request: TaskBatchRequest) -> Dict[str, Any]:
        """批量操作任務（TaskService 介面實作）"""
        return await self.batch_task_operation(request.task_ids, request.action)
    
    async def get_statistics(self) -> TaskStatistics:
        """取得任務統計資料
        
        Returns:
            任務統計資料
        """
        # 檢查快取
        if self._statistics_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
            return self._statistics_cache
        
        # 計算統計資料
        tasks = list(self._tasks.values())
        total = len(tasks)
        
        status_counts = defaultdict(int)
        for task in tasks:
            status_counts[task.status] += 1
        
        # 計算平均執行時長
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED and t.duration]
        avg_duration = sum(t.duration for t in completed_tasks) / len(completed_tasks) if completed_tasks else 0
        
        # 計算成功率
        finished_tasks = [t for t in tasks if t.is_finished()]
        success_rate = (status_counts[TaskStatus.COMPLETED] / len(finished_tasks) * 100) if finished_tasks else 0
        
        stats = TaskStatistics(
            total_tasks=total,
            pending_tasks=status_counts[TaskStatus.PENDING],
            running_tasks=status_counts[TaskStatus.RUNNING],
            completed_tasks=status_counts[TaskStatus.COMPLETED],
            failed_tasks=status_counts[TaskStatus.FAILED],
            cancelled_tasks=status_counts[TaskStatus.CANCELLED],
            average_duration=avg_duration,
            success_rate=success_rate,
            last_updated=datetime.now()
        )
        
        # 更新快取
        self._statistics_cache = stats
        self._cache_expiry = datetime.now() + timedelta(minutes=5)
        
        return stats
    
    async def get_task_logs(self, task_id: str, limit: int = 100, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """取得任務日誌
        
        Args:
            task_id: 任務 ID
            limit: 日誌條目數量限制
            level: 日誌等級篩選
            
        Returns:
            任務日誌列表
        """
        # 這裡應該從日誌系統中獲取任務相關的日誌
        # 目前返回模擬資料
        task = self._tasks.get(task_id)
        if not task:
            return []
        
        logs = [
            {
                "timestamp": task.created_at,
                "level": "INFO",
                "message": f"任務建立: {task.name}",
                "details": {"task_id": task_id, "task_type": task.task_type}
            }
        ]
        
        if task.start_time:
            logs.append({
                "timestamp": task.start_time,
                "level": "INFO",
                "message": "任務開始執行",
                "details": {"task_id": task_id}
            })
        
        if task.end_time:
            logs.append({
                "timestamp": task.end_time,
                "level": "INFO" if task.status == TaskStatus.COMPLETED else "ERROR",
                "message": f"任務執行完成，狀態: {task.status.value}",
                "details": {"task_id": task_id, "status": task.status.value}
            })
        
        # 應用篩選
        if level:
            logs = [log for log in logs if log["level"] == level.upper()]
        
        return logs[:limit]
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """獲取佇列狀態
        
        Returns:
            佇列狀態資訊
        """
        running_count = len(self._running_tasks)
        pending_count = len(self._task_queue)
        
        # 計算吞吐量（每分鐘處理任務數）
        # 這裡需要實際的統計資料，目前返回模擬值
        throughput = 0.0
        
        return {
            "is_running": self._is_running,
            "worker_count": len(self._worker_tasks),
            "pending_tasks": pending_count,
            "running_tasks": running_count,
            "max_concurrent": self._max_concurrent,
            "throughput": throughput,
            "average_wait_time": None,
            "last_processed": None
        }
    
    async def execute_queue_operation(
        self, 
        action: str, 
        filters: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """執行佇列操作
        
        Args:
            action: 操作類型
            filters: 篩選條件
            reason: 操作原因
            
        Returns:
            操作結果
        """
        if action == "start_all":
            return await self._start_queue_processing()
        elif action == "pause_all":
            return await self._pause_queue_processing()
        elif action == "clear_completed":
            return await self._clear_completed_tasks()
        elif action == "clear_failed":
            return await self._clear_failed_tasks()
        elif action == "clear_all":
            return await self._clear_all_tasks()
        else:
            raise ValueError(f"不支援的佇列操作: {action}")
    
    async def start_queue_processing(self):
        """啟動佇列處理"""
        await self._start_queue_processing()
    
    async def schedule_task(self, task_id: str):
        """排程任務執行"""
        if task_id not in self._task_queue:
            self._add_to_queue(task_id)
    
    async def get_available_task_types(self) -> List[str]:
        """獲取可用任務類型"""
        return [task_type.value for task_type in TaskType]
    
    async def get_task_templates(self, task_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """獲取任務模板"""
        templates = [
            {
                "id": "crawl_basic",
                "name": "基本爬蟲任務",
                "task_type": TaskType.CRAWL.value,
                "config": {
                    "url": "",
                    "method": "GET",
                    "timeout": 30,
                    "retry_count": 3
                }
            },
            {
                "id": "proxy_check",
                "name": "代理檢查任務",
                "task_type": TaskType.PROXY_CHECK.value,
                "config": {
                    "proxy_list": [],
                    "test_url": "http://httpbin.org/ip",
                    "timeout": 10
                }
            }
        ]
        
        if task_type:
            templates = [t for t in templates if t["task_type"] == task_type]
        
        return templates
    
    # ============= 私有方法 =============
    
    def _add_to_queue(self, task_id: str):
        """將任務加入佇列"""
        if task_id not in self._task_queue:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.PENDING:
                # 根據優先級插入佇列
                if task.priority == TaskPriority.HIGH:
                    self._task_queue.insert(0, task_id)
                else:
                    self._task_queue.append(task_id)
    
    async def _start_task(self, task_id: str) -> Dict[str, Any]:
        """啟動任務"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"任務不存在: {task_id}")
        
        if task.status != TaskStatus.PENDING:
            raise ValueError(f"任務狀態不允許啟動: {task.status}")
        
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.now()
        task.updated_at = datetime.now()
        
        # 建立執行任務
        execution_task = asyncio.create_task(self._execute_task_impl(task_id))
        self._running_tasks[task_id] = execution_task
        
        self.logger.info(f"啟動任務: {task_id}")
        self._invalidate_cache()
        
        return {"status": "started", "task_id": task_id}
    
    async def _pause_task(self, task_id: str) -> Dict[str, Any]:
        """暫停任務"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"任務不存在: {task_id}")
        
        if task.status != TaskStatus.RUNNING:
            raise ValueError(f"任務狀態不允許暫停: {task.status}")
        
        # 取消執行任務
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
        
        task.status = TaskStatus.PAUSED
        task.updated_at = datetime.now()
        
        self.logger.info(f"暫停任務: {task_id}")
        self._invalidate_cache()
        
        return {"status": "paused", "task_id": task_id}
    
    async def _resume_task(self, task_id: str) -> Dict[str, Any]:
        """恢復任務"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"任務不存在: {task_id}")
        
        if task.status != TaskStatus.PAUSED:
            raise ValueError(f"任務狀態不允許恢復: {task.status}")
        
        return await self._start_task(task_id)
    
    async def _cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任務"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"任務不存在: {task_id}")
        
        if task.is_finished():
            raise ValueError(f"任務已完成，無法取消: {task.status}")
        
        # 取消執行任務
        if task_id in self._running_tasks:
            self._running_tasks[task_id].cancel()
            del self._running_tasks[task_id]
        
        # 從佇列中移除
        if task_id in self._task_queue:
            self._task_queue.remove(task_id)
        
        task.status = TaskStatus.CANCELLED
        task.end_time = datetime.now()
        task.updated_at = datetime.now()
        
        self.logger.info(f"取消任務: {task_id}")
        self._invalidate_cache()
        
        return {"status": "cancelled", "task_id": task_id}
    
    async def _retry_task(self, task_id: str) -> Dict[str, Any]:
        """重試任務"""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"任務不存在: {task_id}")
        
        if not task.can_retry():
            raise ValueError("任務不能重試")
        
        task.retry_count += 1
        task.status = TaskStatus.PENDING
        task.error_message = None
        task.updated_at = datetime.now()
        
        # 重新加入佇列
        self._add_to_queue(task_id)
        
        self.logger.info(f"重試任務: {task_id} (第 {task.retry_count} 次)")
        self._invalidate_cache()
        
        return {"status": "retrying", "task_id": task_id, "retry_count": task.retry_count}
    
    async def _execute_task_impl(self, task_id: str):
        """任務執行實作"""
        task = self._tasks.get(task_id)
        if not task:
            return
        
        try:
            # 模擬任務執行
            self.logger.info(f"執行任務: {task.name} ({task_id})")
            
            # 根據任務類型執行不同邏輯
            if task.task_type == TaskType.CRAWL.value:
                await self._execute_crawl_task(task)
            elif task.task_type == TaskType.PROXY_CHECK.value:
                await self._execute_proxy_check_task(task)
            else:
                # 預設執行邏輯
                await asyncio.sleep(2)  # 模擬執行時間
                task.progress = 100.0
            
            # 任務完成
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.now()
            task.duration = int((task.end_time - task.start_time).total_seconds())
            task.result = {"status": "success", "message": "任務執行成功"}
            
        except asyncio.CancelledError:
            # 任務被取消
            task.status = TaskStatus.CANCELLED
            task.end_time = datetime.now()
            if task.start_time:
                task.duration = int((task.end_time - task.start_time).total_seconds())
            
        except Exception as e:
            # 任務執行失敗
            task.status = TaskStatus.FAILED
            task.end_time = datetime.now()
            if task.start_time:
                task.duration = int((task.end_time - task.start_time).total_seconds())
            task.error_message = str(e)
            
            self.logger.error(f"任務執行失敗: {task_id} - {str(e)}")
        
        finally:
            task.updated_at = datetime.now()
            # 從執行中任務列表移除
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            
            self._invalidate_cache()
    
    async def _execute_crawl_task(self, task: Task):
        """執行爬蟲任務"""
        # 模擬爬蟲執行
        for i in range(10):
            await asyncio.sleep(0.2)
            task.progress = (i + 1) * 10
            task.updated_at = datetime.now()
    
    async def _execute_proxy_check_task(self, task: Task):
        """執行代理檢查任務"""
        # 模擬代理檢查
        for i in range(5):
            await asyncio.sleep(0.5)
            task.progress = (i + 1) * 20
            task.updated_at = datetime.now()
    
    async def _start_queue_processing(self) -> Dict[str, Any]:
        """啟動佇列處理"""
        if self._is_running:
            return {"status": "already_running", "message": "佇列處理已在執行中"}
        
        self._is_running = True
        
        # 啟動工作執行緒
        for i in range(self._max_concurrent):
            worker = asyncio.create_task(self._queue_worker(f"worker-{i}"))
            self._worker_tasks.append(worker)
        
        self.logger.info("啟動佇列處理")
        return {"status": "started", "message": "佇列處理已啟動"}
    
    async def _pause_queue_processing(self) -> Dict[str, Any]:
        """暫停佇列處理"""
        if not self._is_running:
            return {"status": "not_running", "message": "佇列處理未在執行"}
        
        self._is_running = False
        
        # 停止工作執行緒
        for worker in self._worker_tasks:
            worker.cancel()
        
        self._worker_tasks.clear()
        
        self.logger.info("暫停佇列處理")
        return {"status": "paused", "message": "佇列處理已暫停"}
    
    async def _clear_completed_tasks(self) -> Dict[str, Any]:
        """清理已完成任務"""
        completed_ids = [task_id for task_id, task in self._tasks.items() 
                        if task.status == TaskStatus.COMPLETED]
        
        for task_id in completed_ids:
            del self._tasks[task_id]
        
        self.logger.info(f"清理已完成任務: {len(completed_ids)} 個")
        self._invalidate_cache()
        
        return {"status": "cleared", "count": len(completed_ids), "message": f"已清理 {len(completed_ids)} 個已完成任務"}
    
    async def _clear_failed_tasks(self) -> Dict[str, Any]:
        """清理失敗任務"""
        failed_ids = [task_id for task_id, task in self._tasks.items() 
                     if task.status == TaskStatus.FAILED]
        
        for task_id in failed_ids:
            del self._tasks[task_id]
        
        self.logger.info(f"清理失敗任務: {len(failed_ids)} 個")
        self._invalidate_cache()
        
        return {"status": "cleared", "count": len(failed_ids), "message": f"已清理 {len(failed_ids)} 個失敗任務"}
    
    async def _clear_all_tasks(self) -> Dict[str, Any]:
        """清理所有任務"""
        # 停止所有執行中的任務
        for task_id, execution_task in self._running_tasks.items():
            execution_task.cancel()
        
        count = len(self._tasks)
        self._tasks.clear()
        self._task_queue.clear()
        self._running_tasks.clear()
        
        self.logger.info(f"清理所有任務: {count} 個")
        self._invalidate_cache()
        
        return {"status": "cleared", "count": count, "message": f"已清理所有 {count} 個任務"}
    
    async def _queue_worker(self, worker_name: str):
        """佇列工作執行緒"""
        self.logger.info(f"啟動佇列工作執行緒: {worker_name}")
        
        while self._is_running:
            try:
                # 檢查是否有待執行任務
                if not self._task_queue:
                    await asyncio.sleep(1)
                    continue
                
                # 檢查並發限制
                if len(self._running_tasks) >= self._max_concurrent:
                    await asyncio.sleep(1)
                    continue
                
                # 取得下一個任務
                task_id = self._task_queue.pop(0)
                task = self._tasks.get(task_id)
                
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # 檢查排程時間
                if task.scheduled_time and task.scheduled_time > datetime.now():
                    # 重新加入佇列
                    self._task_queue.append(task_id)
                    await asyncio.sleep(1)
                    continue
                
                # 啟動任務
                await self._start_task(task_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"佇列工作執行緒錯誤 ({worker_name}): {str(e)}")
                await asyncio.sleep(1)
        
        self.logger.info(f"佇列工作執行緒停止: {worker_name}")
    
    def _invalidate_cache(self):
        """使快取失效"""
        self._statistics_cache = None
        self._cache_expiry = None