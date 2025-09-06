"""代理爬蟲模組

此模組包含各種網站的代理爬蟲實現，提供統一的介面來抓取不同來源的代理伺服器資訊。

主要組件：
- BaseCrawler: 爬蟲基礎類別
- SSLProxiesOrgCrawler: sslproxies.org 爬蟲
- GeonodeCrawler: geonode.com 爬蟲
- FreeProxyListCrawler: free-proxy-list.net 爬蟲
"""

from .base_crawler import BaseCrawler, ProxyNode, UserAgentManager

__all__ = [
    'BaseCrawler',
    'ProxyCrawlerConfig', 
    'ProxyValidator',
    'DataFormatter'
]

__version__ = '1.0.0'
__author__ = 'Jason Spider Team'