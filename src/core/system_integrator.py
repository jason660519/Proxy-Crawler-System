#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統整合器模組

此模組負責整合所有核心組件，提供統一的接口和協作機制。
主要功能包括：
- 組件生命週期管理
- 組件間通信協調
- 統一配置管理
- 系統狀態監控
- 錯誤處理和恢復
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import traceback
from contextlib import asynccontextmanager

# 導入核心組件
from .task_manager import TaskManager, TaskType, TaskAction
from .workflow_scheduler import WorkflowScheduler, WorkflowStatus, SchedulingStrategy
from ..proxy_manager.storage.redis_storage_manager import RedisStorageManager
from ..proxy_manager.validators.core_validator import CoreValidator, ValidationLevel
from ..models.proxy import ProxyModel
from ..models.task import TaskModel


class ComponentStatus(Enum):
    """組件狀態枚舉"""
    INACTIVE = "inactive"  # 未啟動
    STARTING = "starting"  # 啟動中
    ACTIVE = "active"      # 運行中
    STOPPING = "stopping"  # 停止中
    ERROR = "error"        # 錯誤狀態
    MAINTENANCE = "maintenance"  # 維護模式


class IntegrationEvent(Enum):
    """整合事件類型"""
    COMPONENT_STARTED = "component_started"
    COMPONENT_STOPPED = "component_stopped"
    COMPONENT_ERROR = "component_error"
    VALIDATION_COMPLETED = "validation_completed"
    WORKFLOW_UPDATED = "workflow_updated"
    STORAGE_UPDATED = "storage_updated"
    SYSTEM_HEALTH_CHECK = "system_health_check"


@dataclass
class ComponentInfo:
    """組件資訊"""
    name: str
    instance: Any
    status: ComponentStatus = ComponentStatus.INACTIVE
    last_health_check: Optional[datetime] = None
    error_count: int = 0
    last_error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """系統指標"""
    total_components: int = 0
    active_components: int = 0
    error_components: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_proxies: int = 0
    valid_proxies: int = 0
    system_uptime: timedelta = field(default_factory=lambda: timedelta())
    last_updated: datetime = field(default_factory=datetime.now)


class SystemIntegrator:
    """系統整合器
    
    負責管理和協調所有核心組件的運行，提供統一的系統接口。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化系統整合器
        
        Args:
            config: 系統配置字典
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 組件管理
        self.components: Dict[str, ComponentInfo] = {}
        self.event_handlers: Dict[IntegrationEvent, List[Callable]] = {
            event: [] for event in IntegrationEvent
        }
        
        # 系統狀態
        self.is_running = False
        self.start_time: Optional[datetime] = None
        self.metrics = SystemMetrics()
        
        # 健康檢查
        self.health_check_interval = self.config.get('health_check_interval', 30)
        self.health_check_task: Optional[asyncio.Task] = None
        
        # 初始化組件
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """初始化所有核心組件"""
        try:
            # Redis存儲管理器
            redis_config = self.config.get('redis', {})
            redis_manager = RedisStorageManager(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password'),
                max_connections=redis_config.get('max_connections', 20)
            )
            
            self.components['redis_storage'] = ComponentInfo(
                name='redis_storage',
                instance=redis_manager,
                config=redis_config
            )
            
            # 核心驗證器
            validator_config = self.config.get('validator', {})
            core_validator = CoreValidator(
                validation_level=ValidationLevel(validator_config.get('level', 'STANDARD')),
                max_workers=validator_config.get('max_workers', 10),
                timeout=validator_config.get('timeout', 30)
            )
            
            self.components['core_validator'] = ComponentInfo(
                name='core_validator',
                instance=core_validator,
                config=validator_config,
                dependencies=['redis_storage']
            )
            
            # 任務管理器
            task_config = self.config.get('task_manager', {})
            task_manager = TaskManager(
                redis_url=f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}",
                max_workers=task_config.get('max_workers', 5)
            )
            
            self.components['task_manager'] = ComponentInfo(
                name='task_manager',
                instance=task_manager,
                config=task_config,
                dependencies=['redis_storage']
            )
            
            # 工作流程調度器
            scheduler_config = self.config.get('workflow_scheduler', {})
            workflow_scheduler = WorkflowScheduler(
                strategy=SchedulingStrategy(scheduler_config.get('strategy', 'ROUND_ROBIN')),
                max_concurrent_workflows=scheduler_config.get('max_concurrent', 10)
            )
            
            self.components['workflow_scheduler'] = ComponentInfo(
                name='workflow_scheduler',
                instance=workflow_scheduler,
                config=scheduler_config,
                dependencies=['task_manager', 'core_validator']
            )
            
            self.logger.info(f"已初始化 {len(self.components)} 個核心組件")
            
        except Exception as e:
            self.logger.error(f"組件初始化失敗: {e}")
            raise
    
    async def start(self) -> None:
        """啟動系統整合器"""
        if self.is_running:
            self.logger.warning("系統整合器已在運行中")
            return
        
        try:
            self.logger.info("正在啟動系統整合器...")
            self.start_time = datetime.now()
            
            # 按依賴順序啟動組件
            await self._start_components_in_order()
            
            # 啟動健康檢查
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.is_running = True
            await self._emit_event(IntegrationEvent.COMPONENT_STARTED, {'component': 'system_integrator'})
            
            self.logger.info("系統整合器啟動完成")
            
        except Exception as e:
            self.logger.error(f"系統整合器啟動失敗: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """停止系統整合器"""
        if not self.is_running:
            return
        
        try:
            self.logger.info("正在停止系統整合器...")
            
            # 停止健康檢查
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # 按反向依賴順序停止組件
            await self._stop_components_in_reverse_order()
            
            self.is_running = False
            await self._emit_event(IntegrationEvent.COMPONENT_STOPPED, {'component': 'system_integrator'})
            
            self.logger.info("系統整合器已停止")
            
        except Exception as e:
            self.logger.error(f"系統整合器停止時發生錯誤: {e}")
    
    async def _start_components_in_order(self) -> None:
        """按依賴順序啟動組件"""
        # 計算啟動順序
        start_order = self._calculate_start_order()
        
        for component_name in start_order:
            component = self.components[component_name]
            try:
                self.logger.info(f"正在啟動組件: {component_name}")
                component.status = ComponentStatus.STARTING
                
                # 啟動組件
                if hasattr(component.instance, 'start'):
                    await component.instance.start()
                elif hasattr(component.instance, '__aenter__'):
                    await component.instance.__aenter__()
                
                component.status = ComponentStatus.ACTIVE
                component.last_health_check = datetime.now()
                
                await self._emit_event(IntegrationEvent.COMPONENT_STARTED, {
                    'component': component_name
                })
                
                self.logger.info(f"組件 {component_name} 啟動成功")
                
            except Exception as e:
                component.status = ComponentStatus.ERROR
                component.error_count += 1
                component.last_error = str(e)
                
                self.logger.error(f"組件 {component_name} 啟動失敗: {e}")
                await self._emit_event(IntegrationEvent.COMPONENT_ERROR, {
                    'component': component_name,
                    'error': str(e)
                })
                raise
    
    async def _stop_components_in_reverse_order(self) -> None:
        """按反向依賴順序停止組件"""
        start_order = self._calculate_start_order()
        stop_order = list(reversed(start_order))
        
        for component_name in stop_order:
            component = self.components[component_name]
            if component.status != ComponentStatus.ACTIVE:
                continue
            
            try:
                self.logger.info(f"正在停止組件: {component_name}")
                component.status = ComponentStatus.STOPPING
                
                # 停止組件
                if hasattr(component.instance, 'stop'):
                    await component.instance.stop()
                elif hasattr(component.instance, '__aexit__'):
                    await component.instance.__aexit__(None, None, None)
                
                component.status = ComponentStatus.INACTIVE
                
                await self._emit_event(IntegrationEvent.COMPONENT_STOPPED, {
                    'component': component_name
                })
                
                self.logger.info(f"組件 {component_name} 停止成功")
                
            except Exception as e:
                component.status = ComponentStatus.ERROR
                component.error_count += 1
                component.last_error = str(e)
                
                self.logger.error(f"組件 {component_name} 停止失敗: {e}")
    
    def _calculate_start_order(self) -> List[str]:
        """計算組件啟動順序（拓撲排序）"""
        # 簡單的拓撲排序實現
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(component_name: str):
            if component_name in temp_visited:
                raise ValueError(f"檢測到循環依賴: {component_name}")
            if component_name in visited:
                return
            
            temp_visited.add(component_name)
            
            component = self.components[component_name]
            for dep in component.dependencies:
                if dep in self.components:
                    visit(dep)
            
            temp_visited.remove(component_name)
            visited.add(component_name)
            result.append(component_name)
        
        for component_name in self.components:
            if component_name not in visited:
                visit(component_name)
        
        return result
    
    async def _health_check_loop(self) -> None:
        """健康檢查循環"""
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"健康檢查失敗: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def _perform_health_check(self) -> None:
        """執行健康檢查"""
        for component_name, component in self.components.items():
            try:
                # 檢查組件健康狀態
                if hasattr(component.instance, 'health_check'):
                    is_healthy = await component.instance.health_check()
                    if not is_healthy and component.status == ComponentStatus.ACTIVE:
                        component.status = ComponentStatus.ERROR
                        component.error_count += 1
                        component.last_error = "健康檢查失敗"
                        
                        await self._emit_event(IntegrationEvent.COMPONENT_ERROR, {
                            'component': component_name,
                            'error': '健康檢查失敗'
                        })
                
                component.last_health_check = datetime.now()
                
            except Exception as e:
                self.logger.error(f"組件 {component_name} 健康檢查異常: {e}")
                component.status = ComponentStatus.ERROR
                component.error_count += 1
                component.last_error = str(e)
        
        # 更新系統指標
        await self._update_system_metrics()
        
        await self._emit_event(IntegrationEvent.SYSTEM_HEALTH_CHECK, {
            'metrics': self.metrics
        })
    
    async def _update_system_metrics(self) -> None:
        """更新系統指標"""
        self.metrics.total_components = len(self.components)
        self.metrics.active_components = sum(
            1 for comp in self.components.values() 
            if comp.status == ComponentStatus.ACTIVE
        )
        self.metrics.error_components = sum(
            1 for comp in self.components.values() 
            if comp.status == ComponentStatus.ERROR
        )
        
        # 獲取任務統計
        if 'task_manager' in self.components:
            task_manager = self.components['task_manager'].instance
            if hasattr(task_manager, 'get_statistics'):
                task_stats = await task_manager.get_statistics()
                self.metrics.total_tasks = task_stats.get('total', 0)
                self.metrics.completed_tasks = task_stats.get('completed', 0)
                self.metrics.failed_tasks = task_stats.get('failed', 0)
        
        # 獲取代理統計
        if 'redis_storage' in self.components:
            storage = self.components['redis_storage'].instance
            if hasattr(storage, 'get_proxy_count'):
                self.metrics.total_proxies = await storage.get_proxy_count()
                self.metrics.valid_proxies = await storage.get_proxy_count(status='active')
        
        # 計算系統運行時間
        if self.start_time:
            self.metrics.system_uptime = datetime.now() - self.start_time
        
        self.metrics.last_updated = datetime.now()
    
    async def _emit_event(self, event: IntegrationEvent, data: Dict[str, Any]) -> None:
        """發送系統事件"""
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, data)
                else:
                    handler(event, data)
            except Exception as e:
                self.logger.error(f"事件處理器執行失敗: {e}")
    
    def add_event_handler(self, event: IntegrationEvent, handler: Callable) -> None:
        """添加事件處理器"""
        self.event_handlers[event].append(handler)
    
    def remove_event_handler(self, event: IntegrationEvent, handler: Callable) -> None:
        """移除事件處理器"""
        if handler in self.event_handlers[event]:
            self.event_handlers[event].remove(handler)
    
    def get_component(self, name: str) -> Optional[Any]:
        """獲取組件實例"""
        component = self.components.get(name)
        return component.instance if component else None
    
    def get_component_status(self, name: str) -> Optional[ComponentStatus]:
        """獲取組件狀態"""
        component = self.components.get(name)
        return component.status if component else None
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'is_running': self.is_running,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'components': {
                name: {
                    'status': comp.status.value,
                    'error_count': comp.error_count,
                    'last_error': comp.last_error,
                    'last_health_check': comp.last_health_check.isoformat() if comp.last_health_check else None
                }
                for name, comp in self.components.items()
            },
            'metrics': {
                'total_components': self.metrics.total_components,
                'active_components': self.metrics.active_components,
                'error_components': self.metrics.error_components,
                'total_tasks': self.metrics.total_tasks,
                'completed_tasks': self.metrics.completed_tasks,
                'failed_tasks': self.metrics.failed_tasks,
                'total_proxies': self.metrics.total_proxies,
                'valid_proxies': self.metrics.valid_proxies,
                'system_uptime': str(self.metrics.system_uptime),
                'last_updated': self.metrics.last_updated.isoformat()
            }
        }
    
    async def validate_proxies(self, proxies: List[ProxyModel], 
                             validation_level: Optional[ValidationLevel] = None) -> List[Dict[str, Any]]:
        """驗證代理列表"""
        validator = self.get_component('core_validator')
        if not validator:
            raise RuntimeError("核心驗證器未初始化")
        
        results = await validator.validate_proxies(
            proxies, 
            validation_level or ValidationLevel.STANDARD
        )
        
        await self._emit_event(IntegrationEvent.VALIDATION_COMPLETED, {
            'proxy_count': len(proxies),
            'results': results
        })
        
        return results
    
    async def create_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """創建工作流程"""
        scheduler = self.get_component('workflow_scheduler')
        if not scheduler:
            raise RuntimeError("工作流程調度器未初始化")
        
        workflow_id = await scheduler.create_workflow(workflow_config)
        
        await self._emit_event(IntegrationEvent.WORKFLOW_UPDATED, {
            'workflow_id': workflow_id,
            'action': 'created'
        })
        
        return workflow_id
    
    async def store_proxy(self, proxy: ProxyModel) -> bool:
        """存儲代理"""
        storage = self.get_component('redis_storage')
        if not storage:
            raise RuntimeError("Redis存儲管理器未初始化")
        
        success = await storage.save_proxy(proxy)
        
        if success:
            await self._emit_event(IntegrationEvent.STORAGE_UPDATED, {
                'action': 'proxy_stored',
                'proxy_id': proxy.id
            })
        
        return success
    
    @asynccontextmanager
    async def managed_lifecycle(self):
        """管理系統生命週期的上下文管理器"""
        try:
            await self.start()
            yield self
        finally:
            await self.stop()


# 測試函數
async def main():
    """測試系統整合器"""
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'max_connections': 20
        },
        'validator': {
            'level': 'STANDARD',
            'max_workers': 10,
            'timeout': 30
        },
        'task_manager': {
            'max_workers': 5
        },
        'workflow_scheduler': {
            'strategy': 'ROUND_ROBIN',
            'max_concurrent': 10
        },
        'health_check_interval': 30
    }
    
    async with SystemIntegrator(config).managed_lifecycle() as integrator:
        print("系統整合器測試開始")
        
        # 測試系統狀態
        status = integrator.get_system_status()
        print(f"系統狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 等待一段時間觀察健康檢查
        await asyncio.sleep(5)
        
        print("系統整合器測試完成")


if __name__ == "__main__":
    asyncio.run(main())