#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proxy Crawler System - 代理爬蟲系統

一個高效、可擴展的代理IP爬取、驗證和管理系統。

主要功能：
- 多源代理IP爬取
- 智能代理驗證
- 高性能存儲管理
- 實時監控和統計
- RESTful API接口
- 系統性能優化
- 完整的監控和日誌記錄

模組結構：
- crawlers: 爬蟲模組
- validators: 驗證器模組
- storage: 存儲模組
- core: 核心功能模組
- api: API接口模組
- monitoring: 監控和日誌模組
- optimization: 性能優化模組
- utils: 工具模組
- config: 配置模組
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "Proxy Crawler System Team"
__description__ = "高效的代理IP爬取、驗證和管理系統"

# 導入核心模組
from . import config
from . import utils
from . import crawlers
from . import validators
from . import storage
from . import core
from . import api
from . import monitoring
from . import optimization

# 導入主要類和函數
from .core import (
    ProxyValidator,
    RedisStorageManager,
    TaskManager,
    CoreValidator,
    SystemIntegrator
)

from .api import (
    TaskQueueAPI,
    UnifiedAPI
)

from .monitoring import (
    SystemMonitor,
    EnhancedLogger,
    LoggerManager,
    create_system_monitor,
    create_logger,
    setup_monitoring
)

from .optimization import (
    PerformanceOptimizer,
    SmartCache,
    ConcurrencyManager,
    create_optimizer,
    create_cache,
    optimize_system
)

from .config import (
    Config,
    get_config,
    load_config
)

# 導出的公共接口
__all__ = [
    # 版本信息
    "__version__",
    "__author__",
    "__description__",
    
    # 模組
    "config",
    "utils",
    "crawlers",
    "validators",
    "storage",
    "core",
    "api",
    "monitoring",
    "optimization",
    
    # 核心類
    "ProxyValidator",
    "RedisStorageManager",
    "TaskManager",
    "CoreValidator",
    "SystemIntegrator",
    
    # API類
    "TaskQueueAPI",
    "UnifiedAPI",
    
    # 監控類
    "SystemMonitor",
    "EnhancedLogger",
    "LoggerManager",
    
    # 優化類
    "PerformanceOptimizer",
    "SmartCache",
    "ConcurrencyManager",
    
    # 配置
    "Config",
    "get_config",
    "load_config",
    
    # 便捷函數
    "create_system",
    "get_system_status",
    "create_system_monitor",
    "create_logger",
    "setup_monitoring",
    "create_optimizer",
    "create_cache",
    "optimize_system"
]


# 系統便捷函數
async def create_system(config_path: str = None, 
                       optimization_level: str = "balanced",
                       enable_monitoring: bool = True,
                       enable_optimization: bool = True) -> SystemIntegrator:
    """創建完整的代理爬蟲系統
    
    Args:
        config_path: 配置文件路徑
        optimization_level: 優化級別 (conservative/balanced/aggressive)
        enable_monitoring: 是否啟用監控
        enable_optimization: 是否啟用性能優化
    
    Returns:
        SystemIntegrator: 系統整合器實例
    """
    # 載入配置
    if config_path:
        config = load_config(config_path)
    else:
        config = get_config()
    
    # 創建系統整合器
    integrator = SystemIntegrator(config)
    
    # 設置監控
    if enable_monitoring:
        monitor = create_system_monitor()
        integrator.register_component("system_monitor", monitor)
    
    # 設置性能優化
    if enable_optimization:
        from .optimization import OptimizationLevel
        level_map = {
            "conservative": OptimizationLevel.CONSERVATIVE,
            "balanced": OptimizationLevel.BALANCED,
            "aggressive": OptimizationLevel.AGGRESSIVE
        }
        optimizer = create_optimizer(level_map.get(optimization_level, OptimizationLevel.BALANCED))
        integrator.register_component("performance_optimizer", optimizer)
    
    # 初始化系統
    await integrator.initialize()
    
    return integrator


async def get_system_status() -> dict:
    """獲取系統狀態信息
    
    Returns:
        dict: 系統狀態信息
    """
    from .optimization import get_system_performance, get_process_performance
    
    status = {
        "version": __version__,
        "system_performance": get_system_performance(),
        "process_performance": get_process_performance(),
        "timestamp": time.time()
    }
    
    return status


# 快速啟動函數
async def quick_start(proxy_sources: list = None,
                     redis_url: str = "redis://localhost:6379",
                     api_port: int = 8000,
                     enable_web_ui: bool = True) -> SystemIntegrator:
    """快速啟動代理爬蟲系統
    
    Args:
        proxy_sources: 代理源列表
        redis_url: Redis連接URL
        api_port: API服務端口
        enable_web_ui: 是否啟用Web UI
    
    Returns:
        SystemIntegrator: 系統整合器實例
    """
    # 創建基本配置
    config = Config()
    config.redis.url = redis_url
    config.api.port = api_port
    
    if proxy_sources:
        config.crawlers.sources = proxy_sources
    
    # 創建系統
    system = await create_system(
        config_path=None,
        optimization_level="balanced",
        enable_monitoring=True,
        enable_optimization=True
    )
    
    # 啟動系統
    await system.start()
    
    return system


# 導入必要的模組
import time
import asyncio
from typing import Optional, List, Dict, Any


# 添加快速啟動函數到導出列表
__all__.extend(["quick_start"])


# 系統健康檢查函數
async def health_check() -> Dict[str, Any]:
    """系統健康檢查
    
    Returns:
        dict: 健康檢查結果
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": __version__,
        "components": {}
    }
    
    try:
        # 檢查Redis連接
        from .storage import RedisStorageManager
        redis_manager = RedisStorageManager()
        redis_health = await redis_manager.health_check()
        health_status["components"]["redis"] = redis_health
        
        # 檢查系統資源
        system_perf = get_system_performance()
        health_status["components"]["system_resources"] = {
            "cpu_percent": system_perf["cpu"]["percent"],
            "memory_percent": system_perf["memory"]["percent"],
            "disk_percent": system_perf["disk"]["percent"]
        }
        
        # 判斷整體健康狀態
        if (system_perf["cpu"]["percent"] > 90 or 
            system_perf["memory"]["percent"] > 90 or
            system_perf["disk"]["percent"] > 90):
            health_status["status"] = "warning"
            
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    return health_status


# 添加健康檢查函數到導出列表
__all__.append("health_check")


# 模組級別的配置和初始化
_system_instance = None
_default_config = None


def get_system_instance() -> Optional[SystemIntegrator]:
    """獲取系統實例"""
    return _system_instance


def set_system_instance(instance: SystemIntegrator):
    """設置系統實例"""
    global _system_instance
    _system_instance = instance


def get_default_config() -> Config:
    """獲取默認配置"""
    global _default_config
    if _default_config is None:
        _default_config = get_config()
    return _default_config


# 添加實例管理函數到導出列表
__all__.extend([
    "get_system_instance",
    "set_system_instance",
    "get_default_config"
])


# 模組初始化
def _initialize_module():
    """模組初始化函數"""
    # 設置默認日誌級別
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 創建模組級別的日誌器
    logger = logging.getLogger(__name__)
    logger.info(f"Proxy Crawler System v{__version__} 已初始化")


# 執行模組初始化
_initialize_module()


# 清理函數
async def cleanup():
    """清理系統資源"""
    global _system_instance
    
    if _system_instance:
        try:
            await _system_instance.stop()
            logger = logging.getLogger(__name__)
            logger.info("系統已正常關閉")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"系統關閉時發生錯誤: {e}")
        finally:
            _system_instance = None


# 添加清理函數到導出列表
__all__.append("cleanup")


# 異常處理
class ProxyCrawlerSystemError(Exception):
    """代理爬蟲系統基礎異常類"""
    pass


class SystemNotInitializedError(ProxyCrawlerSystemError):
    """系統未初始化異常"""
    pass


class ComponentError(ProxyCrawlerSystemError):
    """組件錯誤異常"""
    pass


class ConfigurationError(ProxyCrawlerSystemError):
    """配置錯誤異常"""
    pass


# 添加異常類到導出列表
__all__.extend([
    "ProxyCrawlerSystemError",
    "SystemNotInitializedError",
    "ComponentError",
    "ConfigurationError"
])