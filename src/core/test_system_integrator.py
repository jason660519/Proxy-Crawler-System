#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統整合器測試模組

此模組包含系統整合器的完整測試套件，驗證組件整合、
生命週期管理、事件處理和系統監控等功能。
"""

import asyncio
import pytest
import logging
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .system_integrator import (
    SystemIntegrator, ComponentStatus, IntegrationEvent,
    ComponentInfo, SystemMetrics
)
from ..models.proxy import ProxyModel
from ..proxy_manager.validators.core_validator import ValidationLevel


class TestSystemIntegrator:
    """系統整合器測試類"""
    
    @pytest.fixture
    def mock_config(self) -> Dict[str, Any]:
        """測試配置"""
        return {
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
            'health_check_interval': 1  # 快速測試
        }
    
    @pytest.fixture
    def integrator(self, mock_config) -> SystemIntegrator:
        """創建測試用系統整合器"""
        with patch.multiple(
            'src.core.system_integrator',
            RedisStorageManager=Mock,
            CoreValidator=Mock,
            TaskManager=Mock,
            WorkflowScheduler=Mock
        ):
            return SystemIntegrator(mock_config)
    
    def test_initialization(self, integrator):
        """測試初始化"""
        assert not integrator.is_running
        assert integrator.start_time is None
        assert len(integrator.components) == 4
        assert 'redis_storage' in integrator.components
        assert 'core_validator' in integrator.components
        assert 'task_manager' in integrator.components
        assert 'workflow_scheduler' in integrator.components
    
    def test_component_dependencies(self, integrator):
        """測試組件依賴關係"""
        # 檢查依賴關係設置
        assert integrator.components['core_validator'].dependencies == ['redis_storage']
        assert integrator.components['task_manager'].dependencies == ['redis_storage']
        assert integrator.components['workflow_scheduler'].dependencies == ['task_manager', 'core_validator']
    
    def test_calculate_start_order(self, integrator):
        """測試啟動順序計算"""
        start_order = integrator._calculate_start_order()
        
        # redis_storage 應該最先啟動（無依賴）
        assert start_order[0] == 'redis_storage'
        
        # core_validator 和 task_manager 應該在 redis_storage 之後
        redis_index = start_order.index('redis_storage')
        validator_index = start_order.index('core_validator')
        task_manager_index = start_order.index('task_manager')
        
        assert validator_index > redis_index
        assert task_manager_index > redis_index
        
        # workflow_scheduler 應該最後啟動
        scheduler_index = start_order.index('workflow_scheduler')
        assert scheduler_index > validator_index
        assert scheduler_index > task_manager_index
    
    @pytest.mark.asyncio
    async def test_start_stop_lifecycle(self, integrator):
        """測試啟動停止生命週期"""
        # 模擬組件方法
        for component in integrator.components.values():
            component.instance.start = AsyncMock()
            component.instance.stop = AsyncMock()
            component.instance.health_check = AsyncMock(return_value=True)
        
        # 測試啟動
        await integrator.start()
        assert integrator.is_running
        assert integrator.start_time is not None
        
        # 檢查所有組件都已啟動
        for component in integrator.components.values():
            assert component.status == ComponentStatus.ACTIVE
            component.instance.start.assert_called_once()
        
        # 測試停止
        await integrator.stop()
        assert not integrator.is_running
        
        # 檢查所有組件都已停止
        for component in integrator.components.values():
            component.instance.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_component_error_handling(self, integrator):
        """測試組件錯誤處理"""
        # 模擬組件啟動失敗
        redis_component = integrator.components['redis_storage']
        redis_component.instance.start = AsyncMock(side_effect=Exception("連接失敗"))
        
        # 其他組件正常
        for name, component in integrator.components.items():
            if name != 'redis_storage':
                component.instance.start = AsyncMock()
                component.instance.stop = AsyncMock()
        
        # 啟動應該失敗
        with pytest.raises(Exception):
            await integrator.start()
        
        # 檢查錯誤狀態
        assert redis_component.status == ComponentStatus.ERROR
        assert redis_component.error_count == 1
        assert "連接失敗" in redis_component.last_error
    
    @pytest.mark.asyncio
    async def test_health_check(self, integrator):
        """測試健康檢查"""
        # 模擬組件
        for component in integrator.components.values():
            component.instance.start = AsyncMock()
            component.instance.stop = AsyncMock()
            component.instance.health_check = AsyncMock(return_value=True)
            component.instance.get_statistics = AsyncMock(return_value={
                'total': 100, 'completed': 80, 'failed': 5
            })
            component.instance.get_proxy_count = AsyncMock(return_value=50)
        
        await integrator.start()
        
        # 執行健康檢查
        await integrator._perform_health_check()
        
        # 檢查健康檢查時間更新
        for component in integrator.components.values():
            assert component.last_health_check is not None
        
        # 檢查系統指標更新
        assert integrator.metrics.total_components == 4
        assert integrator.metrics.active_components == 4
        assert integrator.metrics.error_components == 0
        
        await integrator.stop()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, integrator):
        """測試健康檢查失敗處理"""
        # 模擬組件
        for component in integrator.components.values():
            component.instance.start = AsyncMock()
            component.instance.stop = AsyncMock()
        
        # 模擬一個組件健康檢查失敗
        redis_component = integrator.components['redis_storage']
        redis_component.instance.health_check = AsyncMock(return_value=False)
        
        # 其他組件正常
        for name, component in integrator.components.items():
            if name != 'redis_storage':
                component.instance.health_check = AsyncMock(return_value=True)
        
        await integrator.start()
        
        # 執行健康檢查
        await integrator._perform_health_check()
        
        # 檢查失敗組件狀態
        assert redis_component.status == ComponentStatus.ERROR
        assert redis_component.error_count == 1
        assert "健康檢查失敗" in redis_component.last_error
        
        await integrator.stop()
    
    def test_event_handling(self, integrator):
        """測試事件處理"""
        # 添加事件處理器
        handler_called = False
        event_data = None
        
        def test_handler(event, data):
            nonlocal handler_called, event_data
            handler_called = True
            event_data = data
        
        integrator.add_event_handler(IntegrationEvent.COMPONENT_STARTED, test_handler)
        
        # 觸發事件
        asyncio.run(integrator._emit_event(IntegrationEvent.COMPONENT_STARTED, {'test': 'data'}))
        
        # 檢查處理器被調用
        assert handler_called
        assert event_data == {'test': 'data'}
        
        # 測試移除處理器
        integrator.remove_event_handler(IntegrationEvent.COMPONENT_STARTED, test_handler)
        
        handler_called = False
        asyncio.run(integrator._emit_event(IntegrationEvent.COMPONENT_STARTED, {'test': 'data2'}))
        assert not handler_called
    
    @pytest.mark.asyncio
    async def test_async_event_handling(self, integrator):
        """測試異步事件處理"""
        # 添加異步事件處理器
        handler_called = False
        
        async def async_handler(event, data):
            nonlocal handler_called
            await asyncio.sleep(0.01)  # 模擬異步操作
            handler_called = True
        
        integrator.add_event_handler(IntegrationEvent.COMPONENT_STARTED, async_handler)
        
        # 觸發事件
        await integrator._emit_event(IntegrationEvent.COMPONENT_STARTED, {'test': 'data'})
        
        # 檢查處理器被調用
        assert handler_called
    
    def test_component_access(self, integrator):
        """測試組件訪問"""
        # 測試獲取組件
        redis_instance = integrator.get_component('redis_storage')
        assert redis_instance is not None
        
        # 測試獲取不存在的組件
        non_existent = integrator.get_component('non_existent')
        assert non_existent is None
        
        # 測試獲取組件狀態
        status = integrator.get_component_status('redis_storage')
        assert status == ComponentStatus.INACTIVE
        
        # 測試獲取不存在組件的狀態
        non_existent_status = integrator.get_component_status('non_existent')
        assert non_existent_status is None
    
    def test_system_status(self, integrator):
        """測試系統狀態獲取"""
        status = integrator.get_system_status()
        
        assert 'is_running' in status
        assert 'start_time' in status
        assert 'components' in status
        assert 'metrics' in status
        
        # 檢查組件狀態
        assert len(status['components']) == 4
        for component_name in ['redis_storage', 'core_validator', 'task_manager', 'workflow_scheduler']:
            assert component_name in status['components']
            component_status = status['components'][component_name]
            assert 'status' in component_status
            assert 'error_count' in component_status
            assert 'last_error' in component_status
            assert 'last_health_check' in component_status
    
    @pytest.mark.asyncio
    async def test_validate_proxies_integration(self, integrator):
        """測試代理驗證整合"""
        # 模擬核心驗證器
        mock_validator = Mock()
        mock_validator.validate_proxies = AsyncMock(return_value=[
            {'proxy': 'test1', 'valid': True, 'score': 0.9},
            {'proxy': 'test2', 'valid': False, 'score': 0.1}
        ])
        
        integrator.components['core_validator'].instance = mock_validator
        integrator.components['core_validator'].status = ComponentStatus.ACTIVE
        
        # 測試代理
        test_proxies = [
            ProxyModel(host='127.0.0.1', port=8080, protocol='http'),
            ProxyModel(host='127.0.0.1', port=8081, protocol='http')
        ]
        
        # 執行驗證
        results = await integrator.validate_proxies(test_proxies)
        
        # 檢查結果
        assert len(results) == 2
        mock_validator.validate_proxies.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_proxies_no_validator(self, integrator):
        """測試無驗證器時的錯誤處理"""
        # 移除驗證器
        del integrator.components['core_validator']
        
        test_proxies = [ProxyModel(host='127.0.0.1', port=8080, protocol='http')]
        
        # 應該拋出錯誤
        with pytest.raises(RuntimeError, match="核心驗證器未初始化"):
            await integrator.validate_proxies(test_proxies)
    
    @pytest.mark.asyncio
    async def test_create_workflow_integration(self, integrator):
        """測試工作流程創建整合"""
        # 模擬工作流程調度器
        mock_scheduler = Mock()
        mock_scheduler.create_workflow = AsyncMock(return_value='workflow_123')
        
        integrator.components['workflow_scheduler'].instance = mock_scheduler
        integrator.components['workflow_scheduler'].status = ComponentStatus.ACTIVE
        
        # 創建工作流程
        workflow_config = {'name': 'test_workflow', 'tasks': []}
        workflow_id = await integrator.create_workflow(workflow_config)
        
        # 檢查結果
        assert workflow_id == 'workflow_123'
        mock_scheduler.create_workflow.assert_called_once_with(workflow_config)
    
    @pytest.mark.asyncio
    async def test_store_proxy_integration(self, integrator):
        """測試代理存儲整合"""
        # 模擬存儲管理器
        mock_storage = Mock()
        mock_storage.save_proxy = AsyncMock(return_value=True)
        
        integrator.components['redis_storage'].instance = mock_storage
        integrator.components['redis_storage'].status = ComponentStatus.ACTIVE
        
        # 存儲代理
        test_proxy = ProxyModel(host='127.0.0.1', port=8080, protocol='http')
        success = await integrator.store_proxy(test_proxy)
        
        # 檢查結果
        assert success is True
        mock_storage.save_proxy.assert_called_once_with(test_proxy)
    
    @pytest.mark.asyncio
    async def test_managed_lifecycle_context(self, integrator):
        """測試管理生命週期上下文管理器"""
        # 模擬組件方法
        for component in integrator.components.values():
            component.instance.start = AsyncMock()
            component.instance.stop = AsyncMock()
            component.instance.health_check = AsyncMock(return_value=True)
        
        # 使用上下文管理器
        async with integrator.managed_lifecycle() as managed_integrator:
            assert managed_integrator.is_running
            assert managed_integrator is integrator
        
        # 檢查自動停止
        assert not integrator.is_running
    
    @pytest.mark.asyncio
    async def test_managed_lifecycle_exception_handling(self, integrator):
        """測試管理生命週期異常處理"""
        # 模擬組件方法
        for component in integrator.components.values():
            component.instance.start = AsyncMock()
            component.instance.stop = AsyncMock()
            component.instance.health_check = AsyncMock(return_value=True)
        
        # 在上下文中拋出異常
        with pytest.raises(ValueError):
            async with integrator.managed_lifecycle():
                raise ValueError("測試異常")
        
        # 檢查仍然正確停止
        assert not integrator.is_running


@pytest.mark.asyncio
async def test_integration_workflow_execution():
    """整合測試：完整工作流程執行"""
    config = {
        'redis': {'host': 'localhost', 'port': 6379, 'db': 0},
        'validator': {'level': 'STANDARD', 'max_workers': 5},
        'task_manager': {'max_workers': 3},
        'workflow_scheduler': {'strategy': 'ROUND_ROBIN'},
        'health_check_interval': 0.5
    }
    
    with patch.multiple(
        'src.core.system_integrator',
        RedisStorageManager=Mock,
        CoreValidator=Mock,
        TaskManager=Mock,
        WorkflowScheduler=Mock
    ):
        integrator = SystemIntegrator(config)
        
        # 模擬所有組件方法
        for component in integrator.components.values():
            component.instance.start = AsyncMock()
            component.instance.stop = AsyncMock()
            component.instance.health_check = AsyncMock(return_value=True)
            component.instance.get_statistics = AsyncMock(return_value={
                'total': 10, 'completed': 8, 'failed': 1
            })
            component.instance.get_proxy_count = AsyncMock(return_value=25)
        
        # 模擬特定功能
        validator = integrator.components['core_validator'].instance
        validator.validate_proxies = AsyncMock(return_value=[
            {'proxy': 'test', 'valid': True, 'score': 0.95}
        ])
        
        scheduler = integrator.components['workflow_scheduler'].instance
        scheduler.create_workflow = AsyncMock(return_value='workflow_test')
        
        storage = integrator.components['redis_storage'].instance
        storage.save_proxy = AsyncMock(return_value=True)
        
        # 執行完整工作流程
        async with integrator.managed_lifecycle():
            # 1. 驗證代理
            test_proxies = [ProxyModel(host='127.0.0.1', port=8080, protocol='http')]
            validation_results = await integrator.validate_proxies(test_proxies)
            assert len(validation_results) == 1
            
            # 2. 創建工作流程
            workflow_id = await integrator.create_workflow({'name': 'test'})
            assert workflow_id == 'workflow_test'
            
            # 3. 存儲代理
            success = await integrator.store_proxy(test_proxies[0])
            assert success is True
            
            # 4. 檢查系統狀態
            status = integrator.get_system_status()
            assert status['is_running'] is True
            assert status['metrics']['active_components'] == 4
            
            # 5. 等待健康檢查執行
            await asyncio.sleep(1)
            
            # 檢查健康檢查執行
            for component in integrator.components.values():
                assert component.last_health_check is not None


# 測試主函數
async def main():
    """執行所有測試"""
    logging.basicConfig(level=logging.INFO)
    
    print("開始系統整合器測試...")
    
    # 運行 pytest
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, '-m', 'pytest', __file__, '-v'
    ], capture_output=True, text=True)
    
    print("測試輸出:")
    print(result.stdout)
    if result.stderr:
        print("錯誤輸出:")
        print(result.stderr)
    
    print(f"測試結果: {'通過' if result.returncode == 0 else '失敗'}")
    
    return result.returncode == 0


if __name__ == "__main__":
    asyncio.run(main())