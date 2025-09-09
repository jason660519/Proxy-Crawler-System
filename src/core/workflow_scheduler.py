"""工作流程調度器模組

提供智能任務分配和負載均衡的高級調度功能，包括：
- 工作流程管理
- 智能任務分配
- 負載均衡
- 資源監控
- 依賴關係處理
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass, field
import logging
import psutil
from concurrent.futures import ThreadPoolExecutor

from .task_manager import TaskManager, TaskType, TaskAction
from .tasks import Task, TaskCreateRequest, TaskStatistics
from .base import TaskStatus, TaskPriority


class WorkflowStatus(str, Enum):
    """工作流程狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SchedulingStrategy(str, Enum):
    """調度策略枚舉"""
    FIFO = "fifo"  # 先進先出
    PRIORITY = "priority"  # 優先級調度
    ROUND_ROBIN = "round_robin"  # 輪詢調度
    LOAD_BALANCED = "load_balanced"  # 負載均衡
    DEPENDENCY_AWARE = "dependency_aware"  # 依賴感知調度


class ResourceType(str, Enum):
    """資源類型枚舉"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DISK = "disk"
    CUSTOM = "custom"


@dataclass
class ResourceRequirement:
    """資源需求定義"""
    resource_type: ResourceType
    amount: float
    unit: str = "percent"  # percent, mb, gb, count
    max_amount: Optional[float] = None


@dataclass
class WorkerNode:
    """工作節點定義"""
    node_id: str
    name: str
    capacity: Dict[ResourceType, float]
    current_load: Dict[ResourceType, float] = field(default_factory=dict)
    active_tasks: Set[str] = field(default_factory=set)
    is_healthy: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_load_percentage(self, resource_type: ResourceType) -> float:
        """獲取資源負載百分比"""
        if resource_type not in self.capacity:
            return 0.0
        current = self.current_load.get(resource_type, 0.0)
        capacity = self.capacity[resource_type]
        return (current / capacity * 100) if capacity > 0 else 0.0

    def can_handle_task(self, requirements: List[ResourceRequirement]) -> bool:
        """檢查是否能處理任務"""
        for req in requirements:
            current_load = self.current_load.get(req.resource_type, 0.0)
            capacity = self.capacity.get(req.resource_type, 0.0)
            if current_load + req.amount > capacity:
                return False
        return True


@dataclass
class WorkflowDefinition:
    """工作流程定義"""
    workflow_id: str
    name: str
    description: Optional[str] = None
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    scheduling_strategy: SchedulingStrategy = SchedulingStrategy.DEPENDENCY_AWARE
    max_parallel_tasks: int = 5
    timeout: Optional[int] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowInstance:
    """工作流程實例"""
    instance_id: str
    workflow_id: str
    status: WorkflowStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_instances: Dict[str, str] = field(default_factory=dict)  # task_name -> task_id
    execution_context: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class SchedulingMetrics:
    """調度指標"""
    total_tasks_scheduled: int = 0
    average_wait_time: float = 0.0
    average_execution_time: float = 0.0
    throughput: float = 0.0  # 每分鐘處理任務數
    resource_utilization: Dict[ResourceType, float] = field(default_factory=dict)
    load_balance_score: float = 0.0  # 負載均衡分數 (0-100)
    last_updated: datetime = field(default_factory=datetime.now)


class WorkflowScheduler:
    """工作流程調度器
    
    提供智能任務分配和負載均衡功能，支持複雜的工作流程管理。
    """
    
    def __init__(self, task_manager: TaskManager):
        """初始化工作流程調度器
        
        Args:
            task_manager: 任務管理器實例
        """
        self.logger = logging.getLogger(__name__)
        self.task_manager = task_manager
        
        # 工作流程管理
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.workflow_instances: Dict[str, WorkflowInstance] = {}
        
        # 節點管理
        self.worker_nodes: Dict[str, WorkerNode] = {}
        self.local_node_id = self._create_local_node()
        
        # 調度配置
        self.default_strategy = SchedulingStrategy.LOAD_BALANCED
        self.max_concurrent_workflows = 10
        self.resource_monitor_interval = 30  # 秒
        
        # 調度隊列
        self.workflow_queue: deque = deque()
        self.task_assignment_queue: deque = deque()
        
        # 統計和監控
        self.metrics = SchedulingMetrics()
        self.task_wait_times: deque = deque(maxlen=1000)
        self.task_execution_times: deque = deque(maxlen=1000)
        
        # 執行器
        self.thread_executor = ThreadPoolExecutor(max_workers=4)
        
        # 控制標誌
        self._is_running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
    
    def _create_local_node(self) -> str:
        """創建本地工作節點"""
        node_id = f"local-{uuid.uuid4().hex[:8]}"
        
        # 獲取系統資源信息
        cpu_count = psutil.cpu_count()
        memory_total = psutil.virtual_memory().total / (1024 ** 3)  # GB
        
        local_node = WorkerNode(
            node_id=node_id,
            name="Local Worker Node",
            capacity={
                ResourceType.CPU: cpu_count * 100,  # CPU 百分比
                ResourceType.MEMORY: memory_total * 1024,  # MB
                ResourceType.NETWORK: 1000,  # Mbps
                ResourceType.DISK: 1000  # MB/s
            },
            metadata={
                "type": "local",
                "hostname": "localhost",
                "created_at": datetime.now().isoformat()
            }
        )
        
        self.worker_nodes[node_id] = local_node
        self.logger.info(f"創建本地工作節點: {node_id}")
        
        return node_id
    
    async def start(self) -> None:
        """啟動調度器"""
        if self._is_running:
            return
        
        self._is_running = True
        self.logger.info("啟動工作流程調度器")
        
        # 啟動調度任務
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        self._monitor_task = asyncio.create_task(self._resource_monitor_loop())
    
    async def stop(self) -> None:
        """停止調度器"""
        if not self._is_running:
            return
        
        self._is_running = False
        self.logger.info("停止工作流程調度器")
        
        # 取消調度任務
        if self._scheduler_task:
            self._scheduler_task.cancel()
        if self._monitor_task:
            self._monitor_task.cancel()
        
        # 關閉執行器
        self.thread_executor.shutdown(wait=True)
    
    async def register_workflow(self, workflow: WorkflowDefinition) -> None:
        """註冊工作流程定義
        
        Args:
            workflow: 工作流程定義
        """
        self.workflows[workflow.workflow_id] = workflow
        self.logger.info(f"註冊工作流程: {workflow.name} ({workflow.workflow_id})")
    
    async def start_workflow(
        self, 
        workflow_id: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """啟動工作流程實例
        
        Args:
            workflow_id: 工作流程ID
            context: 執行上下文
            
        Returns:
            工作流程實例ID
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"工作流程不存在: {workflow_id}")
        
        instance_id = str(uuid.uuid4())
        instance = WorkflowInstance(
            instance_id=instance_id,
            workflow_id=workflow_id,
            status=WorkflowStatus.PENDING,
            created_at=datetime.now(),
            execution_context=context or {}
        )
        
        self.workflow_instances[instance_id] = instance
        self.workflow_queue.append(instance_id)
        
        self.logger.info(f"啟動工作流程實例: {instance_id}")
        return instance_id
    
    async def get_workflow_status(self, instance_id: str) -> Optional[WorkflowInstance]:
        """獲取工作流程狀態
        
        Args:
            instance_id: 工作流程實例ID
            
        Returns:
            工作流程實例或None
        """
        return self.workflow_instances.get(instance_id)
    
    async def cancel_workflow(self, instance_id: str) -> bool:
        """取消工作流程
        
        Args:
            instance_id: 工作流程實例ID
            
        Returns:
            是否成功取消
        """
        instance = self.workflow_instances.get(instance_id)
        if not instance:
            return False
        
        if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            return False
        
        # 取消所有相關任務
        for task_id in instance.task_instances.values():
            try:
                await self.task_manager.execute_task_action(task_id, TaskAction.CANCEL)
            except Exception as e:
                self.logger.warning(f"取消任務失敗: {task_id}, 錯誤: {e}")
        
        instance.status = WorkflowStatus.CANCELLED
        instance.completed_at = datetime.now()
        
        self.logger.info(f"取消工作流程: {instance_id}")
        return True
    
    async def add_worker_node(self, node: WorkerNode) -> None:
        """添加工作節點
        
        Args:
            node: 工作節點
        """
        self.worker_nodes[node.node_id] = node
        self.logger.info(f"添加工作節點: {node.name} ({node.node_id})")
    
    async def remove_worker_node(self, node_id: str) -> bool:
        """移除工作節點
        
        Args:
            node_id: 節點ID
            
        Returns:
            是否成功移除
        """
        if node_id == self.local_node_id:
            self.logger.warning("無法移除本地節點")
            return False
        
        if node_id in self.worker_nodes:
            node = self.worker_nodes[node_id]
            
            # 重新分配該節點上的任務
            if node.active_tasks:
                self.logger.info(f"重新分配節點 {node_id} 上的 {len(node.active_tasks)} 個任務")
                for task_id in list(node.active_tasks):
                    await self._reassign_task(task_id)
            
            del self.worker_nodes[node_id]
            self.logger.info(f"移除工作節點: {node_id}")
            return True
        
        return False
    
    async def get_scheduling_metrics(self) -> SchedulingMetrics:
        """獲取調度指標
        
        Returns:
            調度指標
        """
        # 更新指標
        await self._update_metrics()
        return self.metrics
    
    async def get_node_status(self) -> List[Dict[str, Any]]:
        """獲取所有節點狀態
        
        Returns:
            節點狀態列表
        """
        node_status = []
        
        for node in self.worker_nodes.values():
            status = {
                "node_id": node.node_id,
                "name": node.name,
                "is_healthy": node.is_healthy,
                "active_tasks": len(node.active_tasks),
                "capacity": node.capacity,
                "current_load": node.current_load,
                "load_percentages": {
                    resource_type.value: node.get_load_percentage(resource_type)
                    for resource_type in ResourceType
                },
                "last_heartbeat": node.last_heartbeat,
                "metadata": node.metadata
            }
            node_status.append(status)
        
        return node_status
    
    async def _scheduler_loop(self) -> None:
        """調度器主循環"""
        self.logger.info("調度器主循環啟動")
        
        while self._is_running:
            try:
                # 處理工作流程隊列
                await self._process_workflow_queue()
                
                # 處理任務分配隊列
                await self._process_task_assignment_queue()
                
                # 檢查工作流程狀態
                await self._check_workflow_status()
                
                # 短暫休眠
                await asyncio.sleep(1)
                
            except Exception as e:
                self.logger.error(f"調度器循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _resource_monitor_loop(self) -> None:
        """資源監控循環"""
        self.logger.info("資源監控循環啟動")
        
        while self._is_running:
            try:
                # 更新本地節點資源使用情況
                await self._update_local_node_resources()
                
                # 檢查節點健康狀態
                await self._check_node_health()
                
                # 更新調度指標
                await self._update_metrics()
                
                await asyncio.sleep(self.resource_monitor_interval)
                
            except Exception as e:
                self.logger.error(f"資源監控錯誤: {e}")
                await asyncio.sleep(30)
    
    async def _process_workflow_queue(self) -> None:
        """處理工作流程隊列"""
        while self.workflow_queue and len([i for i in self.workflow_instances.values() 
                                          if i.status == WorkflowStatus.RUNNING]) < self.max_concurrent_workflows:
            instance_id = self.workflow_queue.popleft()
            instance = self.workflow_instances.get(instance_id)
            
            if not instance or instance.status != WorkflowStatus.PENDING:
                continue
            
            try:
                await self._start_workflow_execution(instance)
            except Exception as e:
                self.logger.error(f"啟動工作流程失敗: {instance_id}, 錯誤: {e}")
                instance.status = WorkflowStatus.FAILED
                instance.error_message = str(e)
                instance.completed_at = datetime.now()
    
    async def _start_workflow_execution(self, instance: WorkflowInstance) -> None:
        """開始執行工作流程
        
        Args:
            instance: 工作流程實例
        """
        workflow = self.workflows[instance.workflow_id]
        
        instance.status = WorkflowStatus.RUNNING
        instance.started_at = datetime.now()
        
        self.logger.info(f"開始執行工作流程: {instance.instance_id}")
        
        # 根據調度策略創建任務
        if workflow.scheduling_strategy == SchedulingStrategy.DEPENDENCY_AWARE:
            await self._schedule_dependency_aware(instance, workflow)
        else:
            await self._schedule_simple(instance, workflow)
    
    async def _schedule_dependency_aware(self, instance: WorkflowInstance, workflow: WorkflowDefinition) -> None:
        """依賴感知調度
        
        Args:
            instance: 工作流程實例
            workflow: 工作流程定義
        """
        # 構建依賴圖
        dependency_graph = workflow.dependencies
        
        # 找到沒有依賴的任務（入度為0）
        ready_tasks = []
        for task_def in workflow.tasks:
            task_name = task_def["name"]
            if task_name not in dependency_graph or not dependency_graph[task_name]:
                ready_tasks.append(task_def)
        
        # 創建並調度就緒的任務
        for task_def in ready_tasks:
            await self._create_and_schedule_task(instance, task_def)
    
    async def _schedule_simple(self, instance: WorkflowInstance, workflow: WorkflowDefinition) -> None:
        """簡單調度（忽略依賴關係）
        
        Args:
            instance: 工作流程實例
            workflow: 工作流程定義
        """
        for task_def in workflow.tasks:
            await self._create_and_schedule_task(instance, task_def)
    
    async def _create_and_schedule_task(self, instance: WorkflowInstance, task_def: Dict[str, Any]) -> None:
        """創建並調度任務
        
        Args:
            instance: 工作流程實例
            task_def: 任務定義
        """
        task_request = TaskCreateRequest(
            name=task_def["name"],
            description=task_def.get("description"),
            task_type=task_def.get("type", TaskType.CUSTOM),
            priority=TaskPriority(task_def.get("priority", "medium")),
            config=task_def.get("config", {}),
            metadata={
                "workflow_instance_id": instance.instance_id,
                "workflow_id": instance.workflow_id,
                **task_def.get("metadata", {})
            }
        )
        
        # 創建任務
        task = await self.task_manager.create_task(task_request)
        instance.task_instances[task_def["name"]] = task.id
        
        # 添加到任務分配隊列
        self.task_assignment_queue.append({
            "task_id": task.id,
            "requirements": task_def.get("resource_requirements", []),
            "created_at": datetime.now()
        })
        
        self.logger.info(f"創建工作流程任務: {task.name} ({task.id})")
    
    async def _process_task_assignment_queue(self) -> None:
        """處理任務分配隊列"""
        processed_assignments = []
        
        while self.task_assignment_queue:
            assignment = self.task_assignment_queue.popleft()
            task_id = assignment["task_id"]
            requirements = assignment["requirements"]
            
            # 選擇最佳節點
            best_node = await self._select_best_node(requirements)
            
            if best_node:
                # 分配任務到節點
                await self._assign_task_to_node(task_id, best_node.node_id, requirements)
                
                # 記錄等待時間
                wait_time = (datetime.now() - assignment["created_at"]).total_seconds()
                self.task_wait_times.append(wait_time)
                
            else:
                # 沒有可用節點，重新加入隊列
                processed_assignments.append(assignment)
        
        # 將無法分配的任務重新加入隊列
        for assignment in processed_assignments:
            self.task_assignment_queue.append(assignment)
    
    async def _select_best_node(self, requirements: List[Dict[str, Any]]) -> Optional[WorkerNode]:
        """選擇最佳工作節點
        
        Args:
            requirements: 資源需求列表
            
        Returns:
            最佳工作節點或None
        """
        # 轉換需求格式
        resource_requirements = []
        for req in requirements:
            resource_requirements.append(ResourceRequirement(
                resource_type=ResourceType(req.get("type", "cpu")),
                amount=req.get("amount", 10),
                unit=req.get("unit", "percent")
            ))
        
        # 篩選可用節點
        available_nodes = []
        for node in self.worker_nodes.values():
            if node.is_healthy and node.can_handle_task(resource_requirements):
                available_nodes.append(node)
        
        if not available_nodes:
            return None
        
        # 根據負載選擇最佳節點
        best_node = min(available_nodes, key=lambda n: sum(
            n.get_load_percentage(rt) for rt in ResourceType
        ))
        
        return best_node
    
    async def _assign_task_to_node(
        self, 
        task_id: str, 
        node_id: str, 
        requirements: List[Dict[str, Any]]
    ) -> None:
        """將任務分配到節點
        
        Args:
            task_id: 任務ID
            node_id: 節點ID
            requirements: 資源需求
        """
        node = self.worker_nodes[node_id]
        
        # 更新節點負載
        for req in requirements:
            resource_type = ResourceType(req.get("type", "cpu"))
            amount = req.get("amount", 10)
            current_load = node.current_load.get(resource_type, 0.0)
            node.current_load[resource_type] = current_load + amount
        
        # 添加到活動任務
        node.active_tasks.add(task_id)
        
        # 啟動任務
        try:
            await self.task_manager.execute_task_action(task_id, TaskAction.START)
            self.logger.info(f"任務 {task_id} 分配到節點 {node_id}")
        except Exception as e:
            # 分配失敗，回滾資源
            for req in requirements:
                resource_type = ResourceType(req.get("type", "cpu"))
                amount = req.get("amount", 10)
                current_load = node.current_load.get(resource_type, 0.0)
                node.current_load[resource_type] = max(0, current_load - amount)
            
            node.active_tasks.discard(task_id)
            self.logger.error(f"任務分配失敗: {task_id}, 錯誤: {e}")
            raise
    
    async def _check_workflow_status(self) -> None:
        """檢查工作流程狀態"""
        for instance in list(self.workflow_instances.values()):
            if instance.status != WorkflowStatus.RUNNING:
                continue
            
            # 檢查所有任務狀態
            all_completed = True
            has_failed = False
            
            for task_id in instance.task_instances.values():
                task = await self.task_manager.get_task(task_id)
                if not task:
                    continue
                
                if task.status == TaskStatus.FAILED:
                    has_failed = True
                    break
                elif task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                    all_completed = False
            
            # 更新工作流程狀態
            if has_failed:
                instance.status = WorkflowStatus.FAILED
                instance.completed_at = datetime.now()
                self.logger.info(f"工作流程失敗: {instance.instance_id}")
            elif all_completed:
                instance.status = WorkflowStatus.COMPLETED
                instance.completed_at = datetime.now()
                self.logger.info(f"工作流程完成: {instance.instance_id}")
                
                # 處理依賴任務
                await self._handle_task_dependencies(instance)
    
    async def _handle_task_dependencies(self, instance: WorkflowInstance) -> None:
        """處理任務依賴關係
        
        Args:
            instance: 工作流程實例
        """
        workflow = self.workflows[instance.workflow_id]
        
        # 檢查是否有新的就緒任務
        for task_def in workflow.tasks:
            task_name = task_def["name"]
            
            # 如果任務已經創建，跳過
            if task_name in instance.task_instances:
                continue
            
            # 檢查依賴是否滿足
            dependencies = workflow.dependencies.get(task_name, [])
            dependencies_satisfied = True
            
            for dep_task_name in dependencies:
                if dep_task_name not in instance.task_instances:
                    dependencies_satisfied = False
                    break
                
                dep_task_id = instance.task_instances[dep_task_name]
                dep_task = await self.task_manager.get_task(dep_task_id)
                
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    dependencies_satisfied = False
                    break
            
            # 如果依賴滿足，創建任務
            if dependencies_satisfied:
                await self._create_and_schedule_task(instance, task_def)
    
    async def _reassign_task(self, task_id: str) -> None:
        """重新分配任務
        
        Args:
            task_id: 任務ID
        """
        # 暫停任務
        try:
            await self.task_manager.execute_task_action(task_id, TaskAction.PAUSE)
        except Exception as e:
            self.logger.warning(f"暫停任務失敗: {task_id}, 錯誤: {e}")
        
        # 重新加入分配隊列
        self.task_assignment_queue.append({
            "task_id": task_id,
            "requirements": [],  # 需要從任務元數據中獲取
            "created_at": datetime.now()
        })
    
    async def _update_local_node_resources(self) -> None:
        """更新本地節點資源使用情況"""
        local_node = self.worker_nodes[self.local_node_id]
        
        try:
            # 獲取系統資源使用情況
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_used_gb = memory_info.used / (1024 ** 3)
            
            # 更新節點負載
            local_node.current_load[ResourceType.CPU] = cpu_percent
            local_node.current_load[ResourceType.MEMORY] = memory_used_gb * 1024  # MB
            local_node.last_heartbeat = datetime.now()
            
        except Exception as e:
            self.logger.error(f"更新本地節點資源失敗: {e}")
    
    async def _check_node_health(self) -> None:
        """檢查節點健康狀態"""
        current_time = datetime.now()
        
        for node in self.worker_nodes.values():
            # 檢查心跳超時
            if node.node_id != self.local_node_id:
                time_since_heartbeat = (current_time - node.last_heartbeat).total_seconds()
                if time_since_heartbeat > 300:  # 5分鐘超時
                    if node.is_healthy:
                        node.is_healthy = False
                        self.logger.warning(f"節點 {node.node_id} 心跳超時，標記為不健康")
    
    async def _update_metrics(self) -> None:
        """更新調度指標"""
        # 計算平均等待時間
        if self.task_wait_times:
            self.metrics.average_wait_time = sum(self.task_wait_times) / len(self.task_wait_times)
        
        # 計算平均執行時間
        if self.task_execution_times:
            self.metrics.average_execution_time = sum(self.task_execution_times) / len(self.task_execution_times)
        
        # 計算吞吐量（每分鐘處理任務數）
        completed_tasks_last_minute = len([t for t in self.task_execution_times 
                                         if t < 60])  # 簡化計算
        self.metrics.throughput = completed_tasks_last_minute
        
        # 計算資源利用率
        total_utilization = {}
        for resource_type in ResourceType:
            total_capacity = sum(node.capacity.get(resource_type, 0) 
                               for node in self.worker_nodes.values())
            total_usage = sum(node.current_load.get(resource_type, 0) 
                            for node in self.worker_nodes.values())
            
            if total_capacity > 0:
                total_utilization[resource_type] = (total_usage / total_capacity) * 100
            else:
                total_utilization[resource_type] = 0.0
        
        self.metrics.resource_utilization = total_utilization
        
        # 計算負載均衡分數
        if len(self.worker_nodes) > 1:
            load_variances = []
            for resource_type in ResourceType:
                loads = [node.get_load_percentage(resource_type) 
                        for node in self.worker_nodes.values() if node.is_healthy]
                if loads:
                    avg_load = sum(loads) / len(loads)
                    variance = sum((load - avg_load) ** 2 for load in loads) / len(loads)
                    load_variances.append(variance)
            
            if load_variances:
                avg_variance = sum(load_variances) / len(load_variances)
                # 負載均衡分數：方差越小分數越高
                self.metrics.load_balance_score = max(0, 100 - avg_variance)
            else:
                self.metrics.load_balance_score = 100
        else:
            self.metrics.load_balance_score = 100
        
        self.metrics.last_updated = datetime.now()