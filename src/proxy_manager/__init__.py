"""代理管理器模組

此模組提供完整的代理管理功能，包括：
- 代理池管理
- 代理驗證和評分
- 代理輪換策略
- 性能監控
- 配置管理
- 多源代理爬取
- 統一管理介面
"""

# 核心管理組件
from .pools import ProxyPool
from .manager import ProxyManager
# from .config import ProxyConfig  # 暫時註解掉，ProxyConfig類尚未實現

# 爬蟲管理組件
from .crawler_manager import CrawlerManager

# 爬蟲實現
from .crawlers.base_crawler import BaseCrawler, ProxyNode
from .crawlers.sslproxies_org__proxy_crawler__ import SSLProxiesCrawler
from .crawlers.geonode_com__proxy_crawler__ import GeonodeCrawler
from .crawlers.free_proxy_list_net__proxy_crawler__ import FreeProxyListCrawler

# 驗證組件
from .validators.proxy_validator import ProxyValidator, ValidationResult, ProxyStatus, AnonymityLevel

__all__ = [
    # 核心管理
    'ProxyPool',
    'ProxyManager', 
    'ProxyConfig',
    
    # 爬蟲管理
    'CrawlerManager',
    
    # 爬蟲基礎
    'BaseCrawler',
    'ProxyNode',
    
    # 具體爬蟲
    'SSLProxiesCrawler',
    'GeonodeCrawler', 
    'FreeProxyListCrawler',
    
    # 驗證組件
    'ProxyValidator',
    'ValidationResult',
    'ProxyStatus',
    'AnonymityLevel'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'Jason Spider Team'
__description__ = '專業的代理爬蟲與管理系統'