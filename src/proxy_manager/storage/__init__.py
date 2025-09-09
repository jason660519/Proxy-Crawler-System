"""代理存儲管理模組

此模組提供Redis存儲管理功能，包括：
- 代理數據的持久化存儲
- 驗證結果的歷史記錄
- 性能統計數據管理
- 數據序列化/反序列化
- 連接池管理"""

from .redis_storage_manager import (
    RedisStorageManager,
    StorageConfig,
    ProxyData,
    ValidationData
)
from .connection_manager import (
    RedisConnectionManager,
    CircuitBreaker,
    ConnectionMetrics,
    CircuitState
)

__all__ = [
    'RedisStorageManager',
    'StorageConfig',
    'ProxyData',
    'ValidationData',
    'RedisConnectionManager',
    'CircuitBreaker',
    'ConnectionMetrics',
    'CircuitState'
]