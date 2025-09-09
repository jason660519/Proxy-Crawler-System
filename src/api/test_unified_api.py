#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一API測試模組

此模組提供統一API層的完整測試覆蓋，包括：
- RESTful API端點測試
- WebSocket連接測試
- 認證和授權測試
- 錯誤處理測試
- 性能測試
- 整合測試
"""

import asyncio
import json
import pytest
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import status
import websockets
import aiohttp

# 導入被測試的模組
from .unified_api import UnifiedAPI, APIStatus, WebSocketMessageType
from ..core.system_integrator import SystemIntegrator, ComponentStatus
from ..core.task_manager import TaskType, TaskAction
from ..core.workflow_scheduler import SchedulingStrategy
from ..proxy_manager.validators.core_validator import ValidationLevel
from ..models.proxy import ProxyModel
from ..models.task import TaskModel


class TestUnifiedAPI:
    """統一API測試類"""
    
    @pytest.fixture
    async def mock_integrator(self):
        """創建模擬系統整合器"""
        integrator = Mock(spec=SystemIntegrator)
        integrator.is_running = True
        integrator.components = {
            'redis_storage': Mock(),
            'task_manager': Mock(),
            'workflow_scheduler': Mock(),
            'core_validator': Mock()
        }
        
        # 模擬組件狀態
        for component in integrator.components.values():
            component.status = ComponentStatus.ACTIVE
            component.last_error = None
        
        # 模擬方法
        integrator.get_system_status = Mock(return_value={
            'status': 'running',
            'components': 4,
            'uptime': '1h 30m',
            'memory_usage': '256MB'
        })
        
        integrator.get_component = Mock(side_effect=lambda name: integrator.components.get(name))
        integrator.validate_proxies = AsyncMock(return_value=[
            {'proxy_id': 'test1', 'valid': True, 'response_time': 0.5},
            {'proxy_id': 'test2', 'valid': False, 'error': 'Connection timeout'}
        ])
        
        integrator.store_proxy = AsyncMock(return_value=True)
        integrator.create_workflow = AsyncMock(return_value='workflow_123')
        integrator.add_event_handler = Mock()
        
        return integrator
    
    @pytest.fixture
    def api_client(self, mock_integrator):
        """創建API測試客戶端"""
        api = UnifiedAPI(mock_integrator)
        return TestClient(api.get_app())
    
    @pytest.fixture
    def api_instance(self, mock_integrator):
        """創建API實例"""
        return UnifiedAPI(mock_integrator)
    
    def test_api_initialization(self, mock_integrator):
        """測試API初始化"""
        config = {
            'enable_auth': True,
            'cors_origins': ['http://localhost:3000']
        }
        
        api = UnifiedAPI(mock_integrator, config)
        
        assert api.integrator == mock_integrator
        assert api.config == config
        assert api.enable_auth is True
        assert api.cors_origins == ['http://localhost:3000']
        assert api.websocket_connections == {}
    
    def test_system_status_endpoint(self, api_client, mock_integrator):
        """測試系統狀態端點"""
        response = api_client.get("/api/v1/system/status")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '系統狀態獲取成功'
        assert 'data' in data
        assert data['data']['status'] == 'running'
        
        mock_integrator.get_system_status.assert_called_once()
    
    def test_health_check_endpoint_healthy(self, api_client, mock_integrator):
        """測試健康檢查端點 - 健康狀態"""
        response = api_client.get("/api/v1/system/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '系統健康'
        assert data['data']['running'] is True
        assert data['data']['all_components_healthy'] is True
    
    def test_health_check_endpoint_unhealthy(self, api_client, mock_integrator):
        """測試健康檢查端點 - 不健康狀態"""
        # 設置一個組件為錯誤狀態
        mock_integrator.components['redis_storage'].status = ComponentStatus.ERROR
        mock_integrator.components['redis_storage'].last_error = 'Connection failed'
        
        response = api_client.get("/api/v1/system/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.WARNING.value
        assert data['message'] == '部分組件不健康'
        assert data['data']['running'] is True
        assert len(data['data']['unhealthy_components']) == 1
    
    def test_health_check_endpoint_not_running(self, api_client, mock_integrator):
        """測試健康檢查端點 - 系統未運行"""
        mock_integrator.is_running = False
        
        response = api_client.get("/api/v1/system/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.WARNING.value
        assert data['message'] == '系統未運行'
        assert data['data']['running'] is False
    
    def test_validate_proxies_endpoint(self, api_client, mock_integrator):
        """測試代理驗證端點"""
        request_data = {
            'proxies': [
                {
                    'host': '127.0.0.1',
                    'port': 8080,
                    'protocol': 'http',
                    'username': 'user1',
                    'password': 'pass1',
                    'tags': ['test']
                },
                {
                    'host': '127.0.0.1',
                    'port': 8081,
                    'protocol': 'http'
                }
            ],
            'validation_level': ValidationLevel.STANDARD.value,
            'timeout': 30,
            'max_workers': 10
        }
        
        response = api_client.post("/api/v1/proxies/validate", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert '成功驗證' in data['message']
        assert data['data']['total_count'] == 2
        assert data['data']['valid_count'] == 1
        assert len(data['data']['results']) == 2
        
        mock_integrator.validate_proxies.assert_called_once()
    
    def test_store_proxy_endpoint(self, api_client, mock_integrator):
        """測試存儲代理端點"""
        request_data = {
            'host': '127.0.0.1',
            'port': 8080,
            'protocol': 'http',
            'username': 'user1',
            'password': 'pass1',
            'tags': ['test']
        }
        
        response = api_client.post("/api/v1/proxies", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '代理存儲成功'
        assert 'proxy_id' in data['data']
        
        mock_integrator.store_proxy.assert_called_once()
    
    def test_get_proxies_endpoint(self, api_client, mock_integrator):
        """測試獲取代理列表端點"""
        # 模擬存儲組件
        storage_mock = mock_integrator.components['redis_storage']
        storage_mock.get_proxies = AsyncMock(return_value=[
            ProxyModel(
                host='127.0.0.1',
                port=8080,
                protocol='http',
                username='user1',
                password='pass1'
            )
        ])
        
        response = api_client.get("/api/v1/proxies?limit=50&offset=0&status=active")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '代理列表獲取成功'
        assert data['data']['count'] == 1
        assert data['data']['limit'] == 50
        assert data['data']['offset'] == 0
    
    def test_create_task_endpoint(self, api_client, mock_integrator):
        """測試創建任務端點"""
        # 模擬任務管理器
        task_manager_mock = mock_integrator.components['task_manager']
        task_manager_mock.create_task = AsyncMock(return_value='task_123')
        
        request_data = {
            'task_type': TaskType.PROXY_VALIDATION.value,
            'action': TaskAction.START.value,
            'config': {'timeout': 30},
            'priority': 5
        }
        
        response = api_client.post("/api/v1/tasks", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '任務創建成功'
        assert data['data']['task_id'] == 'task_123'
    
    def test_get_task_endpoint(self, api_client, mock_integrator):
        """測試獲取任務詳情端點"""
        # 模擬任務管理器
        task_manager_mock = mock_integrator.components['task_manager']
        task_model = TaskModel(
            id='task_123',
            task_type=TaskType.PROXY_VALIDATION,
            action=TaskAction.START,
            status='running',
            config={'timeout': 30},
            created_at=datetime.now()
        )
        task_manager_mock.get_task = AsyncMock(return_value=task_model)
        
        response = api_client.get("/api/v1/tasks/task_123")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '任務詳情獲取成功'
        assert data['data']['id'] == 'task_123'
    
    def test_get_task_not_found(self, api_client, mock_integrator):
        """測試獲取不存在的任務"""
        # 模擬任務管理器
        task_manager_mock = mock_integrator.components['task_manager']
        task_manager_mock.get_task = AsyncMock(return_value=None)
        
        response = api_client.get("/api/v1/tasks/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data['detail'] == '任務不存在'
    
    def test_get_tasks_endpoint(self, api_client, mock_integrator):
        """測試獲取任務列表端點"""
        # 模擬任務管理器
        task_manager_mock = mock_integrator.components['task_manager']
        task_manager_mock.get_tasks = AsyncMock(return_value=[
            TaskModel(
                id='task_1',
                task_type=TaskType.PROXY_VALIDATION,
                action=TaskAction.START,
                status='completed',
                config={},
                created_at=datetime.now()
            )
        ])
        
        response = api_client.get("/api/v1/tasks?limit=100&status=completed")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '任務列表獲取成功'
        assert data['data']['count'] == 1
        assert data['data']['limit'] == 100
    
    def test_create_workflow_endpoint(self, api_client, mock_integrator):
        """測試創建工作流程端點"""
        request_data = {
            'name': '測試工作流程',
            'description': '這是一個測試工作流程',
            'tasks': [
                {'type': 'validation', 'config': {'timeout': 30}},
                {'type': 'storage', 'config': {'batch_size': 100}}
            ],
            'strategy': SchedulingStrategy.ROUND_ROBIN.value,
            'max_concurrent': 5
        }
        
        response = api_client.post("/api/v1/workflows", json=request_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '工作流程創建成功'
        assert data['data']['workflow_id'] == 'workflow_123'
        
        mock_integrator.create_workflow.assert_called_once()
    
    def test_get_workflow_endpoint(self, api_client, mock_integrator):
        """測試獲取工作流程詳情端點"""
        # 模擬工作流程調度器
        scheduler_mock = mock_integrator.components['workflow_scheduler']
        workflow_data = {
            'id': 'workflow_123',
            'name': '測試工作流程',
            'status': 'running',
            'tasks': []
        }
        scheduler_mock.get_workflow = AsyncMock(return_value=workflow_data)
        
        response = api_client.get("/api/v1/workflows/workflow_123")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data['status'] == APIStatus.SUCCESS.value
        assert data['message'] == '工作流程詳情獲取成功'
        assert data['data']['id'] == 'workflow_123'
    
    def test_get_workflow_not_found(self, api_client, mock_integrator):
        """測試獲取不存在的工作流程"""
        # 模擬工作流程調度器
        scheduler_mock = mock_integrator.components['workflow_scheduler']
        scheduler_mock.get_workflow = AsyncMock(return_value=None)
        
        response = api_client.get("/api/v1/workflows/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data['detail'] == '工作流程不存在'
    
    def test_service_unavailable_errors(self, api_client, mock_integrator):
        """測試服務不可用錯誤"""
        # 設置組件為None（不可用）
        mock_integrator.get_component = Mock(return_value=None)
        
        # 測試代理列表端點
        response = api_client.get("/api/v1/proxies")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()['detail'] == '存儲服務不可用'
        
        # 測試任務創建端點
        request_data = {
            'task_type': TaskType.PROXY_VALIDATION.value,
            'action': TaskAction.START.value,
            'config': {},
            'priority': 5
        }
        response = api_client.post("/api/v1/tasks", json=request_data)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()['detail'] == '任務管理器不可用'
    
    def test_validation_errors(self, api_client):
        """測試請求驗證錯誤"""
        # 測試無效的代理驗證請求
        invalid_request = {
            'proxies': [
                {
                    'host': '127.0.0.1',
                    'port': 99999,  # 無效端口
                    'protocol': 'http'
                }
            ]
        }
        
        response = api_client.post("/api/v1/proxies/validate", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, api_instance):
        """測試WebSocket連接"""
        # 模擬WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=[
            json.dumps({'type': 'ping'}),
            json.dumps({'type': 'subscribe', 'subscriptions': ['system_status']}),
            json.dumps({'type': 'get_status'})
        ])
        mock_websocket.send_text = AsyncMock()
        
        client_id = 'test_client'
        
        # 模擬連接處理（簡化版）
        connection_data = {
            'websocket': mock_websocket,
            'client_id': client_id,
            'connected_at': datetime.now(),
            'last_ping': datetime.now(),
            'subscriptions': list(WebSocketMessageType)
        }
        
        # 測試ping消息處理
        await api_instance._handle_websocket_message(
            Mock(**connection_data),
            json.dumps({'type': 'ping'})
        )
        
        # 驗證pong響應
        mock_websocket.send_text.assert_called()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message['type'] == 'pong'
    
    @pytest.mark.asyncio
    async def test_websocket_message_handling(self, api_instance):
        """測試WebSocket消息處理"""
        mock_websocket = AsyncMock()
        connection = Mock(
            websocket=mock_websocket,
            client_id='test_client',
            subscriptions=[WebSocketMessageType.SYSTEM_STATUS]
        )
        
        # 測試訂閱消息
        await api_instance._handle_websocket_message(
            connection,
            json.dumps({
                'type': 'subscribe',
                'subscriptions': ['system_status', 'task_update']
            })
        )
        
        # 驗證訂閱更新
        assert WebSocketMessageType.SYSTEM_STATUS in connection.subscriptions
        assert WebSocketMessageType.TASK_UPDATE in connection.subscriptions
    
    @pytest.mark.asyncio
    async def test_websocket_broadcast(self, api_instance):
        """測試WebSocket廣播"""
        # 添加模擬連接
        mock_websocket1 = AsyncMock()
        mock_websocket2 = AsyncMock()
        
        api_instance.websocket_connections = {
            'client1': Mock(
                websocket=mock_websocket1,
                subscriptions=[WebSocketMessageType.SYSTEM_STATUS]
            ),
            'client2': Mock(
                websocket=mock_websocket2,
                subscriptions=[WebSocketMessageType.TASK_UPDATE]
            )
        }
        
        # 廣播系統狀態消息
        await api_instance._broadcast_to_websockets(
            WebSocketMessageType.SYSTEM_STATUS,
            {'status': 'running'}
        )
        
        # 驗證只有訂閱的客戶端收到消息
        mock_websocket1.send_text.assert_called_once()
        mock_websocket2.send_text.assert_not_called()
    
    def test_event_mapping(self, api_instance):
        """測試事件映射"""
        from ..core.system_integrator import IntegrationEvent
        
        # 測試事件到消息類型的映射
        message_type = api_instance._map_event_to_message_type(
            IntegrationEvent.COMPONENT_STARTED
        )
        assert message_type == WebSocketMessageType.SYSTEM_STATUS
        
        message_type = api_instance._map_event_to_message_type(
            IntegrationEvent.VALIDATION_COMPLETED
        )
        assert message_type == WebSocketMessageType.PROXY_UPDATE
    
    def test_cors_configuration(self, mock_integrator):
        """測試CORS配置"""
        config = {
            'cors_origins': ['http://localhost:3000', 'https://example.com']
        }
        
        api = UnifiedAPI(mock_integrator, config)
        assert api.cors_origins == ['http://localhost:3000', 'https://example.com']
    
    @pytest.mark.asyncio
    async def test_error_handling(self, api_client, mock_integrator):
        """測試錯誤處理"""
        # 模擬系統整合器拋出異常
        mock_integrator.get_system_status.side_effect = Exception("測試錯誤")
        
        response = api_client.get("/api/v1/system/status")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "測試錯誤" in response.json()['detail']


@pytest.mark.asyncio
async def test_integration_api_workflow():
    """整合測試：完整的API工作流程"""
    logging.basicConfig(level=logging.INFO)
    
    # 創建真實的系統整合器（使用模擬配置）
    config = {
        'redis': {'host': 'localhost', 'port': 6379, 'db': 1},  # 使用測試數據庫
        'validator': {'level': 'STANDARD', 'max_workers': 2},
        'task_manager': {'max_workers': 2},
        'workflow_scheduler': {'strategy': 'ROUND_ROBIN'},
        'health_check_interval': 10
    }
    
    try:
        integrator = SystemIntegrator(config)
        api = UnifiedAPI(integrator)
        
        # 測試API應用創建
        app = api.get_app()
        assert app is not None
        
        # 測試客戶端
        client = TestClient(app)
        
        # 測試健康檢查
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        
        print("整合測試：API工作流程測試完成")
        
    except Exception as e:
        print(f"整合測試失敗: {e}")
        # 在CI環境中，Redis可能不可用，這是正常的
        assert "Connection" in str(e) or "Redis" in str(e)


# 性能測試
@pytest.mark.asyncio
async def test_api_performance():
    """API性能測試"""
    import time
    
    # 創建模擬整合器
    mock_integrator = Mock(spec=SystemIntegrator)
    mock_integrator.is_running = True
    mock_integrator.components = {'redis_storage': Mock()}
    mock_integrator.get_system_status = Mock(return_value={'status': 'running'})
    
    api = UnifiedAPI(mock_integrator)
    client = TestClient(api.get_app())
    
    # 測試多個並發請求
    start_time = time.time()
    
    responses = []
    for _ in range(100):
        response = client.get("/api/v1/system/status")
        responses.append(response)
    
    end_time = time.time()
    
    # 驗證所有請求都成功
    for response in responses:
        assert response.status_code == 200
    
    # 驗證性能（100個請求應該在1秒內完成）
    total_time = end_time - start_time
    assert total_time < 1.0, f"API性能測試失敗，耗時: {total_time:.3f}秒"
    
    print(f"性能測試完成：100個請求耗時 {total_time:.3f}秒")


if __name__ == "__main__":
    # 運行測試
    pytest.main([__file__, "-v"])