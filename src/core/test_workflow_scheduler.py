"""工作流程調度器測試模組

測試WorkflowScheduler的各項功能，包括：
- 工作流程管理
- 智能任務分配
- 負載均衡
- 資源監控
- 依賴關係處理
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List

from .workflow_scheduler import (
    WorkflowScheduler, WorkflowDefinition, WorkflowInstance, WorkerNode,
    WorkflowStatus, SchedulingStrategy, ResourceType, ResourceRequirement,
    SchedulingMetrics
)
from .task_manager import TaskManager, TaskType, TaskAction
from .tasks import TaskCreateRequest
from .base import TaskStatus, TaskPriority


class TestWorkflowScheduler:
    """工作流程調度器測試類"""
    
    @pytest.fixture
    async def mock_task_manager(self):
        """模擬任務管理器"""
        task_manager = Mock(spec=TaskManager)
        task_manager.create_task = AsyncMock()
        task_manager.get_task = AsyncMock()
        task_manager.execute_task_action = AsyncMock()
        return task_manager
    
    @pytest.fixture
    async def scheduler(self, mock_task_manager):
        """創建調度器實例"""
        with patch('psutil.cpu_count', return_value=4), \
             patch('psutil.virtual_memory') as mock_memory:
            
            mock_memory.return_value.total = 8 * 1024 ** 3  # 8GB
            scheduler = WorkflowScheduler(mock_task_manager)
            yield scheduler
            await scheduler.stop()
    
    @pytest.fixture
    def sample_workflow(self):
        """示例工作流程定義"""
        return WorkflowDefinition(
            workflow_id="test-workflow-001",
            name="測試工作流程",
            description="用於測試的示例工作流程",
            tasks=[
                {
                    "name": "task1",
                    "description": "第一個任務",
                    "type": "validation",
                    "priority": "high",
                    "config": {"batch_size": 100},
                    "resource_requirements": [
                        {"type": "cpu", "amount": 20, "unit": "percent"},
                        {"type": "memory", "amount": 512, "unit": "mb"}
                    ]
                },
                {
                    "name": "task2",
                    "description": "第二個任務",
                    "type": "storage",
                    "priority": "medium",
                    "config": {"timeout": 30},
                    "resource_requirements": [
                        {"type": "cpu", "amount": 15, "unit": "percent"},
                        {"type": "memory", "amount": 256, "unit": "mb"}
                    ]
                },
                {
                    "name": "task3",
                    "description": "第三個任務",
                    "type": "analysis",
                    "priority": "low",
                    "config": {"depth": 5},
                    "resource_requirements": [
                        {"type": "cpu", "amount": 30, "unit": "percent"},
                        {"type": "memory", "amount": 1024, "unit": "mb"}
                    ]
                }
            ],
            dependencies={
                "task2": ["task1"],
                "task3": ["task1", "task2"]
            },
            scheduling_strategy=SchedulingStrategy.DEPENDENCY_AWARE,
            max_parallel_tasks=3
        )
    
    @pytest.fixture
    def sample_worker_node(self):
        """示例工作節點"""
        return WorkerNode(
            node_id="worker-001",
            name="測試工作節點",
            capacity={
                ResourceType.CPU: 400,  # 4核心 * 100%
                ResourceType.MEMORY: 8192,  # 8GB in MB
                ResourceType.NETWORK: 1000,
                ResourceType.DISK: 500
            },
            metadata={"type": "test", "location": "local"}
        )
    
    async def test_scheduler_initialization(self, scheduler):
        """測試調度器初始化"""
        assert scheduler is not None
        assert len(scheduler.worker_nodes) == 1  # 本地節點
        assert scheduler.local_node_id in scheduler.worker_nodes
        assert not scheduler._is_running
        assert scheduler.default_strategy == SchedulingStrategy.LOAD_BALANCED
    
    async def test_start_stop_scheduler(self, scheduler):
        """測試調度器啟動和停止"""
        # 啟動調度器
        await scheduler.start()
        assert scheduler._is_running
        assert scheduler._scheduler_task is not None
        assert scheduler._monitor_task is not None
        
        # 停止調度器
        await scheduler.stop()
        assert not scheduler._is_running
    
    async def test_register_workflow(self, scheduler, sample_workflow):
        """測試工作流程註冊"""
        await scheduler.register_workflow(sample_workflow)
        
        assert sample_workflow.workflow_id in scheduler.workflows
        registered_workflow = scheduler.workflows[sample_workflow.workflow_id]
        assert registered_workflow.name == sample_workflow.name
        assert len(registered_workflow.tasks) == 3
    
    async def test_start_workflow(self, scheduler, sample_workflow, mock_task_manager):
        """測試工作流程啟動"""
        # 註冊工作流程
        await scheduler.register_workflow(sample_workflow)
        
        # 模擬任務創建
        mock_task = Mock()
        mock_task.id = "task-001"
        mock_task.name = "task1"
        mock_task_manager.create_task.return_value = mock_task
        
        # 啟動工作流程
        context = {"user_id": "test-user", "batch_id": "batch-001"}
        instance_id = await scheduler.start_workflow(sample_workflow.workflow_id, context)
        
        assert instance_id is not None
        assert instance_id in scheduler.workflow_instances
        
        instance = scheduler.workflow_instances[instance_id]
        assert instance.workflow_id == sample_workflow.workflow_id
        assert instance.status == WorkflowStatus.PENDING
        assert instance.execution_context == context
        assert instance_id in [item for item in scheduler.workflow_queue]
    
    async def test_workflow_not_found(self, scheduler):
        """測試工作流程不存在的情況"""
        with pytest.raises(ValueError, match="工作流程不存在"):
            await scheduler.start_workflow("non-existent-workflow")
    
    async def test_get_workflow_status(self, scheduler, sample_workflow):
        """測試獲取工作流程狀態"""
        await scheduler.register_workflow(sample_workflow)
        instance_id = await scheduler.start_workflow(sample_workflow.workflow_id)
        
        status = await scheduler.get_workflow_status(instance_id)
        assert status is not None
        assert status.instance_id == instance_id
        assert status.status == WorkflowStatus.PENDING
        
        # 測試不存在的實例
        status = await scheduler.get_workflow_status("non-existent")
        assert status is None
    
    async def test_cancel_workflow(self, scheduler, sample_workflow, mock_task_manager):
        """測試取消工作流程"""
        await scheduler.register_workflow(sample_workflow)
        instance_id = await scheduler.start_workflow(sample_workflow.workflow_id)
        
        # 模擬任務實例
        instance = scheduler.workflow_instances[instance_id]
        instance.task_instances = {"task1": "task-001", "task2": "task-002"}
        instance.status = WorkflowStatus.RUNNING
        
        # 取消工作流程
        result = await scheduler.cancel_workflow(instance_id)
        assert result is True
        
        # 檢查狀態
        instance = scheduler.workflow_instances[instance_id]
        assert instance.status == WorkflowStatus.CANCELLED
        assert instance.completed_at is not None
        
        # 驗證任務取消調用
        assert mock_task_manager.execute_task_action.call_count == 2
    
    async def test_cancel_nonexistent_workflow(self, scheduler):
        """測試取消不存在的工作流程"""
        result = await scheduler.cancel_workflow("non-existent")
        assert result is False
    
    async def test_add_remove_worker_node(self, scheduler, sample_worker_node):
        """測試添加和移除工作節點"""
        initial_count = len(scheduler.worker_nodes)
        
        # 添加工作節點
        await scheduler.add_worker_node(sample_worker_node)
        assert len(scheduler.worker_nodes) == initial_count + 1
        assert sample_worker_node.node_id in scheduler.worker_nodes
        
        # 移除工作節點
        result = await scheduler.remove_worker_node(sample_worker_node.node_id)
        assert result is True
        assert len(scheduler.worker_nodes) == initial_count
        assert sample_worker_node.node_id not in scheduler.worker_nodes
    
    async def test_cannot_remove_local_node(self, scheduler):
        """測試無法移除本地節點"""
        result = await scheduler.remove_worker_node(scheduler.local_node_id)
        assert result is False
        assert scheduler.local_node_id in scheduler.worker_nodes
    
    async def test_worker_node_resource_management(self, sample_worker_node):
        """測試工作節點資源管理"""
        # 測試負載百分比計算
        sample_worker_node.current_load[ResourceType.CPU] = 200  # 50% of 400
        load_percentage = sample_worker_node.get_load_percentage(ResourceType.CPU)
        assert load_percentage == 50.0
        
        # 測試任務處理能力檢查
        requirements = [
            ResourceRequirement(ResourceType.CPU, 100, "percent"),
            ResourceRequirement(ResourceType.MEMORY, 1024, "mb")
        ]
        
        # 應該能處理
        assert sample_worker_node.can_handle_task(requirements) is True
        
        # 超出容量
        requirements[0].amount = 300  # 超出剩餘CPU容量
        assert sample_worker_node.can_handle_task(requirements) is False
    
    async def test_get_scheduling_metrics(self, scheduler):
        """測試獲取調度指標"""
        # 添加一些測試數據
        scheduler.task_wait_times.extend([1.0, 2.0, 3.0])
        scheduler.task_execution_times.extend([10.0, 15.0, 20.0])
        
        metrics = await scheduler.get_scheduling_metrics()
        
        assert isinstance(metrics, SchedulingMetrics)
        assert metrics.average_wait_time == 2.0
        assert metrics.average_execution_time == 15.0
        assert metrics.last_updated is not None
    
    async def test_get_node_status(self, scheduler, sample_worker_node):
        """測試獲取節點狀態"""
        await scheduler.add_worker_node(sample_worker_node)
        
        node_status = await scheduler.get_node_status()
        
        assert len(node_status) == 2  # 本地節點 + 添加的節點
        
        # 檢查節點狀態結構
        for status in node_status:
            assert "node_id" in status
            assert "name" in status
            assert "is_healthy" in status
            assert "active_tasks" in status
            assert "capacity" in status
            assert "current_load" in status
            assert "load_percentages" in status
            assert "last_heartbeat" in status
            assert "metadata" in status
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    async def test_resource_monitoring(self, mock_memory, mock_cpu, scheduler):
        """測試資源監控"""
        # 模擬系統資源
        mock_cpu.return_value = 45.5
        mock_memory.return_value.used = 4 * 1024 ** 3  # 4GB
        
        # 更新本地節點資源
        await scheduler._update_local_node_resources()
        
        local_node = scheduler.worker_nodes[scheduler.local_node_id]
        assert local_node.current_load[ResourceType.CPU] == 45.5
        assert local_node.current_load[ResourceType.MEMORY] == 4096  # 4GB in MB
    
    async def test_node_health_check(self, scheduler, sample_worker_node):
        """測試節點健康檢查"""
        # 添加節點
        await scheduler.add_worker_node(sample_worker_node)
        
        # 設置過期的心跳時間
        sample_worker_node.last_heartbeat = datetime.now() - timedelta(minutes=10)
        sample_worker_node.is_healthy = True
        
        # 執行健康檢查
        await scheduler._check_node_health()
        
        # 節點應該被標記為不健康
        assert not sample_worker_node.is_healthy
    
    async def test_task_assignment_queue_processing(self, scheduler, mock_task_manager):
        """測試任務分配隊列處理"""
        # 添加任務到分配隊列
        scheduler.task_assignment_queue.append({
            "task_id": "task-001",
            "requirements": [
                {"type": "cpu", "amount": 10, "unit": "percent"},
                {"type": "memory", "amount": 256, "unit": "mb"}
            ],
            "created_at": datetime.now()
        })
        
        # 處理分配隊列
        await scheduler._process_task_assignment_queue()
        
        # 檢查任務是否被分配
        local_node = scheduler.worker_nodes[scheduler.local_node_id]
        assert "task-001" in local_node.active_tasks
        assert mock_task_manager.execute_task_action.called
    
    async def test_dependency_aware_scheduling(self, scheduler, sample_workflow, mock_task_manager):
        """測試依賴感知調度"""
        # 模擬任務創建
        mock_task = Mock()
        mock_task.id = "task-001"
        mock_task.name = "task1"
        mock_task_manager.create_task.return_value = mock_task
        
        # 註冊並啟動工作流程
        await scheduler.register_workflow(sample_workflow)
        await scheduler.start()
        
        instance_id = await scheduler.start_workflow(sample_workflow.workflow_id)
        
        # 等待調度處理
        await asyncio.sleep(0.1)
        
        instance = scheduler.workflow_instances[instance_id]
        
        # 只有task1應該被創建（沒有依賴）
        assert "task1" in instance.task_instances
        # task2和task3應該等待task1完成
        assert "task2" not in instance.task_instances
        assert "task3" not in instance.task_instances
    
    async def test_workflow_completion_detection(self, scheduler, sample_workflow, mock_task_manager):
        """測試工作流程完成檢測"""
        # 創建工作流程實例
        await scheduler.register_workflow(sample_workflow)
        instance_id = await scheduler.start_workflow(sample_workflow.workflow_id)
        
        instance = scheduler.workflow_instances[instance_id]
        instance.status = WorkflowStatus.RUNNING
        instance.task_instances = {
            "task1": "task-001",
            "task2": "task-002",
            "task3": "task-003"
        }
        
        # 模擬所有任務完成
        completed_task = Mock()
        completed_task.status = TaskStatus.COMPLETED
        mock_task_manager.get_task.return_value = completed_task
        
        # 檢查工作流程狀態
        await scheduler._check_workflow_status()
        
        # 工作流程應該被標記為完成
        assert instance.status == WorkflowStatus.COMPLETED
        assert instance.completed_at is not None
    
    async def test_workflow_failure_detection(self, scheduler, sample_workflow, mock_task_manager):
        """測試工作流程失敗檢測"""
        # 創建工作流程實例
        await scheduler.register_workflow(sample_workflow)
        instance_id = await scheduler.start_workflow(sample_workflow.workflow_id)
        
        instance = scheduler.workflow_instances[instance_id]
        instance.status = WorkflowStatus.RUNNING
        instance.task_instances = {"task1": "task-001"}
        
        # 模擬任務失敗
        failed_task = Mock()
        failed_task.status = TaskStatus.FAILED
        mock_task_manager.get_task.return_value = failed_task
        
        # 檢查工作流程狀態
        await scheduler._check_workflow_status()
        
        # 工作流程應該被標記為失敗
        assert instance.status == WorkflowStatus.FAILED
        assert instance.completed_at is not None
    
    async def test_load_balancing(self, scheduler):
        """測試負載均衡"""
        # 添加多個工作節點
        nodes = []
        for i in range(3):
            node = WorkerNode(
                node_id=f"worker-{i:03d}",
                name=f"工作節點 {i+1}",
                capacity={
                    ResourceType.CPU: 400,
                    ResourceType.MEMORY: 4096,
                    ResourceType.NETWORK: 1000,
                    ResourceType.DISK: 500
                }
            )
            nodes.append(node)
            await scheduler.add_worker_node(node)
        
        # 設置不同的負載
        nodes[0].current_load[ResourceType.CPU] = 100  # 25%
        nodes[1].current_load[ResourceType.CPU] = 200  # 50%
        nodes[2].current_load[ResourceType.CPU] = 300  # 75%
        
        # 選擇最佳節點（應該選擇負載最低的）
        requirements = [{"type": "cpu", "amount": 50, "unit": "percent"}]
        best_node = await scheduler._select_best_node(requirements)
        
        assert best_node is not None
        assert best_node.node_id == "worker-000"  # 負載最低的節點
    
    async def test_resource_requirement_filtering(self, scheduler):
        """測試資源需求過濾"""
        # 添加容量有限的節點
        limited_node = WorkerNode(
            node_id="limited-worker",
            name="有限資源節點",
            capacity={
                ResourceType.CPU: 100,  # 只有1核心
                ResourceType.MEMORY: 1024,  # 只有1GB
                ResourceType.NETWORK: 100,
                ResourceType.DISK: 100
            }
        )
        await scheduler.add_worker_node(limited_node)
        
        # 高資源需求
        high_requirements = [
            {"type": "cpu", "amount": 200, "unit": "percent"},  # 需要2核心
            {"type": "memory", "amount": 2048, "unit": "mb"}  # 需要2GB
        ]
        
        # 應該選擇本地節點（資源更充足）
        best_node = await scheduler._select_best_node(high_requirements)
        assert best_node is not None
        assert best_node.node_id == scheduler.local_node_id
        
        # 低資源需求
        low_requirements = [
            {"type": "cpu", "amount": 50, "unit": "percent"},
            {"type": "memory", "amount": 512, "unit": "mb"}
        ]
        
        # 應該能選擇到合適的節點
        best_node = await scheduler._select_best_node(low_requirements)
        assert best_node is not None


async def test_integration_workflow_execution():
    """整合測試：完整工作流程執行"""
    # 創建模擬任務管理器
    mock_task_manager = Mock(spec=TaskManager)
    
    # 模擬任務創建和狀態變化
    task_counter = 0
    created_tasks = {}
    
    async def mock_create_task(request):
        nonlocal task_counter
        task_counter += 1
        task_id = f"task-{task_counter:03d}"
        
        task = Mock()
        task.id = task_id
        task.name = request.name
        task.status = TaskStatus.PENDING
        
        created_tasks[task_id] = task
        return task
    
    async def mock_get_task(task_id):
        return created_tasks.get(task_id)
    
    async def mock_execute_action(task_id, action):
        task = created_tasks.get(task_id)
        if task and action == TaskAction.START:
            task.status = TaskStatus.RUNNING
            # 模擬任務完成
            await asyncio.sleep(0.01)
            task.status = TaskStatus.COMPLETED
    
    mock_task_manager.create_task = mock_create_task
    mock_task_manager.get_task = mock_get_task
    mock_task_manager.execute_task_action = mock_execute_action
    
    # 創建調度器
    with patch('psutil.cpu_count', return_value=4), \
         patch('psutil.virtual_memory') as mock_memory:
        
        mock_memory.return_value.total = 8 * 1024 ** 3
        scheduler = WorkflowScheduler(mock_task_manager)
    
    try:
        # 創建簡單工作流程
        workflow = WorkflowDefinition(
            workflow_id="integration-test",
            name="整合測試工作流程",
            tasks=[
                {
                    "name": "prepare",
                    "type": "preparation",
                    "priority": "high",
                    "resource_requirements": [
                        {"type": "cpu", "amount": 10, "unit": "percent"}
                    ]
                },
                {
                    "name": "process",
                    "type": "processing",
                    "priority": "medium",
                    "resource_requirements": [
                        {"type": "cpu", "amount": 20, "unit": "percent"}
                    ]
                }
            ],
            dependencies={"process": ["prepare"]},
            scheduling_strategy=SchedulingStrategy.DEPENDENCY_AWARE
        )
        
        # 註冊並啟動工作流程
        await scheduler.register_workflow(workflow)
        await scheduler.start()
        
        instance_id = await scheduler.start_workflow(workflow.workflow_id)
        
        # 等待工作流程完成
        max_wait = 50  # 5秒超時
        while max_wait > 0:
            instance = await scheduler.get_workflow_status(instance_id)
            if instance.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED]:
                break
            await asyncio.sleep(0.1)
            max_wait -= 1
        
        # 驗證結果
        final_instance = await scheduler.get_workflow_status(instance_id)
        assert final_instance.status == WorkflowStatus.COMPLETED
        assert len(final_instance.task_instances) == 2
        assert "prepare" in final_instance.task_instances
        assert "process" in final_instance.task_instances
        
        # 檢查調度指標
        metrics = await scheduler.get_scheduling_metrics()
        assert metrics.total_tasks_scheduled >= 0
        
    finally:
        await scheduler.stop()


if __name__ == "__main__":
    """運行測試"""
    import logging
    
    # 設置日誌
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 運行整合測試
    asyncio.run(test_integration_workflow_execution())
    print("工作流程調度器整合測試完成")