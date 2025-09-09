#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API模組

此模組提供代理爬蟲系統的完整API接口，包括：
- 統一API層（RESTful + WebSocket）
- 任務隊列API
- 代理管理API
- 系統監控API
- WebSocket實時通信
- API認證和授權
"""

from .task_queue_api import TaskQueueAPI
from .unified_api import (
    UnifiedAPI,
    APIStatus,
    WebSocketMessageType,
    APIResponse,
    ProxyRequest,
    ProxyValidationRequest,
    TaskRequest,
    WorkflowRequest,
    SystemConfigRequest,
    WebSocketConnection
)

__all__ = [
    'TaskQueueAPI',
    'UnifiedAPI',
    'APIStatus',
    'WebSocketMessageType',
    'APIResponse',
    'ProxyRequest',
    'ProxyValidationRequest',
    'TaskRequest',
    'WorkflowRequest',
    'SystemConfigRequest',
    'WebSocketConnection'
]