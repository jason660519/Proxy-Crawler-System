"""代理驗證器模組

此包提供代理驗證相關的功能，包括：
- 代理連通性測試
- 速度測試
- 匿名性檢測
- 地理位置驗證
- 協議支援檢測
"""

from .proxy_validator import (
    ProxyValidator,
    ValidationResult,
    ProxyStatus,
    AnonymityLevel
)

__all__ = [
    'ProxyValidator',
    'ValidationResult', 
    'ProxyStatus',
    'AnonymityLevel'
]