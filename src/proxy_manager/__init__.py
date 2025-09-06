"""代理管理器模組

這個模組提供了完整的代理伺服器管理功能，包括：
- 自動代理獲取（支援多種來源）
- 智能驗證系統
- 分級代理池管理
- REST API 服務
- 實時監控和統計
"""

from .fetchers import ProxyFetcher, ProxyFetcherManager, JsonFileFetcher
from .advanced_fetchers import (
    ProxyScrapeApiFetcher, GitHubProxyFetcher, ShodanProxyFetcher,
    AdvancedProxyFetcherManager
)
from .scanner import ProxyScanner, FastPortScanner, ProxyValidator as ScannerValidator, EnhancedProxyScanner
from .zmap_integration import ZMapIntegration, IntelligentTargetDiscovery
from .geolocation_enhanced import EnhancedGeolocationDetector, GeolocationInfo, ProximityInfo, IntelligentProxyRouter
from .intelligent_detection import IntelligentProxyDetector, AnonymityLevel, ProxyType, DetectionResult, BenchmarkResult
from .quality_assessment import ProxyQualityAssessor, QualityGrade, QualityMetrics, HistoricalPerformance
from .config import (
    ProxyManagerConfig, ApiConfig, ScannerConfig, ValidationConfig as ConfigValidation
)
from .validators import ProxyValidator, ValidationConfig, BatchValidator
from .pools import ProxyPool, ProxyPoolManager, PoolConfig, PoolType
from .models import (
    ProxyNode, ProxyMetrics, ProxyFilter,
    ProxyProtocol, ProxyAnonymity, ProxySpeed, ProxyStatus
)
from .manager import ProxyManager

__version__ = "2.0.0"
__author__ = "Jason Spyder Team"

__all__ = [
    # 核心類
    'ProxyManager',
    'ProxyManagerConfig',
    
    # 數據模型
    'ProxyNode',
    'ProxyMetrics', 
    'ProxyFilter',
    'ProxyProtocol',
    'ProxyAnonymity',
    'ProxySpeed',
    'ProxyStatus',
    
    # 獲取器
    'ProxyFetcher',
    'ProxyFetcherManager',
    'JsonFileFetcher',
    
    # 高級獲取器
    'ProxyScrapeApiFetcher',
    'GitHubProxyFetcher', 
    'ShodanProxyFetcher',
    'AdvancedProxyFetcherManager',
    
    # 掃描器
    'ProxyScanner',
    'FastPortScanner',
    'ScannerValidator',
    
    # 配置
    'ApiConfig',
    'ScannerConfig',
    'ConfigValidation',
    
    # 驗證器
    'ProxyValidator',
    'ValidationConfig',
    'BatchValidator',
    
    # 池管理
    'ProxyPool',
    'ProxyPoolManager',
    'PoolConfig',
    'PoolType',
]