"""核心模組

此模組包含系統的核心功能組件，包括：
- 任務管理器：負責任務的創建、調度和執行
- 工作流程調度器：負責智能任務分配和負載均衡
- 系統整合器：負責組件整合和生命週期管理
- 分析引擎：負責數據分析和報告生成
- 日誌系統：負責系統日誌記錄和管理
- 基礎類：提供通用的基礎功能
"""

from .base import (
    TaskStatus, TaskPriority, ProxyStatus, AnonymityLevel,
    ValidationResult, ProxyInfo, TaskConfig
)
from .config import Config, get_config
from .logger import setup_logger, get_logger
from .task_manager import TaskManager, TaskType, TaskAction
from .tasks import Task, TaskCreateRequest, TaskUpdateRequest, TaskStatistics
from .workflow_scheduler import (
    WorkflowScheduler, WorkflowDefinition, WorkflowInstance, WorkerNode,
    WorkflowStatus, SchedulingStrategy, ResourceType, ResourceRequirement,
    SchedulingMetrics
)
from .system_integrator import (
    SystemIntegrator, ComponentStatus, IntegrationEvent,
    ComponentInfo, SystemMetrics
)

__all__ = [
    # 基礎模型
    "TaskStatus", "TaskPriority", "ProxyStatus", "AnonymityLevel",
    "ValidationResult", "ProxyInfo", "TaskConfig",
    
    # 配置管理
    "Config", "get_config",
    
    # 日誌系統
    "setup_logger", "get_logger",
    
    # 任務管理
    "TaskManager", "TaskType", "TaskAction",
    "Task", "TaskCreateRequest", "TaskUpdateRequest", "TaskStatistics",
    
    # 工作流程調度器
    "WorkflowScheduler", "WorkflowDefinition", "WorkflowInstance", "WorkerNode",
    "WorkflowStatus", "SchedulingStrategy", "ResourceType", "ResourceRequirement",
    "SchedulingMetrics",
    
    # 系統整合
    "SystemIntegrator", "ComponentStatus", "IntegrationEvent",
    "ComponentInfo", "SystemMetrics"
]

__version__ = "1.0.0"
__author__ = "Jason"