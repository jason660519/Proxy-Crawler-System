#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合測試模組

此模組提供完整的系統整合測試，驗證各組件間的協作和整體系統功能。
包括端到端測試、性能測試和壓力測試。
"""

import asyncio
import pytest
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# 導入系統組件
from src.core.system_integrator import (
    SystemIntegrator, ComponentStatus, ComponentInfo
)
from src.core.redis_storage_manager import RedisStorageManager
from src.core.core_validator import CoreValidator
from src.core.task_manager import TaskManager
from src.api.unified_api import UnifiedAPI
from src.monitoring.system_monitor import SystemMonitor
from src.monitoring.logger import EnhancedLogger, LogLevel
from src.models.proxy import ProxyInfo, ProxyStatus
from src.models.task import Task, TaskStatus, TaskType


class TestSystemIntegration:
    """系統整合測試類"""
    
    @pytest.fixture
    async def system_integrator(self):
        """創建系統整合器測試夾具"""
        integrator = SystemIntegrator()
        yield integrator
        await integrator.shutdown()
    
    @pytest.fixture
    async def mock_redis_manager(self):
        """創建模擬Redis管理器"""
        manager = AsyncMock(spec=RedisStorageManager)
        manager.is_connected.return_value = True
        manager.get_proxy_count.return_value = 100
        manager.get_active_proxy_count.return_value = 80
        return manager
    
    @pytest.fixture
    async def mock_validator(self):
        """創建模擬驗證器"""
        validator = AsyncMock(spec=CoreValidator)
        validator.validate_proxy.return_value = {
            'is_valid': True,
            'response_time': 0.5,
            'quality_score': 0.85
        }
        return validator
    
    @pytest.fixture
    async def mock_task_manager(self):
        """創建模擬任務管理器"""
        manager = AsyncMock(spec=TaskManager)
        manager.get_queue_size.return_value = 10
        manager.get_active_task_count.return_value = 5
        return manager
    
    @pytest.fixture
    async def mock_api(self):
        """創建模擬API"""
        api = AsyncMock(spec=UnifiedAPI)
        api.is_running = True
        return api
    
    @pytest.fixture
    async def mock_monitor(self):
        """創建模擬監控器"""
        monitor = AsyncMock(spec=SystemMonitor)
        monitor.is_running = True
        monitor.get_system_health.return_value = {
            'status': 'healthy',
            'cpu_usage': 45.2,
            'memory_usage': 62.1
        }
        return monitor
    
    async def test_full_system_startup(self, system_integrator, 
                                     mock_redis_manager, mock_validator,
                                     mock_task_manager, mock_api, mock_monitor):
        """測試完整系統啟動流程"""
        # 註冊所有組件
        await system_integrator.register_component(
            "redis_manager", mock_redis_manager, []
        )
        await system_integrator.register_component(
            "validator", mock_validator, ["redis_manager"]
        )
        await system_integrator.register_component(
            "task_manager", mock_task_manager, ["redis_manager"]
        )
        await system_integrator.register_component(
            "api", mock_api, ["redis_manager", "validator", "task_manager"]
        )
        await system_integrator.register_component(
            "monitor", mock_monitor, []
        )
        
        # 啟動系統
        await system_integrator.start_all()
        
        # 驗證所有組件都已啟動
        status = await system_integrator.get_system_status()
        assert status['status'] == 'running'
        assert len(status['components']) == 5
        
        for component in status['components'].values():
            assert component['status'] == ComponentStatus.RUNNING
    
    async def test_component_failure_recovery(self, system_integrator,
                                            mock_redis_manager, mock_validator):
        """測試組件故障恢復"""
        # 註冊組件
        await system_integrator.register_component(
            "redis_manager", mock_redis_manager, []
        )
        await system_integrator.register_component(
            "validator", mock_validator, ["redis_manager"]
        )
        
        # 啟動系統
        await system_integrator.start_all()
        
        # 模擬Redis管理器故障
        mock_redis_manager.is_connected.return_value = False
        
        # 檢查健康狀態
        health = await system_integrator.check_component_health("redis_manager")
        assert not health
        
        # 模擬恢復
        mock_redis_manager.is_connected.return_value = True
        
        # 重新檢查健康狀態
        health = await system_integrator.check_component_health("redis_manager")
        assert health
    
    async def test_event_propagation(self, system_integrator,
                                   mock_redis_manager, mock_validator):
        """測試事件傳播機制"""
        events_received = []
        
        def event_handler(event):
            events_received.append(event)
        
        # 註冊事件處理器
        system_integrator.add_event_handler(event_handler)
        
        # 註冊組件
        await system_integrator.register_component(
            "redis_manager", mock_redis_manager, []
        )
        
        # 啟動組件
        await system_integrator.start_component("redis_manager")
        
        # 驗證事件被觸發
        assert len(events_received) >= 2  # COMPONENT_REGISTERED 和 COMPONENT_STARTED
        
        event_types = [event.event_type for event in events_received]
        assert "COMPONENT_REGISTERED" in event_types
        assert "COMPONENT_STARTED" in event_types


class TestEndToEndWorkflow:
    """端到端工作流程測試類"""
    
    @pytest.fixture
    async def full_system(self):
        """創建完整系統測試夾具"""
        # 創建臨時目錄
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 創建系統組件（使用模擬實現）
            redis_manager = AsyncMock(spec=RedisStorageManager)
            validator = AsyncMock(spec=CoreValidator)
            task_manager = AsyncMock(spec=TaskManager)
            api = AsyncMock(spec=UnifiedAPI)
            monitor = AsyncMock(spec=SystemMonitor)
            
            # 設置模擬行為
            redis_manager.is_connected.return_value = True
            redis_manager.save_proxy.return_value = True
            redis_manager.get_proxy.return_value = ProxyInfo(
                host="127.0.0.1",
                port=8080,
                protocol="http",
                status=ProxyStatus.ACTIVE
            )
            
            validator.validate_proxy.return_value = {
                'is_valid': True,
                'response_time': 0.5,
                'quality_score': 0.85
            }
            
            task_manager.submit_task.return_value = "task_123"
            task_manager.get_task_status.return_value = TaskStatus.COMPLETED
            
            # 創建系統整合器
            integrator = SystemIntegrator()
            
            # 註冊組件
            await integrator.register_component("redis_manager", redis_manager, [])
            await integrator.register_component("validator", validator, ["redis_manager"])
            await integrator.register_component("task_manager", task_manager, ["redis_manager"])
            await integrator.register_component("api", api, ["redis_manager", "validator", "task_manager"])
            await integrator.register_component("monitor", monitor, [])
            
            # 啟動系統
            await integrator.start_all()
            
            yield {
                'integrator': integrator,
                'redis_manager': redis_manager,
                'validator': validator,
                'task_manager': task_manager,
                'api': api,
                'monitor': monitor,
                'temp_dir': temp_dir
            }
            
        finally:
            # 清理
            await integrator.shutdown()
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def test_proxy_validation_workflow(self, full_system):
        """測試代理驗證工作流程"""
        components = full_system
        integrator = components['integrator']
        redis_manager = components['redis_manager']
        validator = components['validator']
        task_manager = components['task_manager']
        
        # 模擬代理驗證工作流程
        proxy_info = ProxyInfo(
            host="192.168.1.100",
            port=3128,
            protocol="http",
            status=ProxyStatus.PENDING
        )
        
        # 1. 保存代理到Redis
        await redis_manager.save_proxy(proxy_info)
        redis_manager.save_proxy.assert_called_once_with(proxy_info)
        
        # 2. 提交驗證任務
        task_id = await task_manager.submit_task(
            Task(
                task_type=TaskType.PROXY_VALIDATION,
                data={'proxy': proxy_info.to_dict()}
            )
        )
        assert task_id == "task_123"
        
        # 3. 執行驗證
        validation_result = await validator.validate_proxy(proxy_info)
        assert validation_result['is_valid'] is True
        assert validation_result['quality_score'] > 0.8
        
        # 4. 檢查任務狀態
        status = await task_manager.get_task_status(task_id)
        assert status == TaskStatus.COMPLETED
        
        # 驗證系統狀態
        system_status = await integrator.get_system_status()
        assert system_status['status'] == 'running'
    
    async def test_batch_proxy_processing(self, full_system):
        """測試批量代理處理"""
        components = full_system
        redis_manager = components['redis_manager']
        validator = components['validator']
        task_manager = components['task_manager']
        
        # 創建批量代理
        proxies = [
            ProxyInfo(host=f"192.168.1.{i}", port=3128, protocol="http")
            for i in range(1, 11)
        ]
        
        # 批量保存代理
        for proxy in proxies:
            await redis_manager.save_proxy(proxy)
        
        # 驗證保存次數
        assert redis_manager.save_proxy.call_count == 10
        
        # 批量提交驗證任務
        task_ids = []
        for proxy in proxies:
            task_id = await task_manager.submit_task(
                Task(
                    task_type=TaskType.PROXY_VALIDATION,
                    data={'proxy': proxy.to_dict()}
                )
            )
            task_ids.append(task_id)
        
        # 驗證任務提交
        assert len(task_ids) == 10
        assert task_manager.submit_task.call_count == 10
        
        # 批量驗證
        validation_results = []
        for proxy in proxies:
            result = await validator.validate_proxy(proxy)
            validation_results.append(result)
        
        # 驗證結果
        assert len(validation_results) == 10
        assert all(result['is_valid'] for result in validation_results)
    
    async def test_system_monitoring_integration(self, full_system):
        """測試系統監控整合"""
        components = full_system
        integrator = components['integrator']
        monitor = components['monitor']
        
        # 檢查系統健康狀態
        health = await monitor.get_system_health()
        assert health['status'] == 'healthy'
        assert 'cpu_usage' in health
        assert 'memory_usage' in health
        
        # 檢查組件健康狀態
        for component_name in ['redis_manager', 'validator', 'task_manager']:
            component_health = await integrator.check_component_health(component_name)
            assert component_health is True
        
        # 獲取系統指標
        system_status = await integrator.get_system_status()
        assert 'metrics' in system_status
        assert 'uptime' in system_status['metrics']


class TestPerformanceAndStress:
    """性能和壓力測試類"""
    
    @pytest.fixture
    async def performance_system(self):
        """創建性能測試系統"""
        # 創建高性能模擬組件
        redis_manager = AsyncMock(spec=RedisStorageManager)
        validator = AsyncMock(spec=CoreValidator)
        task_manager = AsyncMock(spec=TaskManager)
        
        # 設置快速響應
        redis_manager.save_proxy.return_value = True
        redis_manager.get_proxy.return_value = ProxyInfo(
            host="127.0.0.1", port=8080, protocol="http"
        )
        
        validator.validate_proxy.return_value = {
            'is_valid': True,
            'response_time': 0.1,
            'quality_score': 0.9
        }
        
        task_manager.submit_task.return_value = "task_perf"
        
        integrator = SystemIntegrator()
        await integrator.register_component("redis_manager", redis_manager, [])
        await integrator.register_component("validator", validator, ["redis_manager"])
        await integrator.register_component("task_manager", task_manager, ["redis_manager"])
        
        await integrator.start_all()
        
        yield {
            'integrator': integrator,
            'redis_manager': redis_manager,
            'validator': validator,
            'task_manager': task_manager
        }
        
        await integrator.shutdown()
    
    async def test_high_throughput_proxy_validation(self, performance_system):
        """測試高吞吐量代理驗證"""
        components = performance_system
        validator = components['validator']
        
        # 創建大量代理
        proxy_count = 1000
        proxies = [
            ProxyInfo(host=f"192.168.{i//255}.{i%255}", port=3128, protocol="http")
            for i in range(proxy_count)
        ]
        
        # 測量驗證時間
        start_time = time.time()
        
        # 並發驗證
        tasks = [validator.validate_proxy(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 性能斷言
        assert len(results) == proxy_count
        assert duration < 10.0  # 應該在10秒內完成1000個驗證
        
        throughput = proxy_count / duration
        assert throughput > 100  # 每秒至少100個驗證
        
        print(f"驗證吞吐量: {throughput:.2f} 代理/秒")
    
    async def test_concurrent_task_submission(self, performance_system):
        """測試並發任務提交"""
        components = performance_system
        task_manager = components['task_manager']
        
        # 並發提交任務
        task_count = 500
        start_time = time.time()
        
        tasks = [
            task_manager.submit_task(
                Task(
                    task_type=TaskType.PROXY_VALIDATION,
                    data={'proxy_id': f'proxy_{i}'}
                )
            )
            for i in range(task_count)
        ]
        
        task_ids = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 性能斷言
        assert len(task_ids) == task_count
        assert duration < 5.0  # 應該在5秒內完成500個任務提交
        
        submission_rate = task_count / duration
        assert submission_rate > 100  # 每秒至少100個任務提交
        
        print(f"任務提交速率: {submission_rate:.2f} 任務/秒")
    
    async def test_memory_usage_under_load(self, performance_system):
        """測試負載下的記憶體使用"""
        import psutil
        import gc
        
        components = performance_system
        redis_manager = components['redis_manager']
        
        # 記錄初始記憶體使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 創建大量代理對象
        proxy_count = 10000
        proxies = []
        
        for i in range(proxy_count):
            proxy = ProxyInfo(
                host=f"192.168.{i//255}.{i%255}",
                port=3128 + (i % 1000),
                protocol="http"
            )
            proxies.append(proxy)
            
            # 模擬保存到Redis
            await redis_manager.save_proxy(proxy)
        
        # 記錄峰值記憶體使用
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 清理對象
        del proxies
        gc.collect()
        
        # 記錄清理後記憶體使用
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 記憶體使用斷言
        memory_increase = peak_memory - initial_memory
        memory_per_proxy = memory_increase / proxy_count * 1024  # KB per proxy
        
        assert memory_per_proxy < 10  # 每個代理對象應該少於10KB
        
        # 記憶體洩漏檢查
        memory_leak = final_memory - initial_memory
        assert memory_leak < memory_increase * 0.5  # 洩漏應該少於峰值增量的50%
        
        print(f"初始記憶體: {initial_memory:.2f} MB")
        print(f"峰值記憶體: {peak_memory:.2f} MB")
        print(f"最終記憶體: {final_memory:.2f} MB")
        print(f"每代理記憶體: {memory_per_proxy:.2f} KB")
    
    async def test_system_stability_under_stress(self, performance_system):
        """測試壓力下的系統穩定性"""
        components = performance_system
        integrator = components['integrator']
        
        # 持續運行測試
        test_duration = 30  # 秒
        start_time = time.time()
        error_count = 0
        operation_count = 0
        
        while time.time() - start_time < test_duration:
            try:
                # 執行各種操作
                status = await integrator.get_system_status()
                assert status['status'] == 'running'
                
                # 檢查組件健康
                for component_name in ['redis_manager', 'validator', 'task_manager']:
                    health = await integrator.check_component_health(component_name)
                    assert health is True
                
                operation_count += 1
                
                # 短暫延遲
                await asyncio.sleep(0.1)
                
            except Exception as e:
                error_count += 1
                print(f"操作錯誤: {e}")
        
        # 穩定性斷言
        error_rate = error_count / operation_count if operation_count > 0 else 1
        assert error_rate < 0.01  # 錯誤率應該低於1%
        
        print(f"總操作數: {operation_count}")
        print(f"錯誤數: {error_count}")
        print(f"錯誤率: {error_rate:.4f}")


if __name__ == "__main__":
    """運行整合測試"""
    import sys
    
    async def run_tests():
        """運行所有測試"""
        print("開始運行整合測試...")
        
        # 運行基本整合測試
        print("\n=== 系統整合測試 ===")
        test_integration = TestSystemIntegration()
        
        # 運行端到端測試
        print("\n=== 端到端工作流程測試 ===")
        test_e2e = TestEndToEndWorkflow()
        
        # 運行性能測試
        print("\n=== 性能和壓力測試 ===")
        test_performance = TestPerformanceAndStress()
        
        print("\n所有整合測試完成！")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run":
        asyncio.run(run_tests())
    else:
        print("使用 'python test_integration.py --run' 來運行測試")
        print("或使用 'pytest tests/test_integration.py' 來運行pytest測試")