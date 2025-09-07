#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
監控 API 端點

提供系統監控、告警管理和指標查詢等 API 接口
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import logging

from .system_monitor import SystemMonitor, MonitoringConfig, AlertLevel

logger = logging.getLogger(__name__)

# 創建監控 API 應用程式
monitoring_api = FastAPI(
    title="System Monitoring API",
    description="系統監控和告警管理 API",
    version="1.0.0"
)

# 初始化系統監控器
monitor = SystemMonitor()


@monitoring_api.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "system-monitoring-api",
        "timestamp": datetime.now().isoformat()
    }


@monitoring_api.get("/metrics/current")
async def get_current_metrics() -> Dict[str, Any]:
    """獲取當前系統指標"""
    try:
        metrics = monitor.get_current_metrics()
        if not metrics:
            raise HTTPException(status_code=404, detail="無可用指標數據")
        
        return {
            "success": True,
            "metrics": {
                "timestamp": metrics.timestamp.isoformat(),
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_used_mb": metrics.memory_used,
                "memory_total_mb": metrics.memory_total,
                "disk_percent": metrics.disk_percent,
                "disk_used_gb": metrics.disk_used,
                "disk_total_gb": metrics.disk_total,
                "network_sent_bytes": metrics.network_sent,
                "network_recv_bytes": metrics.network_recv,
                "active_connections": metrics.active_connections,
                "proxy_count": metrics.proxy_count,
                "api_requests_per_minute": metrics.api_requests_per_minute,
                "error_rate": metrics.error_rate
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取當前指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取指標失敗: {str(e)}")


@monitoring_api.get("/metrics/history")
async def get_metrics_history(hours: int = 24) -> Dict[str, Any]:
    """獲取指標歷史數據
    
    Args:
        hours: 歷史數據小時數
    """
    try:
        history = monitor.get_metrics_history(hours)
        
        # 轉換為 JSON 可序列化格式
        metrics_data = []
        for metrics in history:
            metrics_data.append({
                "timestamp": metrics.timestamp.isoformat(),
                "cpu_percent": metrics.cpu_percent,
                "memory_percent": metrics.memory_percent,
                "memory_used_mb": metrics.memory_used,
                "memory_total_mb": metrics.memory_total,
                "disk_percent": metrics.disk_percent,
                "disk_used_gb": metrics.disk_used,
                "disk_total_gb": metrics.disk_total,
                "network_sent_bytes": metrics.network_sent,
                "network_recv_bytes": metrics.network_recv,
                "active_connections": metrics.active_connections,
                "proxy_count": metrics.proxy_count,
                "api_requests_per_minute": metrics.api_requests_per_minute,
                "error_rate": metrics.error_rate
            })
        
        return {
            "success": True,
            "history": metrics_data,
            "period_hours": hours,
            "total_records": len(metrics_data)
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取指標歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取歷史數據失敗: {str(e)}")


@monitoring_api.get("/alerts/active")
async def get_active_alerts() -> Dict[str, Any]:
    """獲取活躍告警"""
    try:
        alerts = monitor.get_active_alerts()
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved
            })
        
        return {
            "success": True,
            "alerts": alert_data,
            "total_count": len(alert_data)
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取活躍告警失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取告警失敗: {str(e)}")


@monitoring_api.get("/alerts/history")
async def get_alert_history(hours: int = 24) -> Dict[str, Any]:
    """獲取告警歷史
    
    Args:
        hours: 歷史數據小時數
    """
    try:
        alerts = monitor.get_alert_history(hours)
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "id": alert.id,
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            })
        
        return {
            "success": True,
            "alerts": alert_data,
            "period_hours": hours,
            "total_count": len(alert_data)
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取告警歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取告警歷史失敗: {str(e)}")


@monitoring_api.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str) -> Dict[str, Any]:
    """解決告警
    
    Args:
        alert_id: 告警 ID
    """
    try:
        monitor.resolve_alert(alert_id)
        
        return {
            "success": True,
            "message": f"告警 {alert_id} 已解決",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 解決告警失敗: {e}")
        raise HTTPException(status_code=500, detail=f"解決告警失敗: {str(e)}")


@monitoring_api.get("/health/status")
async def get_system_health() -> Dict[str, Any]:
    """獲取系統健康狀態"""
    try:
        health = monitor.get_system_health()
        
        return {
            "success": True,
            "health": health
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取系統健康狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取健康狀態失敗: {str(e)}")


@monitoring_api.get("/dashboard")
async def get_monitoring_dashboard() -> Dict[str, Any]:
    """獲取監控儀表板數據"""
    try:
        # 獲取當前指標
        current_metrics = monitor.get_current_metrics()
        
        # 獲取歷史數據 (最近 24 小時)
        history = monitor.get_metrics_history(24)
        
        # 獲取活躍告警
        active_alerts = monitor.get_active_alerts()
        
        # 獲取系統健康狀態
        health = monitor.get_system_health()
        
        # 計算統計數據
        if history:
            cpu_avg = sum(m.cpu_percent for m in history) / len(history)
            memory_avg = sum(m.memory_percent for m in history) / len(history)
            disk_avg = sum(m.disk_percent for m in history) / len(history)
        else:
            cpu_avg = memory_avg = disk_avg = 0
        
        # 準備儀表板數據
        dashboard_data = {
            "current_metrics": {
                "cpu_percent": current_metrics.cpu_percent if current_metrics else 0,
                "memory_percent": current_metrics.memory_percent if current_metrics else 0,
                "disk_percent": current_metrics.disk_percent if current_metrics else 0,
                "proxy_count": current_metrics.proxy_count if current_metrics else 0,
                "active_connections": current_metrics.active_connections if current_metrics else 0
            },
            "averages_24h": {
                "cpu_percent": round(cpu_avg, 2),
                "memory_percent": round(memory_avg, 2),
                "disk_percent": round(disk_avg, 2)
            },
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
                "warning_count": len([a for a in active_alerts if a.level == AlertLevel.WARNING])
            },
            "system_health": health,
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "dashboard": dashboard_data
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取監控儀表板失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取儀表板失敗: {str(e)}")


@monitoring_api.post("/config/update")
async def update_monitoring_config(
    config_data: Dict[str, Any]
) -> Dict[str, Any]:
    """更新監控配置
    
    Args:
        config_data: 配置數據
    """
    try:
        # 更新配置
        if "cpu_threshold" in config_data:
            monitor.config.cpu_threshold = config_data["cpu_threshold"]
        if "memory_threshold" in config_data:
            monitor.config.memory_threshold = config_data["memory_threshold"]
        if "disk_threshold" in config_data:
            monitor.config.disk_threshold = config_data["disk_threshold"]
        if "error_rate_threshold" in config_data:
            monitor.config.error_rate_threshold = config_data["error_rate_threshold"]
        if "check_interval" in config_data:
            monitor.config.check_interval = config_data["check_interval"]
        
        return {
            "success": True,
            "message": "監控配置已更新",
            "config": {
                "cpu_threshold": monitor.config.cpu_threshold,
                "memory_threshold": monitor.config.memory_threshold,
                "disk_threshold": monitor.config.disk_threshold,
                "error_rate_threshold": monitor.config.error_rate_threshold,
                "check_interval": monitor.config.check_interval
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 更新監控配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新配置失敗: {str(e)}")


@monitoring_api.get("/config")
async def get_monitoring_config() -> Dict[str, Any]:
    """獲取監控配置"""
    try:
        return {
            "success": True,
            "config": {
                "cpu_threshold": monitor.config.cpu_threshold,
                "memory_threshold": monitor.config.memory_threshold,
                "disk_threshold": monitor.config.disk_threshold,
                "error_rate_threshold": monitor.config.error_rate_threshold,
                "check_interval": monitor.config.check_interval,
                "alert_cooldown": monitor.config.alert_cooldown,
                "data_retention_days": monitor.config.data_retention_days
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取監控配置失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取配置失敗: {str(e)}")

