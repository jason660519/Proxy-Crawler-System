#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
統一API層模組

此模組提供完整的RESTful API接口和WebSocket支持，
整合所有核心組件功能，包括：
- 代理管理API
- 任務管理API
- 工作流程API
- 系統監控API
- WebSocket實時通信
- API認證和授權
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# 導入核心組件
from ..core.system_integrator import SystemIntegrator, ComponentStatus, IntegrationEvent
from ..core.task_manager import TaskType, TaskAction
from ..core.workflow_scheduler import WorkflowStatus, SchedulingStrategy
from ..proxy_manager.validators.core_validator import ValidationLevel
from ..models.proxy import ProxyModel
from ..models.task import TaskModel


class APIStatus(Enum):
    """API狀態枚舉"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class WebSocketMessageType(Enum):
    """WebSocket消息類型"""
    SYSTEM_STATUS = "system_status"
    TASK_UPDATE = "task_update"
    PROXY_UPDATE = "proxy_update"
    WORKFLOW_UPDATE = "workflow_update"
    ERROR_NOTIFICATION = "error_notification"
    HEALTH_CHECK = "health_check"


# Pydantic模型定義
class APIResponse(BaseModel):
    """API響應模型"""
    status: APIStatus
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = None


class ProxyRequest(BaseModel):
    """代理請求模型"""
    host: str = Field(..., description="代理主機地址")
    port: int = Field(..., ge=1, le=65535, description="代理端口")
    protocol: str = Field(..., description="代理協議")
    username: Optional[str] = Field(None, description="用戶名")
    password: Optional[str] = Field(None, description="密碼")
    tags: Optional[List[str]] = Field(default_factory=list, description="標籤")


class ProxyValidationRequest(BaseModel):
    """代理驗證請求模型"""
    proxies: List[ProxyRequest]
    validation_level: ValidationLevel = ValidationLevel.STANDARD
    timeout: Optional[int] = Field(30, ge=1, le=300, description="超時時間（秒）")
    max_workers: Optional[int] = Field(10, ge=1, le=50, description="最大工作線程數")


class TaskRequest(BaseModel):
    """任務請求模型"""
    task_type: TaskType
    action: TaskAction
    config: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(5, ge=1, le=10, description="任務優先級")
    scheduled_time: Optional[datetime] = Field(None, description="計劃執行時間")


class WorkflowRequest(BaseModel):
    """工作流程請求模型"""
    name: str = Field(..., description="工作流程名稱")
    description: Optional[str] = Field(None, description="工作流程描述")
    tasks: List[Dict[str, Any]] = Field(..., description="任務列表")
    strategy: SchedulingStrategy = SchedulingStrategy.ROUND_ROBIN
    max_concurrent: int = Field(5, ge=1, le=20, description="最大並發數")


class SystemConfigRequest(BaseModel):
    """系統配置請求模型"""
    component: str = Field(..., description="組件名稱")
    config: Dict[str, Any] = Field(..., description="配置參數")


@dataclass
class WebSocketConnection:
    """WebSocket連接信息"""
    websocket: WebSocket
    client_id: str
    connected_at: datetime
    last_ping: datetime
    subscriptions: List[WebSocketMessageType]


class UnifiedAPI:
    """統一API層
    
    提供完整的RESTful API和WebSocket支持，整合所有核心組件。
    """
    
    def __init__(self, integrator: SystemIntegrator, config: Optional[Dict[str, Any]] = None):
        """初始化統一API
        
        Args:
            integrator: 系統整合器實例
            config: API配置
        """
        self.integrator = integrator
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # FastAPI應用
        self.app = FastAPI(
            title="Proxy Crawler System API",
            description="代理爬蟲系統統一API接口",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # WebSocket連接管理
        self.websocket_connections: Dict[str, WebSocketConnection] = {}
        
        # API配置
        self.enable_auth = self.config.get('enable_auth', False)
        self.cors_origins = self.config.get('cors_origins', ["*"])
        
        # 設置中間件和路由
        self._setup_middleware()
        self._setup_routes()
        self._setup_event_handlers()
    
    def _setup_middleware(self) -> None:
        """設置中間件"""
        # CORS中間件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 請求日誌中間件
        @self.app.middleware("http")
        async def log_requests(request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            process_time = (datetime.now() - start_time).total_seconds()
            
            self.logger.info(
                f"{request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )
            return response
    
    def _setup_routes(self) -> None:
        """設置API路由"""
        # 系統狀態API
        @self.app.get("/api/v1/system/status", response_model=APIResponse)
        async def get_system_status():
            """獲取系統狀態"""
            try:
                status = self.integrator.get_system_status()
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="系統狀態獲取成功",
                    data=status
                )
            except Exception as e:
                self.logger.error(f"獲取系統狀態失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/system/health", response_model=APIResponse)
        async def health_check():
            """健康檢查"""
            try:
                # 檢查系統整合器狀態
                if not self.integrator.is_running:
                    return APIResponse(
                        status=APIStatus.WARNING,
                        message="系統未運行",
                        data={"running": False}
                    )
                
                # 檢查組件狀態
                unhealthy_components = []
                for name, component in self.integrator.components.items():
                    if component.status != ComponentStatus.ACTIVE:
                        unhealthy_components.append({
                            "name": name,
                            "status": component.status.value,
                            "error": component.last_error
                        })
                
                if unhealthy_components:
                    return APIResponse(
                        status=APIStatus.WARNING,
                        message="部分組件不健康",
                        data={
                            "running": True,
                            "unhealthy_components": unhealthy_components
                        }
                    )
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="系統健康",
                    data={"running": True, "all_components_healthy": True}
                )
                
            except Exception as e:
                self.logger.error(f"健康檢查失敗: {e}")
                return APIResponse(
                    status=APIStatus.ERROR,
                    message=f"健康檢查失敗: {str(e)}",
                    data={"running": False}
                )
        
        # 代理管理API
        @self.app.post("/api/v1/proxies/validate", response_model=APIResponse)
        async def validate_proxies(request: ProxyValidationRequest):
            """驗證代理列表"""
            try:
                # 轉換為ProxyModel
                proxy_models = [
                    ProxyModel(
                        host=proxy.host,
                        port=proxy.port,
                        protocol=proxy.protocol,
                        username=proxy.username,
                        password=proxy.password,
                        tags=proxy.tags or []
                    )
                    for proxy in request.proxies
                ]
                
                # 執行驗證
                results = await self.integrator.validate_proxies(
                    proxy_models, 
                    request.validation_level
                )
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message=f"成功驗證 {len(results)} 個代理",
                    data={
                        "total_count": len(results),
                        "valid_count": sum(1 for r in results if r.get('valid', False)),
                        "results": results
                    }
                )
                
            except Exception as e:
                self.logger.error(f"代理驗證失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/api/v1/proxies", response_model=APIResponse)
        async def store_proxy(request: ProxyRequest):
            """存儲代理"""
            try:
                proxy_model = ProxyModel(
                    host=request.host,
                    port=request.port,
                    protocol=request.protocol,
                    username=request.username,
                    password=request.password,
                    tags=request.tags or []
                )
                
                success = await self.integrator.store_proxy(proxy_model)
                
                if success:
                    return APIResponse(
                        status=APIStatus.SUCCESS,
                        message="代理存儲成功",
                        data={"proxy_id": proxy_model.id}
                    )
                else:
                    return APIResponse(
                        status=APIStatus.ERROR,
                        message="代理存儲失敗"
                    )
                    
            except Exception as e:
                self.logger.error(f"代理存儲失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/proxies", response_model=APIResponse)
        async def get_proxies(
            limit: int = 100,
            offset: int = 0,
            status: Optional[str] = None,
            protocol: Optional[str] = None
        ):
            """獲取代理列表"""
            try:
                storage = self.integrator.get_component('redis_storage')
                if not storage:
                    raise HTTPException(status_code=503, detail="存儲服務不可用")
                
                # 構建查詢條件
                filters = {}
                if status:
                    filters['status'] = status
                if protocol:
                    filters['protocol'] = protocol
                
                # 獲取代理列表
                proxies = await storage.get_proxies(
                    limit=limit,
                    offset=offset,
                    filters=filters
                )
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="代理列表獲取成功",
                    data={
                        "proxies": [asdict(proxy) for proxy in proxies],
                        "count": len(proxies),
                        "limit": limit,
                        "offset": offset
                    }
                )
                
            except Exception as e:
                self.logger.error(f"獲取代理列表失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # 任務管理API
        @self.app.post("/api/v1/tasks", response_model=APIResponse)
        async def create_task(request: TaskRequest):
            """創建任務"""
            try:
                task_manager = self.integrator.get_component('task_manager')
                if not task_manager:
                    raise HTTPException(status_code=503, detail="任務管理器不可用")
                
                task_id = await task_manager.create_task(
                    task_type=request.task_type,
                    action=request.action,
                    config=request.config,
                    priority=request.priority,
                    scheduled_time=request.scheduled_time
                )
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="任務創建成功",
                    data={"task_id": task_id}
                )
                
            except Exception as e:
                self.logger.error(f"任務創建失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/tasks/{task_id}", response_model=APIResponse)
        async def get_task(task_id: str):
            """獲取任務詳情"""
            try:
                task_manager = self.integrator.get_component('task_manager')
                if not task_manager:
                    raise HTTPException(status_code=503, detail="任務管理器不可用")
                
                task = await task_manager.get_task(task_id)
                if not task:
                    raise HTTPException(status_code=404, detail="任務不存在")
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="任務詳情獲取成功",
                    data=asdict(task)
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"獲取任務詳情失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/tasks", response_model=APIResponse)
        async def get_tasks(
            limit: int = 100,
            offset: int = 0,
            status: Optional[str] = None,
            task_type: Optional[TaskType] = None
        ):
            """獲取任務列表"""
            try:
                task_manager = self.integrator.get_component('task_manager')
                if not task_manager:
                    raise HTTPException(status_code=503, detail="任務管理器不可用")
                
                # 構建查詢條件
                filters = {}
                if status:
                    filters['status'] = status
                if task_type:
                    filters['task_type'] = task_type
                
                tasks = await task_manager.get_tasks(
                    limit=limit,
                    offset=offset,
                    filters=filters
                )
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="任務列表獲取成功",
                    data={
                        "tasks": [asdict(task) for task in tasks],
                        "count": len(tasks),
                        "limit": limit,
                        "offset": offset
                    }
                )
                
            except Exception as e:
                self.logger.error(f"獲取任務列表失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # 工作流程API
        @self.app.post("/api/v1/workflows", response_model=APIResponse)
        async def create_workflow(request: WorkflowRequest):
            """創建工作流程"""
            try:
                workflow_config = {
                    'name': request.name,
                    'description': request.description,
                    'tasks': request.tasks,
                    'strategy': request.strategy,
                    'max_concurrent': request.max_concurrent
                }
                
                workflow_id = await self.integrator.create_workflow(workflow_config)
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="工作流程創建成功",
                    data={"workflow_id": workflow_id}
                )
                
            except Exception as e:
                self.logger.error(f"工作流程創建失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/api/v1/workflows/{workflow_id}", response_model=APIResponse)
        async def get_workflow(workflow_id: str):
            """獲取工作流程詳情"""
            try:
                scheduler = self.integrator.get_component('workflow_scheduler')
                if not scheduler:
                    raise HTTPException(status_code=503, detail="工作流程調度器不可用")
                
                workflow = await scheduler.get_workflow(workflow_id)
                if not workflow:
                    raise HTTPException(status_code=404, detail="工作流程不存在")
                
                return APIResponse(
                    status=APIStatus.SUCCESS,
                    message="工作流程詳情獲取成功",
                    data=workflow
                )
                
            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"獲取工作流程詳情失敗: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # WebSocket端點
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            """WebSocket連接端點"""
            await self._handle_websocket_connection(websocket, client_id)
    
    def _setup_event_handlers(self) -> None:
        """設置事件處理器"""
        # 監聽系統事件並通過WebSocket廣播
        async def broadcast_event(event: IntegrationEvent, data: Dict[str, Any]):
            """廣播系統事件"""
            message_type = self._map_event_to_message_type(event)
            if message_type:
                await self._broadcast_to_websockets(message_type, data)
        
        # 註冊事件處理器
        for event in IntegrationEvent:
            self.integrator.add_event_handler(event, broadcast_event)
    
    def _map_event_to_message_type(self, event: IntegrationEvent) -> Optional[WebSocketMessageType]:
        """將系統事件映射到WebSocket消息類型"""
        mapping = {
            IntegrationEvent.COMPONENT_STARTED: WebSocketMessageType.SYSTEM_STATUS,
            IntegrationEvent.COMPONENT_STOPPED: WebSocketMessageType.SYSTEM_STATUS,
            IntegrationEvent.COMPONENT_ERROR: WebSocketMessageType.ERROR_NOTIFICATION,
            IntegrationEvent.VALIDATION_COMPLETED: WebSocketMessageType.PROXY_UPDATE,
            IntegrationEvent.WORKFLOW_UPDATED: WebSocketMessageType.WORKFLOW_UPDATE,
            IntegrationEvent.STORAGE_UPDATED: WebSocketMessageType.PROXY_UPDATE,
            IntegrationEvent.SYSTEM_HEALTH_CHECK: WebSocketMessageType.HEALTH_CHECK
        }
        return mapping.get(event)
    
    async def _handle_websocket_connection(self, websocket: WebSocket, client_id: str):
        """處理WebSocket連接"""
        await websocket.accept()
        
        connection = WebSocketConnection(
            websocket=websocket,
            client_id=client_id,
            connected_at=datetime.now(),
            last_ping=datetime.now(),
            subscriptions=list(WebSocketMessageType)  # 默認訂閱所有消息
        )
        
        self.websocket_connections[client_id] = connection
        self.logger.info(f"WebSocket客戶端 {client_id} 已連接")
        
        try:
            while True:
                # 接收客戶端消息
                data = await websocket.receive_text()
                await self._handle_websocket_message(connection, data)
                
        except WebSocketDisconnect:
            self.logger.info(f"WebSocket客戶端 {client_id} 已斷開連接")
        except Exception as e:
            self.logger.error(f"WebSocket連接錯誤: {e}")
        finally:
            # 清理連接
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
    
    async def _handle_websocket_message(self, connection: WebSocketConnection, message: str):
        """處理WebSocket消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'ping':
                connection.last_ping = datetime.now()
                await connection.websocket.send_text(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            
            elif message_type == 'subscribe':
                # 更新訂閱
                subscriptions = data.get('subscriptions', [])
                connection.subscriptions = [
                    WebSocketMessageType(sub) for sub in subscriptions
                    if sub in [t.value for t in WebSocketMessageType]
                ]
                
                await connection.websocket.send_text(json.dumps({
                    'type': 'subscription_updated',
                    'subscriptions': [sub.value for sub in connection.subscriptions]
                }))
            
            elif message_type == 'get_status':
                # 發送當前系統狀態
                status = self.integrator.get_system_status()
                await connection.websocket.send_text(json.dumps({
                    'type': 'system_status',
                    'data': status,
                    'timestamp': datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await connection.websocket.send_text(json.dumps({
                'type': 'error',
                'message': '無效的JSON格式'
            }))
        except Exception as e:
            self.logger.error(f"處理WebSocket消息失敗: {e}")
            await connection.websocket.send_text(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def _broadcast_to_websockets(self, message_type: WebSocketMessageType, data: Dict[str, Any]):
        """向所有訂閱的WebSocket客戶端廣播消息"""
        if not self.websocket_connections:
            return
        
        message = {
            'type': message_type.value,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        message_text = json.dumps(message, ensure_ascii=False)
        
        # 向所有訂閱此消息類型的客戶端發送
        disconnected_clients = []
        
        for client_id, connection in self.websocket_connections.items():
            if message_type in connection.subscriptions:
                try:
                    await connection.websocket.send_text(message_text)
                except Exception as e:
                    self.logger.error(f"向客戶端 {client_id} 發送消息失敗: {e}")
                    disconnected_clients.append(client_id)
        
        # 清理斷開的連接
        for client_id in disconnected_clients:
            if client_id in self.websocket_connections:
                del self.websocket_connections[client_id]
    
    async def start_server(self, host: str = "0.0.0.0", port: int = 8000):
        """啟動API服務器"""
        self.logger.info(f"正在啟動API服務器 {host}:{port}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_app(self) -> FastAPI:
        """獲取FastAPI應用實例"""
        return self.app


# 測試函數
async def main():
    """測試統一API"""
    logging.basicConfig(level=logging.INFO)
    
    # 創建系統整合器
    config = {
        'redis': {'host': 'localhost', 'port': 6379, 'db': 0},
        'validator': {'level': 'STANDARD', 'max_workers': 10},
        'task_manager': {'max_workers': 5},
        'workflow_scheduler': {'strategy': 'ROUND_ROBIN'},
        'health_check_interval': 30
    }
    
    integrator = SystemIntegrator(config)
    
    # 創建API
    api_config = {
        'enable_auth': False,
        'cors_origins': ["*"]
    }
    
    api = UnifiedAPI(integrator, api_config)
    
    # 啟動系統
    async with integrator.managed_lifecycle():
        print("統一API測試開始")
        print(f"API文檔地址: http://localhost:8000/docs")
        print(f"WebSocket測試地址: ws://localhost:8000/ws/test_client")
        
        # 啟動API服務器（這會阻塞）
        await api.start_server(host="localhost", port=8000)


if __name__ == "__main__":
    asyncio.run(main())