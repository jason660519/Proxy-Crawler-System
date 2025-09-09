"""代理驗證器模組

此模組提供完整的代理驗證功能：
- ProxyValidator: 單個代理驗證
- BatchValidator: 批量代理驗證
- CoreValidator: 核心驗證器，提供統一接口和質量評分
- 支援多種驗證方式、匿名性檢測和質量評分
"""

from .proxy_validator import (
    ProxyValidator,
    ValidationResult,
    ProxyStatus,
    AnonymityLevel
)
from .batch_validator import BatchValidator
from .core_validator import (
    CoreValidator, 
    EnhancedValidationResult, 
    ValidationConfig, 
    ValidationLevel,
    QualityScore,
    QualityMetric
)

__all__ = [
    'ProxyValidator',
    'ValidationResult', 
    'ProxyStatus',
    'AnonymityLevel',
    'BatchValidator',
    'CoreValidator',
    'EnhancedValidationResult',
    'ValidationConfig',
    'ValidationLevel',
    'QualityScore',
    'QualityMetric'
]