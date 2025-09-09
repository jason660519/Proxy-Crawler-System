#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
優化模組

此模組提供系統性能優化功能，包括：
- 智能緩存管理
- 資源池化
- 並發處理優化
- 記憶體管理
- 自動性能調優

主要組件：
- PerformanceOptimizer: 性能優化器主類
- SmartCache: 智能緩存實現
- ResourcePool: 通用資源池
- ConcurrencyManager: 並發管理器
- ConnectionPool: 連接池實現
"""

# 導入核心優化組件
from .performance_optimizer import (
    # 主要類
    PerformanceOptimizer,
    SmartCache,
    ResourcePool,
    ConcurrencyManager,
    ConnectionPool,
    
    # 配置類
    CacheConfig,
    ResourcePoolConfig,
    ConcurrencyConfig,
    
    # 數據類
    CacheEntry,
    CacheStatistics,
    
    # 枚舉
    CacheStrategy,
    OptimizationLevel,
    ResourceType,
    
    # 裝飾器
    cached,
    
    # 全局函數
    get_global_optimizer
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Proxy Crawler System Team"

# 導出的公共接口
__all__ = [
    # 主要類
    "PerformanceOptimizer",
    "SmartCache",
    "ResourcePool",
    "ConcurrencyManager",
    "ConnectionPool",
    
    # 配置類
    "CacheConfig",
    "ResourcePoolConfig",
    "ConcurrencyConfig",
    
    # 數據類
    "CacheEntry",
    "CacheStatistics",
    
    # 枚舉
    "CacheStrategy",
    "OptimizationLevel",
    "ResourceType",
    
    # 裝飾器
    "cached",
    
    # 便捷函數
    "get_global_optimizer",
    "create_optimizer",
    "create_cache",
    "create_connection_pool",
    "create_concurrency_manager",
    "optimize_system"
]


def create_optimizer(level: OptimizationLevel = OptimizationLevel.BALANCED) -> PerformanceOptimizer:
    """創建性能優化器的便捷函數
    
    Args:
        level: 優化級別
    
    Returns:
        PerformanceOptimizer: 性能優化器實例
    """
    return PerformanceOptimizer(level)


def create_cache(name: str = "default",
                max_size: int = 1000,
                strategy: CacheStrategy = CacheStrategy.LRU,
                ttl: float = None,
                max_memory_mb: int = 100) -> SmartCache:
    """創建智能緩存的便捷函數
    
    Args:
        name: 緩存名稱
        max_size: 最大條目數
        strategy: 緩存策略
        ttl: 默認過期時間（秒）
        max_memory_mb: 最大記憶體使用（MB）
    
    Returns:
        SmartCache: 智能緩存實例
    """
    config = CacheConfig(
        max_size=max_size,
        strategy=strategy,
        default_ttl=ttl,
        max_memory_mb=max_memory_mb
    )
    
    optimizer = get_global_optimizer()
    return optimizer.create_cache(name, config)


def create_connection_pool(connection_factory,
                          min_size: int = 1,
                          max_size: int = 10,
                          max_idle_time: float = 300.0) -> ConnectionPool:
    """創建連接池的便捷函數
    
    Args:
        connection_factory: 連接工廠函數
        min_size: 最小連接數
        max_size: 最大連接數
        max_idle_time: 最大空閒時間（秒）
    
    Returns:
        ConnectionPool: 連接池實例
    """
    config = ResourcePoolConfig(
        min_size=min_size,
        max_size=max_size,
        max_idle_time=max_idle_time
    )
    
    return ConnectionPool(config, connection_factory)


def create_concurrency_manager(max_workers: int = 10,
                              max_concurrent_tasks: int = 100,
                              task_timeout: float = 30.0,
                              enable_backpressure: bool = True) -> ConcurrencyManager:
    """創建並發管理器的便捷函數
    
    Args:
        max_workers: 最大工作線程數
        max_concurrent_tasks: 最大並發任務數
        task_timeout: 任務超時時間（秒）
        enable_backpressure: 是否啟用背壓控制
    
    Returns:
        ConcurrencyManager: 並發管理器實例
    """
    config = ConcurrencyConfig(
        max_workers=max_workers,
        max_concurrent_tasks=max_concurrent_tasks,
        task_timeout=task_timeout,
        enable_backpressure=enable_backpressure
    )
    
    optimizer = get_global_optimizer()
    return optimizer.create_concurrency_manager(config)


async def optimize_system(level: OptimizationLevel = OptimizationLevel.BALANCED,
                         enable_auto_optimization: bool = True) -> dict:
    """系統優化的便捷函數
    
    Args:
        level: 優化級別
        enable_auto_optimization: 是否啟用自動優化
    
    Returns:
        dict: 優化結果
    """
    optimizer = get_global_optimizer()
    
    # 設置優化級別
    optimizer.optimization_level = level
    optimizer._setup_default_configs()
    
    # 執行優化
    results = {}
    
    # 記憶體優化
    memory_result = await optimizer.optimize_memory()
    results['memory_optimization'] = memory_result
    
    # 自動優化
    if enable_auto_optimization:
        auto_result = await optimizer.auto_optimize()
        results['auto_optimization'] = auto_result
    
    # 獲取性能指標
    metrics = optimizer.get_performance_metrics()
    results['performance_metrics'] = metrics
    
    return results


# 預設配置常量
DEFAULT_CACHE_CONFIGS = {
    OptimizationLevel.CONSERVATIVE: CacheConfig(
        max_size=500,
        strategy=CacheStrategy.LRU,
        max_memory_mb=50,
        cleanup_interval=120.0
    ),
    OptimizationLevel.BALANCED: CacheConfig(
        max_size=1000,
        strategy=CacheStrategy.ADAPTIVE,
        max_memory_mb=100,
        cleanup_interval=60.0
    ),
    OptimizationLevel.AGGRESSIVE: CacheConfig(
        max_size=2000,
        strategy=CacheStrategy.ADAPTIVE,
        max_memory_mb=200,
        cleanup_interval=30.0
    )
}

DEFAULT_CONCURRENCY_CONFIGS = {
    OptimizationLevel.CONSERVATIVE: ConcurrencyConfig(
        max_workers=5,
        max_concurrent_tasks=50,
        task_timeout=60.0,
        enable_backpressure=True
    ),
    OptimizationLevel.BALANCED: ConcurrencyConfig(
        max_workers=10,
        max_concurrent_tasks=100,
        task_timeout=30.0,
        enable_backpressure=True
    ),
    OptimizationLevel.AGGRESSIVE: ConcurrencyConfig(
        max_workers=20,
        max_concurrent_tasks=200,
        task_timeout=15.0,
        enable_backpressure=True,
        use_process_pool=True
    )
}

DEFAULT_RESOURCE_POOL_CONFIGS = {
    OptimizationLevel.CONSERVATIVE: ResourcePoolConfig(
        min_size=1,
        max_size=5,
        max_idle_time=600.0,
        creation_timeout=60.0
    ),
    OptimizationLevel.BALANCED: ResourcePoolConfig(
        min_size=2,
        max_size=10,
        max_idle_time=300.0,
        creation_timeout=30.0
    ),
    OptimizationLevel.AGGRESSIVE: ResourcePoolConfig(
        min_size=5,
        max_size=20,
        max_idle_time=120.0,
        creation_timeout=15.0
    )
}


def get_default_cache_config(level: OptimizationLevel) -> CacheConfig:
    """獲取默認緩存配置"""
    return DEFAULT_CACHE_CONFIGS.get(level, DEFAULT_CACHE_CONFIGS[OptimizationLevel.BALANCED])


def get_default_concurrency_config(level: OptimizationLevel) -> ConcurrencyConfig:
    """獲取默認並發配置"""
    return DEFAULT_CONCURRENCY_CONFIGS.get(level, DEFAULT_CONCURRENCY_CONFIGS[OptimizationLevel.BALANCED])


def get_default_resource_pool_config(level: OptimizationLevel) -> ResourcePoolConfig:
    """獲取默認資源池配置"""
    return DEFAULT_RESOURCE_POOL_CONFIGS.get(level, DEFAULT_RESOURCE_POOL_CONFIGS[OptimizationLevel.BALANCED])


# 添加配置獲取函數到導出列表
__all__.extend([
    "DEFAULT_CACHE_CONFIGS",
    "DEFAULT_CONCURRENCY_CONFIGS",
    "DEFAULT_RESOURCE_POOL_CONFIGS",
    "get_default_cache_config",
    "get_default_concurrency_config",
    "get_default_resource_pool_config"
])


# 模組級別的便捷實例
_default_optimizer = None
_default_cache = None
_default_concurrency_manager = None


def get_default_cache() -> SmartCache:
    """獲取默認緩存實例"""
    global _default_cache
    if _default_cache is None:
        _default_cache = create_cache("default")
    return _default_cache


def get_default_concurrency_manager() -> ConcurrencyManager:
    """獲取默認並發管理器實例"""
    global _default_concurrency_manager
    if _default_concurrency_manager is None:
        _default_concurrency_manager = create_concurrency_manager()
    return _default_concurrency_manager


# 便捷的裝飾器別名
def cache(ttl: float = None, key_func=None):
    """緩存裝飾器的便捷別名"""
    return cached("default", ttl, key_func)


# 添加便捷函數到導出列表
__all__.extend([
    "get_default_cache",
    "get_default_concurrency_manager",
    "cache"
])


# 性能監控相關的便捷函數
import psutil
import time
from typing import Dict, Any


def get_system_performance() -> Dict[str, Any]:
    """獲取系統性能信息"""
    return {
        'cpu': {
            'percent': psutil.cpu_percent(interval=1),
            'count': psutil.cpu_count(),
            'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
        },
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent,
            'used': psutil.virtual_memory().used
        },
        'disk': {
            'total': psutil.disk_usage('/').total if hasattr(psutil, 'disk_usage') else 0,
            'used': psutil.disk_usage('/').used if hasattr(psutil, 'disk_usage') else 0,
            'free': psutil.disk_usage('/').free if hasattr(psutil, 'disk_usage') else 0,
            'percent': psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 0
        },
        'network': {
            'bytes_sent': psutil.net_io_counters().bytes_sent,
            'bytes_recv': psutil.net_io_counters().bytes_recv,
            'packets_sent': psutil.net_io_counters().packets_sent,
            'packets_recv': psutil.net_io_counters().packets_recv
        },
        'timestamp': time.time()
    }


def get_process_performance() -> Dict[str, Any]:
    """獲取當前進程性能信息"""
    process = psutil.Process()
    
    return {
        'pid': process.pid,
        'cpu_percent': process.cpu_percent(),
        'memory_info': process.memory_info()._asdict(),
        'memory_percent': process.memory_percent(),
        'num_threads': process.num_threads(),
        'num_fds': process.num_fds() if hasattr(process, 'num_fds') else None,
        'create_time': process.create_time(),
        'status': process.status(),
        'timestamp': time.time()
    }


# 添加性能監控函數到導出列表
__all__.extend([
    "get_system_performance",
    "get_process_performance"
])


# 模組初始化時的設置
def _initialize_module():
    """模組初始化"""
    # 可以在這裡進行一些初始化設置
    pass


# 執行模組初始化
_initialize_module()