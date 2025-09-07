#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
監控儀表板

提供實時監控代理狀態和系統性能的 Web 介面，包括：
1. 實時數據展示
2. 性能指標監控
3. 系統健康狀態
4. 歷史趨勢分析
5. 警報和通知

作者: JasonSpider 專案
日期: 2024
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import aiohttp
from aiohttp import web, WSMsgType
from aiohttp.web import Application, Request, Response, WebSocketResponse
import aiohttp_cors
from loguru import logger
import jinja2
import aiofiles

# 導入相關模組
from .proxy_etl_pipeline import ProxyETLPipeline, ETLStage, ETLMetrics
from .data_validator import ProxyDataValidator, ValidationConfig
from ..proxy_manager.models import ProxyNode, ProxyStatus
from database_config import db_config


@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: datetime
    total_proxies: int
    active_proxies: int
    inactive_proxies: int
    validation_success_rate: float
    avg_response_time: float
    etl_pipeline_status: str
    memory_usage_mb: float
    cpu_usage_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class AlertRule:
    """警報規則"""
    name: str
    metric: str
    operator: str  # '>', '<', '>=', '<=', '==', '!='
    threshold: float
    severity: str  # 'info', 'warning', 'error', 'critical'
    enabled: bool = True
    
    def check(self, value: float) -> bool:
        """檢查是否觸發警報"""
        if not self.enabled:
            return False
        
        operators = {
            '>': lambda x, y: x > y,
            '<': lambda x, y: x < y,
            '>=': lambda x, y: x >= y,
            '<=': lambda x, y: x <= y,
            '==': lambda x, y: x == y,
            '!=': lambda x, y: x != y
        }
        
        return operators.get(self.operator, lambda x, y: False)(value, self.threshold)


@dataclass
class Alert:
    """警報"""
    id: str
    rule_name: str
    message: str
    severity: str
    timestamp: datetime
    acknowledged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class MonitoringDashboard:
    """監控儀表板
    
    提供 Web 介面來監控代理系統的狀態和性能
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8888):
        self.host = host
        self.port = port
        self.app: Optional[Application] = None
        self.logger = logger.bind(component='MonitoringDashboard')
        
        # WebSocket 連接管理
        self.websocket_connections: List[WebSocketResponse] = []
        
        # 數據存儲
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        self.alert_rules: List[AlertRule] = []
        
        # 監控任務
        self.monitoring_task: Optional[asyncio.Task] = None
        self.metrics_collection_interval = 30  # 秒
        
        # 組件引用
        self.etl_pipeline: Optional[ProxyETLPipeline] = None
        self.validator: Optional[ProxyDataValidator] = None
        
        # 初始化警報規則
        self._initialize_alert_rules()
    
    def _initialize_alert_rules(self) -> None:
        """初始化預設警報規則"""
        self.alert_rules = [
            AlertRule(
                name="低驗證成功率",
                metric="validation_success_rate",
                operator="<",
                threshold=0.7,
                severity="warning"
            ),
            AlertRule(
                name="高響應時間",
                metric="avg_response_time",
                operator=">",
                threshold=5000,
                severity="warning"
            ),
            AlertRule(
                name="活躍代理數量過低",
                metric="active_proxies",
                operator="<",
                threshold=10,
                severity="error"
            ),
            AlertRule(
                name="高記憶體使用",
                metric="memory_usage_mb",
                operator=">",
                threshold=1000,
                severity="warning"
            ),
            AlertRule(
                name="高 CPU 使用率",
                metric="cpu_usage_percent",
                operator=">",
                threshold=80,
                severity="warning"
            )
        ]
    
    async def initialize(self) -> None:
        """初始化儀表板"""
        # 創建 Web 應用
        self.app = web.Application()
        
        # 設置 CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # 設置路由
        self._setup_routes()
        
        # 為所有路由添加 CORS
        for route in list(self.app.router.routes()):
            cors.add(route)
        
        # 設置靜態文件服務
        static_dir = Path(__file__).parent / 'static'
        if static_dir.exists():
            self.app.router.add_static('/static/', static_dir)
        
        # 設置模板引擎
        template_dir = Path(__file__).parent / 'templates'
        if template_dir.exists():
            self.jinja_env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(template_dir))
            )
        
        self.logger.info(f"監控儀表板初始化完成，將在 {self.host}:{self.port} 啟動")
    
    def _setup_routes(self) -> None:
        """設置路由"""
        # Web 頁面路由
        self.app.router.add_get('/', self.index_handler)
        self.app.router.add_get('/dashboard', self.dashboard_handler)
        
        # API 路由
        self.app.router.add_get('/api/metrics', self.get_metrics_handler)
        self.app.router.add_get('/api/metrics/history', self.get_metrics_history_handler)
        self.app.router.add_get('/api/proxies', self.get_proxies_handler)
        self.app.router.add_get('/api/alerts', self.get_alerts_handler)
        self.app.router.add_post('/api/alerts/{alert_id}/acknowledge', self.acknowledge_alert_handler)
        self.app.router.add_get('/api/system/status', self.get_system_status_handler)
        
        # WebSocket 路由
        self.app.router.add_get('/ws', self.websocket_handler)
    
    async def start(self) -> None:
        """啟動儀表板"""
        if not self.app:
            await self.initialize()
        
        # 啟動監控任務
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # 啟動 Web 服務器
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        self.logger.info(f"監控儀表板已啟動: http://{self.host}:{self.port}")
    
    async def stop(self) -> None:
        """停止儀表板"""
        # 停止監控任務
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        # 關閉 WebSocket 連接
        for ws in self.websocket_connections:
            if not ws.closed:
                await ws.close()
        
        self.logger.info("監控儀表板已停止")
    
    async def _monitoring_loop(self) -> None:
        """監控循環"""
        while True:
            try:
                # 收集系統指標
                metrics = await self._collect_system_metrics()
                
                # 添加到歷史記錄
                self.metrics_history.append(metrics)
                
                # 保持歷史記錄在合理範圍內（最近24小時）
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.metrics_history = [
                    m for m in self.metrics_history 
                    if m.timestamp > cutoff_time
                ]
                
                # 檢查警報
                await self._check_alerts(metrics)
                
                # 廣播更新到 WebSocket 客戶端
                await self._broadcast_update({
                    'type': 'metrics_update',
                    'data': metrics.to_dict()
                })
                
                # 等待下次收集
                await asyncio.sleep(self.metrics_collection_interval)
                
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            import psutil
            
            # 系統資源指標
            memory_info = psutil.virtual_memory()
            memory_usage_mb = memory_info.used / 1024 / 1024
            cpu_usage_percent = psutil.cpu_percent(interval=1)
            
            # 代理相關指標（模擬數據，實際應從數據庫獲取）
            total_proxies = 1000  # 從數據庫查詢
            active_proxies = 750   # 從數據庫查詢
            inactive_proxies = total_proxies - active_proxies
            
            # ETL 管道狀態
            etl_status = "running" if self.etl_pipeline else "stopped"
            
            # 驗證成功率（從驗證器獲取）
            validation_success_rate = 0.85
            if self.validator:
                stats = self.validator.get_validation_statistics()
                if stats['total_validated'] > 0:
                    validation_success_rate = stats['valid_rate']
            
            # 平均響應時間（模擬數據）
            avg_response_time = 2500.0
            
            return SystemMetrics(
                timestamp=datetime.now(),
                total_proxies=total_proxies,
                active_proxies=active_proxies,
                inactive_proxies=inactive_proxies,
                validation_success_rate=validation_success_rate,
                avg_response_time=avg_response_time,
                etl_pipeline_status=etl_status,
                memory_usage_mb=memory_usage_mb,
                cpu_usage_percent=cpu_usage_percent
            )
            
        except ImportError:
            # 如果 psutil 不可用，返回模擬數據
            return SystemMetrics(
                timestamp=datetime.now(),
                total_proxies=1000,
                active_proxies=750,
                inactive_proxies=250,
                validation_success_rate=0.85,
                avg_response_time=2500.0,
                etl_pipeline_status="unknown",
                memory_usage_mb=512.0,
                cpu_usage_percent=45.0
            )
    
    async def _check_alerts(self, metrics: SystemMetrics) -> None:
        """檢查警報條件"""
        metrics_dict = metrics.to_dict()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            metric_value = metrics_dict.get(rule.metric)
            if metric_value is None:
                continue
            
            if rule.check(metric_value):
                # 檢查是否已經有相同的未確認警報
                existing_alert = next(
                    (alert for alert in self.alerts 
                     if alert.rule_name == rule.name and not alert.acknowledged),
                    None
                )
                
                if not existing_alert:
                    # 創建新警報
                    alert = Alert(
                        id=f"{rule.name}_{int(time.time())}",
                        rule_name=rule.name,
                        message=f"{rule.name}: {rule.metric} = {metric_value} {rule.operator} {rule.threshold}",
                        severity=rule.severity,
                        timestamp=datetime.now()
                    )
                    
                    self.alerts.append(alert)
                    
                    # 廣播警報
                    await self._broadcast_update({
                        'type': 'new_alert',
                        'data': alert.to_dict()
                    })
                    
                    self.logger.warning(f"觸發警報: {alert.message}")
    
    async def _broadcast_update(self, message: Dict[str, Any]) -> None:
        """廣播更新到所有 WebSocket 客戶端"""
        if not self.websocket_connections:
            return
        
        message_str = json.dumps(message, ensure_ascii=False)
        
        # 移除已關閉的連接
        active_connections = []
        for ws in self.websocket_connections:
            if not ws.closed:
                try:
                    await ws.send_str(message_str)
                    active_connections.append(ws)
                except Exception as e:
                    self.logger.warning(f"發送 WebSocket 消息失敗: {e}")
        
        self.websocket_connections = active_connections
    
    # Web 處理器
    async def index_handler(self, request: Request) -> Response:
        """首頁處理器"""
        return web.Response(
            text="監控儀表板首頁 - 請訪問 /dashboard",
            content_type='text/html; charset=utf-8'
        )
    
    async def dashboard_handler(self, request: Request) -> Response:
        """儀表板頁面處理器"""
        # 簡單的 HTML 頁面
        html_content = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代理監控儀表板</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        .metric-label {
            color: #666;
            margin-top: 5px;
        }
        .alerts-section {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .alert {
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }
        .alert.warning {
            background-color: #fff3cd;
            border-color: #ffc107;
        }
        .alert.error {
            background-color: #f8d7da;
            border-color: #dc3545;
        }
        .alert.critical {
            background-color: #f5c6cb;
            border-color: #721c24;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online {
            background-color: #28a745;
        }
        .status-offline {
            background-color: #dc3545;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            height: 300px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>代理監控儀表板</h1>
            <p>實時監控代理系統狀態和性能</p>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="total-proxies">-</div>
                <div class="metric-label">總代理數</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-proxies">-</div>
                <div class="metric-label">活躍代理</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="validation-rate">-</div>
                <div class="metric-label">驗證成功率</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="avg-response-time">-</div>
                <div class="metric-label">平均響應時間 (ms)</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">
                    <span class="status-indicator" id="etl-status-indicator"></span>
                    <span id="etl-status">-</span>
                </div>
                <div class="metric-label">ETL 管道狀態</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="memory-usage">-</div>
                <div class="metric-label">記憶體使用 (MB)</div>
            </div>
        </div>
        
        <div class="alerts-section">
            <h3>系統警報</h3>
            <div id="alerts-container">
                <p>暫無警報</p>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>性能趨勢圖</h3>
            <p>圖表功能需要整合 Chart.js 或其他圖表庫</p>
        </div>
    </div>
    
    <script>
        // WebSocket 連接
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        
        ws.onopen = function(event) {
            console.log('WebSocket 連接已建立');
        };
        
        ws.onmessage = function(event) {
            const message = JSON.parse(event.data);
            
            if (message.type === 'metrics_update') {
                updateMetrics(message.data);
            } else if (message.type === 'new_alert') {
                addAlert(message.data);
            }
        };
        
        ws.onclose = function(event) {
            console.log('WebSocket 連接已關閉');
            // 嘗試重新連接
            setTimeout(() => {
                location.reload();
            }, 5000);
        };
        
        function updateMetrics(metrics) {
            document.getElementById('total-proxies').textContent = metrics.total_proxies;
            document.getElementById('active-proxies').textContent = metrics.active_proxies;
            document.getElementById('validation-rate').textContent = (metrics.validation_success_rate * 100).toFixed(1) + '%';
            document.getElementById('avg-response-time').textContent = Math.round(metrics.avg_response_time);
            document.getElementById('etl-status').textContent = metrics.etl_pipeline_status;
            document.getElementById('memory-usage').textContent = Math.round(metrics.memory_usage_mb);
            
            // 更新狀態指示器
            const statusIndicator = document.getElementById('etl-status-indicator');
            if (metrics.etl_pipeline_status === 'running') {
                statusIndicator.className = 'status-indicator status-online';
            } else {
                statusIndicator.className = 'status-indicator status-offline';
            }
        }
        
        function addAlert(alert) {
            const alertsContainer = document.getElementById('alerts-container');
            
            // 移除 "暫無警報" 消息
            if (alertsContainer.children.length === 1 && alertsContainer.children[0].tagName === 'P') {
                alertsContainer.innerHTML = '';
            }
            
            const alertElement = document.createElement('div');
            alertElement.className = `alert ${alert.severity}`;
            alertElement.innerHTML = `
                <strong>${alert.rule_name}</strong><br>
                ${alert.message}<br>
                <small>${new Date(alert.timestamp).toLocaleString('zh-TW')}</small>
            `;
            
            alertsContainer.insertBefore(alertElement, alertsContainer.firstChild);
        }
        
        // 初始載入數據
        fetch('/api/metrics')
            .then(response => response.json())
            .then(data => updateMetrics(data))
            .catch(error => console.error('載入指標失敗:', error));
        
        // 載入現有警報
        fetch('/api/alerts')
            .then(response => response.json())
            .then(alerts => {
                alerts.forEach(alert => addAlert(alert));
            })
            .catch(error => console.error('載入警報失敗:', error));
    </script>
</body>
</html>
        """
        
        return web.Response(
            text=html_content,
            content_type='text/html; charset=utf-8'
        )
    
    # API 處理器
    async def get_metrics_handler(self, request: Request) -> Response:
        """獲取當前指標"""
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            return web.json_response(latest_metrics.to_dict())
        else:
            # 返回預設指標
            default_metrics = await self._collect_system_metrics()
            return web.json_response(default_metrics.to_dict())
    
    async def get_metrics_history_handler(self, request: Request) -> Response:
        """獲取指標歷史"""
        # 獲取查詢參數
        hours = int(request.query.get('hours', 1))
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # 過濾歷史數據
        filtered_metrics = [
            metrics.to_dict() for metrics in self.metrics_history
            if metrics.timestamp > cutoff_time
        ]
        
        return web.json_response(filtered_metrics)
    
    async def get_proxies_handler(self, request: Request) -> Response:
        """獲取代理列表"""
        # 這裡應該從數據庫獲取實際的代理數據
        # 暫時返回模擬數據
        proxies = [
            {
                'id': 1,
                'host': '192.168.1.1',
                'port': 8080,
                'protocol': 'HTTP',
                'status': 'active',
                'response_time': 1500,
                'last_checked': datetime.now().isoformat()
            },
            {
                'id': 2,
                'host': '10.0.0.1',
                'port': 3128,
                'protocol': 'HTTPS',
                'status': 'inactive',
                'response_time': None,
                'last_checked': (datetime.now() - timedelta(hours=1)).isoformat()
            }
        ]
        
        return web.json_response(proxies)
    
    async def get_alerts_handler(self, request: Request) -> Response:
        """獲取警報列表"""
        # 獲取查詢參數
        acknowledged = request.query.get('acknowledged')
        
        alerts = self.alerts
        if acknowledged is not None:
            acknowledged_bool = acknowledged.lower() == 'true'
            alerts = [alert for alert in alerts if alert.acknowledged == acknowledged_bool]
        
        return web.json_response([alert.to_dict() for alert in alerts])
    
    async def acknowledge_alert_handler(self, request: Request) -> Response:
        """確認警報"""
        alert_id = request.match_info['alert_id']
        
        # 查找並確認警報
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                
                # 廣播更新
                await self._broadcast_update({
                    'type': 'alert_acknowledged',
                    'data': alert.to_dict()
                })
                
                return web.json_response({'success': True})
        
        return web.json_response({'error': '警報未找到'}, status=404)
    
    async def get_system_status_handler(self, request: Request) -> Response:
        """獲取系統狀態"""
        status = {
            'dashboard_uptime': time.time(),
            'etl_pipeline_running': self.etl_pipeline is not None,
            'validator_active': self.validator is not None,
            'websocket_connections': len(self.websocket_connections),
            'total_alerts': len(self.alerts),
            'unacknowledged_alerts': len([a for a in self.alerts if not a.acknowledged])
        }
        
        return web.json_response(status)
    
    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """WebSocket 處理器"""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_connections.append(ws)
        self.logger.info(f"新的 WebSocket 連接，總連接數: {len(self.websocket_connections)}")
        
        try:
            # 發送初始數據
            if self.metrics_history:
                await ws.send_str(json.dumps({
                    'type': 'metrics_update',
                    'data': self.metrics_history[-1].to_dict()
                }, ensure_ascii=False))
            
            # 處理客戶端消息
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        # 處理客戶端請求
                        if data.get('type') == 'ping':
                            await ws.send_str(json.dumps({'type': 'pong'}))
                    except json.JSONDecodeError:
                        pass
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f'WebSocket 錯誤: {ws.exception()}')
                    break
        
        except Exception as e:
            self.logger.error(f"WebSocket 處理錯誤: {e}")
        
        finally:
            if ws in self.websocket_connections:
                self.websocket_connections.remove(ws)
            self.logger.info(f"WebSocket 連接關閉，剩餘連接數: {len(self.websocket_connections)}")
        
        return ws
    
    def set_etl_pipeline(self, pipeline: ProxyETLPipeline) -> None:
        """設置 ETL 管道引用"""
        self.etl_pipeline = pipeline
    
    def set_validator(self, validator: ProxyDataValidator) -> None:
        """設置驗證器引用"""
        self.validator = validator


# 便利函數
async def start_monitoring_dashboard(
    host: str = '0.0.0.0',
    port: int = 8888,
    etl_pipeline: Optional[ProxyETLPipeline] = None,
    validator: Optional[ProxyDataValidator] = None
) -> MonitoringDashboard:
    """啟動監控儀表板的便利函數
    
    Args:
        host: 主機地址
        port: 端口號
        etl_pipeline: ETL 管道實例
        validator: 驗證器實例
        
    Returns:
        MonitoringDashboard: 儀表板實例
    """
    dashboard = MonitoringDashboard(host, port)
    
    if etl_pipeline:
        dashboard.set_etl_pipeline(etl_pipeline)
    
    if validator:
        dashboard.set_validator(validator)
    
    await dashboard.start()
    return dashboard


if __name__ == "__main__":
    # 測試用例
    async def main():
        dashboard = MonitoringDashboard()
        
        try:
            await dashboard.start()
            print(f"監控儀表板已啟動: http://{dashboard.host}:{dashboard.port}/dashboard")
            
            # 保持運行
            while True:
                await asyncio.sleep(1)
        
        except KeyboardInterrupt:
            print("正在停止儀表板...")
        
        finally:
            await dashboard.stop()
    
    asyncio.run(main())