"""任務佇列 API 模組

提供任務管理相關的 API 端點，包括任務的建立、查詢、更新和刪除等功能。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..core.base import BaseResponse, PaginatedResponse
from ..core.tasks import (
    Task, TaskFilter, TaskCreateRequest, TaskUpdateRequest,
    TaskBatchRequest, TaskStatistics, TaskService
)

# 創建路由器
router = APIRouter(prefix="/api/v1/tasks", tags=["任務佇列"])

# 模擬任務服務實例（實際應用中應該通過依賴注入）
class MockTaskService(TaskService):
    """模擬任務服務實作"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_counter = 0
    
    async def initialize(self) -> None:
        """初始化服務"""
        pass
    
    async def cleanup(self) -> None:
        """清理服務資源"""
        pass
    
    async def create_task(self, request: TaskCreateRequest) -> Task:
        """建立新任務"""
        self.task_counter += 1
        task_id = f"task_{self.task_counter:06d}"
        
        task = Task(
            id=task_id,
            name=request.name,
            description=request.description,
            task_type=request.task_type,
            priority=request.priority,
            config=request.config,
            tags=request.tags or [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        """取得單一任務"""
        return self.tasks.get(task_id)
    
    async def list_tasks(self, filters: Optional[TaskFilter] = None, 
                        skip: int = 0, limit: int = 20) -> List[Task]:
        """列出任務"""
        tasks = list(self.tasks.values())
        
        # 簡單篩選邏輯
        if filters:
            if filters.status:
                tasks = [t for t in tasks if t.status in filters.status]
            if filters.task_types:
                tasks = [t for t in tasks if t.task_type in filters.task_types]
            if filters.priorities:
                tasks = [t for t in tasks if t.priority in filters.priorities]
        
        return tasks[skip:skip + limit]
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> Task:
        """更新任務"""
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self.tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        task.updated_at = datetime.now()
        return task
    
    async def delete_task(self, task_id: str) -> bool:
        """刪除任務"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
    
    async def get_statistics(self, filters: Optional[TaskFilter] = None) -> TaskStatistics:
        """取得任務統計"""
        tasks = list(self.tasks.values())
        
        return TaskStatistics(
            total_tasks=len(tasks),
            pending_tasks=len([t for t in tasks if t.status == "pending"]),
            running_tasks=len([t for t in tasks if t.status == "running"]),
            completed_tasks=len([t for t in tasks if t.status == "completed"]),
            failed_tasks=len([t for t in tasks if t.status == "failed"]),
            success_rate=0.85,  # 模擬數據
            average_duration=120.5,  # 模擬數據
            last_updated=datetime.now()
        )


# 全域任務服務實例
task_service = MockTaskService()


def get_task_service() -> TaskService:
    """取得任務服務實例"""
    return task_service


@router.get("/", response_model=PaginatedResponse[Task])
async def list_tasks(
    page: int = Query(1, ge=1, description="頁碼"),
    page_size: int = Query(20, ge=1, le=100, description="每頁數量"),
    status: Optional[List[str]] = Query(None, description="任務狀態篩選"),
    task_type: Optional[List[str]] = Query(None, description="任務類型篩選"),
    priority: Optional[List[str]] = Query(None, description="優先級篩選"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    service: TaskService = Depends(get_task_service)
):
    """列出任務
    
    支援分頁、篩選和搜尋功能。
    """
    try:
        # 建立篩選器
        filters = TaskFilter(
            status=status,
            task_types=task_type,
            priorities=priority,
            search_query=search
        )
        
        # 計算分頁參數
        skip = (page - 1) * page_size
        
        # 取得任務列表
        tasks = await service.list_tasks(filters, skip, page_size)
        
        # 取得總數（簡化實作）
        total = len(tasks) + skip
        
        return PaginatedResponse(
            items=tasks,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得任務列表失敗: {str(e)}")


@router.get("/statistics", response_model=TaskStatistics)
async def get_task_statistics(
    status: Optional[List[str]] = Query(None, description="任務狀態篩選"),
    task_type: Optional[List[str]] = Query(None, description="任務類型篩選"),
    service: TaskService = Depends(get_task_service)
):
    """取得任務統計資訊"""
    try:
        filters = TaskFilter(
            status=status,
            task_types=task_type
        )
        
        statistics = await service.get_statistics(filters)
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得任務統計失敗: {str(e)}")


@router.post("/", response_model=BaseResponse[Task])
async def create_task(
    request: TaskCreateRequest,
    service: TaskService = Depends(get_task_service)
):
    """建立新任務"""
    try:
        task = await service.create_task(request)
        
        return BaseResponse(
            success=True,
            message="任務建立成功",
            data=task
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"建立任務失敗: {str(e)}")


@router.get("/{task_id}", response_model=BaseResponse[Task])
async def get_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
):
    """取得單一任務詳情"""
    try:
        task = await service.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        return BaseResponse(
            success=True,
            message="取得任務成功",
            data=task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取得任務失敗: {str(e)}")


@router.put("/{task_id}", response_model=BaseResponse[Task])
async def update_task(
    task_id: str,
    request: TaskUpdateRequest,
    service: TaskService = Depends(get_task_service)
):
    """更新任務"""
    try:
        # 檢查任務是否存在
        existing_task = await service.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 準備更新資料
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = request.status
        if request.priority is not None:
            updates["priority"] = request.priority
        if request.config is not None:
            updates["config"] = request.config
        if request.tags is not None:
            updates["tags"] = request.tags
        
        # 更新任務
        updated_task = await service.update_task(task_id, updates)
        
        return BaseResponse(
            success=True,
            message="任務更新成功",
            data=updated_task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新任務失敗: {str(e)}")


@router.delete("/{task_id}", response_model=BaseResponse[bool])
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
):
    """刪除任務"""
    try:
        # 檢查任務是否存在
        existing_task = await service.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 刪除任務
        success = await service.delete_task(task_id)
        
        return BaseResponse(
            success=success,
            message="任務刪除成功" if success else "任務刪除失敗",
            data=success
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"刪除任務失敗: {str(e)}")


@router.post("/batch", response_model=BaseResponse[Dict[str, Any]])
async def batch_operations(
    request: TaskBatchRequest,
    service: TaskService = Depends(get_task_service)
):
    """批次操作任務"""
    try:
        results = {
            "success_count": 0,
            "failed_count": 0,
            "results": []
        }
        
        for task_id in request.task_ids:
            try:
                if request.action == "delete":
                    success = await service.delete_task(task_id)
                    if success:
                        results["success_count"] += 1
                        results["results"].append({"task_id": task_id, "status": "success"})
                    else:
                        results["failed_count"] += 1
                        results["results"].append({"task_id": task_id, "status": "failed", "error": "任務不存在"})
                
                elif request.action == "update_status":
                    if not request.data or "status" not in request.data:
                        raise ValueError("缺少狀態參數")
                    
                    await service.update_task(task_id, {"status": request.data["status"]})
                    results["success_count"] += 1
                    results["results"].append({"task_id": task_id, "status": "success"})
                
                else:
                    results["failed_count"] += 1
                    results["results"].append({"task_id": task_id, "status": "failed", "error": "不支援的操作"})
                    
            except Exception as e:
                results["failed_count"] += 1
                results["results"].append({"task_id": task_id, "status": "failed", "error": str(e)})
        
        return BaseResponse(
            success=True,
            message=f"批次操作完成，成功: {results['success_count']}, 失敗: {results['failed_count']}",
            data=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批次操作失敗: {str(e)}")


@router.post("/{task_id}/start", response_model=BaseResponse[Task])
async def start_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
):
    """啟動任務"""
    try:
        # 檢查任務是否存在
        existing_task = await service.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 更新任務狀態為執行中
        updated_task = await service.update_task(task_id, {
            "status": "running",
            "started_at": datetime.now()
        })
        
        return BaseResponse(
            success=True,
            message="任務啟動成功",
            data=updated_task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"啟動任務失敗: {str(e)}")


@router.post("/{task_id}/stop", response_model=BaseResponse[Task])
async def stop_task(
    task_id: str,
    service: TaskService = Depends(get_task_service)
):
    """停止任務"""
    try:
        # 檢查任務是否存在
        existing_task = await service.get_task(task_id)
        if not existing_task:
            raise HTTPException(status_code=404, detail="任務不存在")
        
        # 更新任務狀態為已停止
        updated_task = await service.update_task(task_id, {
            "status": "stopped",
            "finished_at": datetime.now()
        })
        
        return BaseResponse(
            success=True,
            message="任務停止成功",
            data=updated_task
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止任務失敗: {str(e)}")