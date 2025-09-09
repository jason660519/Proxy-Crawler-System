#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
監控模組

此模組提供完整的系統監控和日誌記錄功能，包括：
- 系統性能監控（CPU、記憶體、磁碟、網路）
- 應用程式指標監控
- 警報和通知機制
- 結構化日誌記錄
- 日誌分析和查詢
- 監控數據持久化

主要組件：
- SystemMonitor: 系統監控器，提供基礎的系統監控功能
- EnhancedLogger: 增強日誌器，提供結構化日誌記錄
- LoggerManager: 日誌器管理器，管理多個日誌器實例
- MetricCollector: 指標收集器（如果使用擴展監控功能）
- AlertManager: 警報管理器（如果使用擴展監控功能）
"""

# 導入基礎監控組件
from .system_monitor import (
    SystemMonitor,
    SystemMetrics,
    Alert,
    AlertLevel,
    MonitoringConfig
)

# 導入日誌記錄組件
from .logger import (
    EnhancedLogger,
    LoggerManager,
    LoggerConfig,
    LogLevel,
    LogFormat,
    LogDestination,
    LogEntry,
    LogAnalyzer,
    get_logger,
    logger_manager
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Proxy Crawler System Team"

# 導出的公共接口
__all__ = [
    # 系統監控
    "SystemMonitor",
    "SystemMetrics",
    "Alert",
    "AlertLevel",
    "MonitoringConfig",
    
    # 日誌記錄
    "EnhancedLogger",
    "LoggerManager",
    "LoggerConfig",
    "LogLevel",
    "LogFormat",
    "LogDestination",
    "LogEntry",
    "LogAnalyzer",
    "get_logger",
    "logger_manager",
    
    # 便捷函數
    "create_system_monitor",
    "create_logger",
    "setup_monitoring"
]


def create_system_monitor(config: MonitoringConfig = None) -> SystemMonitor:
    """創建系統監控器的便捷函數
    
    Args:
        config: 監控配置，如果為None則使用默認配置
    
    Returns:
        SystemMonitor: 系統監控器實例
    """
    if config is None:
        config = MonitoringConfig(
            cpu_threshold=80.0,
            memory_threshold=85.0,
            disk_threshold=90.0,
            error_rate_threshold=0.1,
            check_interval=30,
            alert_cooldown=300,
            data_retention_days=7
        )
    
    return SystemMonitor(config)


def create_logger(name: str, 
                 level: LogLevel = LogLevel.INFO,
                 format_type: LogFormat = LogFormat.STRUCTURED,
                 log_file: str = None,
                 enable_console: bool = True,
                 enable_file_rotation: bool = True) -> EnhancedLogger:
    """創建日誌器的便捷函數
    
    Args:
        name: 日誌器名稱
        level: 日誌級別
        format_type: 日誌格式
        log_file: 日誌文件路徑
        enable_console: 是否啟用控制台輸出
        enable_file_rotation: 是否啟用文件輪轉
    
    Returns:
        EnhancedLogger: 增強日誌器實例
    """
    destinations = []
    
    if enable_console:
        destinations.append(LogDestination.CONSOLE)
    
    if log_file:
        if enable_file_rotation:
            destinations.append(LogDestination.ROTATING_FILE)
        else:
            destinations.append(LogDestination.FILE)
    
    config = LoggerConfig(
        name=name,
        level=level,
        format_type=format_type,
        destinations=destinations,
        log_file=log_file or f"logs/{name}.log"
    )
    
    return get_logger(name, config)


def setup_monitoring(app_name: str = "proxy_crawler",
                    log_level: LogLevel = LogLevel.INFO,
                    enable_system_monitor: bool = True,
                    enable_file_logging: bool = True,
                    log_directory: str = "logs") -> tuple[SystemMonitor, EnhancedLogger]:
    """設置完整的監控系統
    
    Args:
        app_name: 應用程式名稱
        log_level: 日誌級別
        enable_system_monitor: 是否啟用系統監控
        enable_file_logging: 是否啟用文件日誌
        log_directory: 日誌目錄
    
    Returns:
        tuple: (系統監控器, 主日誌器)
    """
    # 創建主日誌器
    main_logger = create_logger(
        name=app_name,
        level=log_level,
        format_type=LogFormat.STRUCTURED,
        log_file=f"{log_directory}/{app_name}.log" if enable_file_logging else None,
        enable_console=True,
        enable_file_rotation=True
    )
    
    # 創建系統監控器
    system_monitor = None
    if enable_system_monitor:
        monitor_config = MonitoringConfig(
            cpu_threshold=80.0,
            memory_threshold=85.0,
            disk_threshold=90.0,
            error_rate_threshold=0.05,
            check_interval=30,
            alert_cooldown=300,
            data_retention_days=7
        )
        
        system_monitor = create_system_monitor(monitor_config)
        
        # 設置監控警報回調
        def alert_callback(alert: Alert):
            """監控警報回調函數"""
            level_map = {
                AlertLevel.INFO: LogLevel.INFO,
                AlertLevel.WARNING: LogLevel.WARNING,
                AlertLevel.ERROR: LogLevel.ERROR,
                AlertLevel.CRITICAL: LogLevel.CRITICAL
            }
            
            log_level = level_map.get(alert.level, LogLevel.WARNING)
            
            if log_level == LogLevel.INFO:
                main_logger.info(f"系統監控警報: {alert.message}", 
                               alert_id=alert.id, alert_level=alert.level.value)
            elif log_level == LogLevel.WARNING:
                main_logger.warning(f"系統監控警報: {alert.message}", 
                                  alert_id=alert.id, alert_level=alert.level.value)
            elif log_level == LogLevel.ERROR:
                main_logger.error(f"系統監控警報: {alert.message}", 
                                alert_id=alert.id, alert_level=alert.level.value)
            else:  # CRITICAL
                main_logger.critical(f"系統監控警報: {alert.message}", 
                                   alert_id=alert.id, alert_level=alert.level.value)
        
        system_monitor.add_alert_callback(alert_callback)
    
    # 記錄監控系統啟動
    main_logger.info(f"監控系統已設置完成", 
                    app_name=app_name,
                    log_level=log_level.value,
                    system_monitor_enabled=enable_system_monitor,
                    file_logging_enabled=enable_file_logging)
    
    return system_monitor, main_logger


# 模組級別的便捷實例
# 這些可以在需要快速設置監控時使用
_default_monitor = None
_default_logger = None


def get_default_monitor() -> SystemMonitor:
    """獲取默認系統監控器"""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = create_system_monitor()
    return _default_monitor


def get_default_logger() -> EnhancedLogger:
    """獲取默認日誌器"""
    global _default_logger
    if _default_logger is None:
        _default_logger = create_logger("default")
    return _default_logger


# 添加便捷的日誌函數
def log_info(message: str, **kwargs):
    """記錄信息日誌的便捷函數"""
    get_default_logger().info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """記錄警告日誌的便捷函數"""
    get_default_logger().warning(message, **kwargs)


def log_error(message: str, exception: Exception = None, **kwargs):
    """記錄錯誤日誌的便捷函數"""
    get_default_logger().error(message, exception=exception, **kwargs)


def log_critical(message: str, exception: Exception = None, **kwargs):
    """記錄嚴重錯誤日誌的便捷函數"""
    get_default_logger().critical(message, exception=exception, **kwargs)


# 添加便捷函數到導出列表
__all__.extend([
    "get_default_monitor",
    "get_default_logger",
    "log_info",
    "log_warning",
    "log_error",
    "log_critical"
])