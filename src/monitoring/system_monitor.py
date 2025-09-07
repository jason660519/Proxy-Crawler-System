#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系統監控器

提供系統性能監控、告警和指標收集功能
"""

import asyncio
import psutil
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int  # MB
    memory_total: int  # MB
    disk_percent: float
    disk_used: int  # GB
    disk_total: int  # GB
    network_sent: int  # bytes
    network_recv: int  # bytes
    active_connections: int
    proxy_count: int
    api_requests_per_minute: int
    error_rate: float


@dataclass
class Alert:
    """告警"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class MonitoringConfig:
    """監控配置"""
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    disk_threshold: float = 90.0
    error_rate_threshold: float = 0.1
    check_interval: int = 30  # 秒
    alert_cooldown: int = 300  # 秒
    data_retention_days: int = 7


class SystemMonitor:
    """系統監控器"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.data_dir = Path("data/monitoring")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 監控狀態
        self.is_running = False
        self.metrics_history: List[SystemMetrics] = []
        self.active_alerts: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 網絡統計基準
        self._network_baseline = None
        self._last_network_check = None
        
        # 啟動監控
        self._start_monitoring()
    
    def _start_monitoring(self):
        """啟動監控"""
        if not self.is_running:
            self.is_running = True
            asyncio.create_task(self._monitoring_loop())
            logger.info("🚀 系統監控已啟動")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 收集系統指標
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # 檢查告警條件
                await self._check_alerts(metrics)
                
                # 清理舊數據
                self._cleanup_old_data()
                
                # 保存指標數據
                await self._save_metrics(metrics)
                
                # 等待下次檢查
                await asyncio.sleep(self.config.check_interval)
                
            except Exception as e:
                logger.error(f"❌ 監控循環錯誤: {e}")
                await asyncio.sleep(5)  # 錯誤後短暫等待
    
    async def _collect_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 記憶體使用
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used // (1024 * 1024)  # MB
        memory_total = memory.total // (1024 * 1024)  # MB
        
        # 磁碟使用
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_used = disk.used // (1024 * 1024 * 1024)  # GB
        disk_total = disk.total // (1024 * 1024 * 1024)  # GB
        
        # 網路統計
        network = psutil.net_io_counters()
        network_sent = network.bytes_sent
        network_recv = network.bytes_recv
        
        # 計算網路速度
        current_time = time.time()
        if self._last_network_check and self._network_baseline:
            time_diff = current_time - self._last_network_check
            if time_diff > 0:
                sent_speed = (network_sent - self._network_baseline['sent']) / time_diff
                recv_speed = (network_recv - self._network_baseline['recv']) / time_diff
            else:
                sent_speed = recv_speed = 0
        else:
            sent_speed = recv_speed = 0
        
        # 更新網路基準
        self._network_baseline = {'sent': network_sent, 'recv': network_recv}
        self._last_network_check = current_time
        
        # 活躍連接數
        connections = len(psutil.net_connections())
        
        # 模擬代理和 API 統計 (實際應用中應該從相應服務獲取)
        proxy_count = await self._get_proxy_count()
        api_requests_per_minute = await self._get_api_requests_per_minute()
        error_rate = await self._get_error_rate()
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_used=memory_used,
            memory_total=memory_total,
            disk_percent=disk_percent,
            disk_used=disk_used,
            disk_total=disk_total,
            network_sent=network_sent,
            network_recv=network_recv,
            active_connections=connections,
            proxy_count=proxy_count,
            api_requests_per_minute=api_requests_per_minute,
            error_rate=error_rate
        )
    
    async def _get_proxy_count(self) -> int:
        """獲取代理數量"""
        try:
            # 模擬從代理管理器獲取數量
            return 150  # 實際應用中應該調用代理管理器 API
        except:
            return 0
    
    async def _get_api_requests_per_minute(self) -> int:
        """獲取 API 請求數/分鐘"""
        try:
            # 模擬從 API 服務獲取統計
            return 25  # 實際應用中應該從 API 服務獲取
        except:
            return 0
    
    async def _get_error_rate(self) -> float:
        """獲取錯誤率"""
        try:
            # 模擬錯誤率計算
            return 0.02  # 2% 錯誤率
        except:
            return 0.0
    
    async def _check_alerts(self, metrics: SystemMetrics):
        """檢查告警條件"""
        alerts = []
        
        # CPU 使用率告警
        if metrics.cpu_percent > self.config.cpu_threshold:
            alerts.append(Alert(
                id=f"cpu_high_{int(time.time())}",
                level=AlertLevel.WARNING if metrics.cpu_percent < 95 else AlertLevel.CRITICAL,
                title="CPU 使用率過高",
                message=f"CPU 使用率: {metrics.cpu_percent:.1f}% (閾值: {self.config.cpu_threshold}%)",
                timestamp=datetime.now()
            ))
        
        # 記憶體使用率告警
        if metrics.memory_percent > self.config.memory_threshold:
            alerts.append(Alert(
                id=f"memory_high_{int(time.time())}",
                level=AlertLevel.WARNING if metrics.memory_percent < 95 else AlertLevel.CRITICAL,
                title="記憶體使用率過高",
                message=f"記憶體使用率: {metrics.memory_percent:.1f}% (閾值: {self.config.memory_threshold}%)",
                timestamp=datetime.now()
            ))
        
        # 磁碟使用率告警
        if metrics.disk_percent > self.config.disk_threshold:
            alerts.append(Alert(
                id=f"disk_high_{int(time.time())}",
                level=AlertLevel.WARNING if metrics.disk_percent < 95 else AlertLevel.CRITICAL,
                title="磁碟使用率過高",
                message=f"磁碟使用率: {metrics.disk_percent:.1f}% (閾值: {self.config.disk_threshold}%)",
                timestamp=datetime.now()
            ))
        
        # 錯誤率告警
        if metrics.error_rate > self.config.error_rate_threshold:
            alerts.append(Alert(
                id=f"error_rate_high_{int(time.time())}",
                level=AlertLevel.ERROR,
                title="錯誤率過高",
                message=f"錯誤率: {metrics.error_rate:.2%} (閾值: {self.config.error_rate_threshold:.2%})",
                timestamp=datetime.now()
            ))
        
        # 處理新告警
        for alert in alerts:
            await self._handle_alert(alert)
    
    async def _handle_alert(self, alert: Alert):
        """處理告警"""
        # 檢查是否已存在相同告警
        existing_alert = next(
            (a for a in self.active_alerts if a.title == alert.title and not a.resolved),
            None
        )
        
        if existing_alert:
            # 檢查冷卻時間
            time_diff = (alert.timestamp - existing_alert.timestamp).total_seconds()
            if time_diff < self.config.alert_cooldown:
                return
        
        # 添加新告警
        self.active_alerts.append(alert)
        
        # 觸發告警回調
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"❌ 告警回調執行失敗: {e}")
        
        logger.warning(f"🚨 系統告警: {alert.title} - {alert.message}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回調函數"""
        self.alert_callbacks.append(callback)
    
    def resolve_alert(self, alert_id: str):
        """解決告警"""
        for alert in self.active_alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"✅ 告警已解決: {alert.title}")
                break
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """獲取當前指標"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self, hours: int = 24) -> List[SystemMetrics]:
        """獲取指標歷史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍告警"""
        return [a for a in self.active_alerts if not a.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """獲取告警歷史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [a for a in self.active_alerts if a.timestamp >= cutoff_time]
    
    def _cleanup_old_data(self):
        """清理舊數據"""
        cutoff_time = datetime.now() - timedelta(days=self.config.data_retention_days)
        
        # 清理指標歷史
        self.metrics_history = [m for m in self.metrics_history if m.timestamp >= cutoff_time]
        
        # 清理已解決的告警
        self.active_alerts = [a for a in self.active_alerts if not a.resolved or a.timestamp >= cutoff_time]
    
    async def _save_metrics(self, metrics: SystemMetrics):
        """保存指標數據"""
        try:
            # 保存到文件
            metrics_file = self.data_dir / f"metrics_{datetime.now().strftime('%Y%m%d')}.json"
            
            # 讀取現有數據
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"metrics": []}
            
            # 添加新指標
            data["metrics"].append(asdict(metrics))
            
            # 保存數據
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
        except Exception as e:
            logger.error(f"❌ 保存指標數據失敗: {e}")
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_running = False
        logger.info("🛑 系統監控已停止")
    
    def get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        current_metrics = self.get_current_metrics()
        active_alerts = self.get_active_alerts()
        
        if not current_metrics:
            return {
                "status": "unknown",
                "message": "無可用指標數據",
                "timestamp": datetime.now().isoformat()
            }
        
        # 計算健康狀態
        health_score = 100
        issues = []
        
        if current_metrics.cpu_percent > self.config.cpu_threshold:
            health_score -= 20
            issues.append("CPU 使用率過高")
        
        if current_metrics.memory_percent > self.config.memory_threshold:
            health_score -= 20
            issues.append("記憶體使用率過高")
        
        if current_metrics.disk_percent > self.config.disk_threshold:
            health_score -= 15
            issues.append("磁碟使用率過高")
        
        if current_metrics.error_rate > self.config.error_rate_threshold:
            health_score -= 25
            issues.append("錯誤率過高")
        
        # 確定狀態
        if health_score >= 90:
            status = "healthy"
        elif health_score >= 70:
            status = "warning"
        elif health_score >= 50:
            status = "degraded"
        else:
            status = "critical"
        
        return {
            "status": status,
            "health_score": health_score,
            "issues": issues,
            "active_alerts": len(active_alerts),
            "current_metrics": asdict(current_metrics),
            "timestamp": datetime.now().isoformat()
        }
