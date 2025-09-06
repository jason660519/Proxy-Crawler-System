"""高級代理獲取器模組

實施代理整合第一階段：擴展數據來源
- Shodan/Censys API 整合
- ProxyScrape 多來源聚合
- GitHub 開源專案整合
- 智能代理發現與驗證
"""

import asyncio
import aiohttp
import json
import re
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator, Set
from datetime import datetime, timedelta
import logging
from pathlib import Path
import random
from urllib.parse import urljoin, urlparse

from .models import ProxyNode, ProxyProtocol, ProxyAnonymity, ProxyStatus
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ProxyFetcher(ABC):
    """代理獲取器抽象基類。"""
    
    def __init__(self, name: str = None):
        """初始化代理獲取器。
        
        Args:
            name: 獲取器名稱
        """
        self.name = name or self.__class__.__name__
        self.enabled = True  # 添加 enabled 屬性
        self.stats = {
            'total_fetched': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'last_fetch_time': None
        }
    
    @abstractmethod
    async def fetch_proxies(self, limit: int = None) -> List[ProxyNode]:
        """獲取代理列表。
        
        Args:
            limit: 限制獲取的代理數量
            
        Returns:
            代理節點列表
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取獲取器統計信息。
        
        Returns:
            統計信息字典
        """
        return self.stats.copy()


class ProxyScrapeApiFetcher(ProxyFetcher):
    """ProxyScrape API 代理獲取器
    
    支援多種格式和協議的代理獲取
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("proxyscrape-api")
        self.api_key = api_key
        self.base_url = "https://api.proxyscrape.com/v2/"
        self.session: Optional[aiohttp.ClientSession] = None
        self.total_fetched = 0
        self.fetch_errors = 0
        self.last_fetch_time = None
        
        # 支援的代理類型配置
        self.proxy_configs = [
            {"request": "get", "protocol": "http", "timeout": 10000, "country": "all"},
            {"request": "get", "protocol": "socks4", "timeout": 10000, "country": "all"},
            {"request": "get", "protocol": "socks5", "timeout": 10000, "country": "all"},
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建 HTTP 會話"""
        if not self.session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def fetch_proxies(self, limit: Optional[int] = None) -> List[ProxyNode]:
        """從 ProxyScrape API 獲取代理"""
        all_proxies = []
        session = await self._get_session()
        
        for config in self.proxy_configs:
            try:
                proxies = await self._fetch_by_protocol(session, config)
                all_proxies.extend(proxies)
                
                if limit and len(all_proxies) >= limit:
                    break
                    
                # 避免請求過於頻繁
                await asyncio.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"❌ ProxyScrape {config['protocol']} 獲取失敗: {e}")
                self.fetch_errors += 1
        
        # 去重並限制數量
        unique_proxies = self._deduplicate_proxies(all_proxies)
        result = unique_proxies[:limit] if limit else unique_proxies
        
        self.last_fetch_time = datetime.now()
        self.total_fetched += len(result)
        
        logger.info(f"✅ ProxyScrape API 獲取到 {len(result)} 個代理")
        return result
    
    async def _fetch_by_protocol(self, session: aiohttp.ClientSession, config: Dict[str, Any]) -> List[ProxyNode]:
        """按協議獲取代理"""
        params = {
            "request": config["request"],
            "protocol": config["protocol"],
            "timeout": config["timeout"],
            "country": config["country"],
            "format": "textplain"
        }
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        async with session.get(self.base_url, params=params) as response:
            if response.status == 200:
                content = await response.text()
                return self._parse_proxy_list(content, config["protocol"])
            else:
                logger.warning(f"ProxyScrape API 響應錯誤: {response.status}")
                return []
    
    def _parse_proxy_list(self, content: str, protocol: str) -> List[ProxyNode]:
        """解析代理列表"""
        proxies = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or ':' not in line:
                continue
            
            try:
                host, port_str = line.split(':', 1)
                port = int(port_str)
                
                proxy_protocol = {
                    "http": ProxyProtocol.HTTP,
                    "https": ProxyProtocol.HTTPS,
                    "socks4": ProxyProtocol.SOCKS4,
                    "socks5": ProxyProtocol.SOCKS5
                }.get(protocol.lower(), ProxyProtocol.HTTP)
                
                proxy = ProxyNode(
                    host=host.strip(),
                    port=port,
                    protocol=proxy_protocol,
                    status=ProxyStatus.INACTIVE,
                    source=self.name,
                    tags=["proxyscrape", protocol]
                )
                
                proxies.append(proxy)
                
            except ValueError as e:
                logger.debug(f"解析代理行失敗 '{line}': {e}")
                continue
        
        return proxies
    
    def _deduplicate_proxies(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """代理去重"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()
            self.session = None


class GitHubProxyFetcher(ProxyFetcher):
    """GitHub 開源代理專案獲取器
    
    從多個 GitHub 代理專案獲取代理列表
    """
    
    def __init__(self, github_token: Optional[str] = None):
        super().__init__("github-proxy")
        self.github_token = github_token
        self.session: Optional[aiohttp.ClientSession] = None
        self.total_fetched = 0
        self.fetch_errors = 0
        self.last_fetch_time = None
        
        # GitHub 代理專案配置
        self.github_sources = [
            {
                "name": "proxifly/free-proxy-list",
                "files": ["proxies/http.txt", "proxies/https.txt", "proxies/socks4.txt", "proxies/socks5.txt"],
                "format": "txt"
            },
            {
                "name": "TheSpeedX/PROXY-List",
                "files": ["http.txt", "socks4.txt", "socks5.txt"],
                "format": "txt"
            },
            {
                "name": "ShiftyTR/Proxy-List",
                "files": ["http.txt", "https.txt", "socks4.txt", "socks5.txt"],
                "format": "txt"
            }
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建 HTTP 會話"""
        if not self.session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/vnd.github.v3.raw'
            }
            
            if self.github_token:
                headers['Authorization'] = f'token {self.github_token}'
            
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def fetch_proxies(self, limit: Optional[int] = None) -> List[ProxyNode]:
        """從 GitHub 專案獲取代理"""
        all_proxies = []
        session = await self._get_session()
        
        for source in self.github_sources:
            try:
                proxies = await self._fetch_from_github_source(session, source)
                all_proxies.extend(proxies)
                
                if limit and len(all_proxies) >= limit:
                    break
                
                # 避免觸發 GitHub API 限制
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"❌ GitHub 專案 {source['name']} 獲取失敗: {e}")
                self.fetch_errors += 1
        
        # 去重並限制數量
        unique_proxies = self._deduplicate_proxies(all_proxies)
        result = unique_proxies[:limit] if limit else unique_proxies
        
        self.last_fetch_time = datetime.now()
        self.total_fetched += len(result)
        
        logger.info(f"✅ GitHub 專案獲取到 {len(result)} 個代理")
        return result
    
    async def _fetch_from_github_source(self, session: aiohttp.ClientSession, source: Dict[str, Any]) -> List[ProxyNode]:
        """從單個 GitHub 專案獲取代理"""
        all_proxies = []
        
        for file_path in source["files"]:
            try:
                url = f"https://raw.githubusercontent.com/{source['name']}/main/{file_path}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        protocol = self._extract_protocol_from_filename(file_path)
                        proxies = self._parse_github_proxy_list(content, protocol, source["name"])
                        all_proxies.extend(proxies)
                    else:
                        logger.debug(f"GitHub 文件獲取失敗 {url}: {response.status}")
                
                # 避免請求過於頻繁
                await asyncio.sleep(random.uniform(0.5, 1))
                
            except Exception as e:
                logger.debug(f"GitHub 文件處理失敗 {file_path}: {e}")
                continue
        
        return all_proxies
    
    def _extract_protocol_from_filename(self, filename: str) -> str:
        """從文件名提取協議類型"""
        filename_lower = filename.lower()
        if "socks5" in filename_lower:
            return "socks5"
        elif "socks4" in filename_lower:
            return "socks4"
        elif "https" in filename_lower:
            return "https"
        elif "http" in filename_lower:
            return "http"
        else:
            return "http"  # 默認
    
    def _parse_github_proxy_list(self, content: str, protocol: str, source_name: str) -> List[ProxyNode]:
        """解析 GitHub 代理列表"""
        proxies = []
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#') or ':' not in line:
                continue
            
            try:
                # 支援多種格式：ip:port 或 ip:port:user:pass
                parts = line.split(':')
                if len(parts) >= 2:
                    host = parts[0].strip()
                    port = int(parts[1].strip())
                    
                    proxy_protocol = {
                        "http": ProxyProtocol.HTTP,
                        "https": ProxyProtocol.HTTPS,
                        "socks4": ProxyProtocol.SOCKS4,
                        "socks5": ProxyProtocol.SOCKS5
                    }.get(protocol.lower(), ProxyProtocol.HTTP)
                    
                    proxy = ProxyNode(
                        host=host,
                        port=port,
                        protocol=proxy_protocol,
                        status=ProxyStatus.INACTIVE,
                        source=self.name,
                        tags=["github", protocol, source_name.split('/')[1]],
                        metadata={"github_source": source_name}
                    )
                    
                    proxies.append(proxy)
                
            except (ValueError, IndexError) as e:
                logger.debug(f"解析 GitHub 代理行失敗 '{line}': {e}")
                continue
        
        return proxies
    
    def _deduplicate_proxies(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """代理去重"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()
            self.session = None


class ShodanProxyFetcher(ProxyFetcher):
    """Shodan API 代理發現器
    
    使用 Shodan 搜尋引擎發現開放的代理服務
    """
    
    def __init__(self, api_key: str):
        super().__init__("shodan-proxy")
        self.api_key = api_key
        self.base_url = "https://api.shodan.io"
        self.session: Optional[aiohttp.ClientSession] = None
        self.total_fetched = 0
        self.fetch_errors = 0
        self.last_fetch_time = None
        
        # Shodan 搜尋查詢
        self.search_queries = [
            "port:8080 proxy",
            "port:3128 proxy",
            "port:1080 socks",
            "\"HTTP/1.1 200\" \"Via:\" port:8080",
            "\"HTTP/1.1 200\" \"X-Forwarded-For\" port:3128"
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建 HTTP 會話"""
        if not self.session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def fetch_proxies(self, limit: Optional[int] = None) -> List[ProxyNode]:
        """從 Shodan 發現代理"""
        all_proxies = []
        session = await self._get_session()
        
        for query in self.search_queries:
            try:
                proxies = await self._search_shodan(session, query, limit=50)
                all_proxies.extend(proxies)
                
                if limit and len(all_proxies) >= limit:
                    break
                
                # Shodan API 有速率限制
                await asyncio.sleep(random.uniform(3, 5))
                
            except Exception as e:
                logger.error(f"❌ Shodan 搜尋失敗 '{query}': {e}")
                self.fetch_errors += 1
        
        # 去重並限制數量
        unique_proxies = self._deduplicate_proxies(all_proxies)
        result = unique_proxies[:limit] if limit else unique_proxies
        
        self.last_fetch_time = datetime.now()
        self.total_fetched += len(result)
        
        logger.info(f"✅ Shodan 發現 {len(result)} 個潛在代理")
        return result
    
    async def _search_shodan(self, session: aiohttp.ClientSession, query: str, limit: int = 50) -> List[ProxyNode]:
        """執行 Shodan 搜尋"""
        params = {
            "key": self.api_key,
            "query": query,
            "limit": limit
        }
        
        url = f"{self.base_url}/shodan/host/search"
        
        async with session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_shodan_results(data, query)
            elif response.status == 401:
                logger.error("❌ Shodan API 金鑰無效")
                return []
            else:
                logger.warning(f"Shodan API 響應錯誤: {response.status}")
                return []
    
    def _parse_shodan_results(self, data: Dict[str, Any], query: str) -> List[ProxyNode]:
        """解析 Shodan 搜尋結果"""
        proxies = []
        
        for match in data.get("matches", []):
            try:
                host = match.get("ip_str")
                port = match.get("port")
                
                if not host or not port:
                    continue
                
                # 根據端口推測協議
                protocol = self._guess_protocol_from_port(port)
                
                # 提取地理位置信息
                location = match.get("location", {})
                
                proxy = ProxyNode(
                    host=host,
                    port=port,
                    protocol=protocol,
                    status=ProxyStatus.INACTIVE,
                    country=location.get("country_name"),
                    region=location.get("region_code"),
                    city=location.get("city"),
                    isp=match.get("isp"),
                    source=self.name,
                    tags=["shodan", "discovered"],
                    metadata={
                        "shodan_query": query,
                        "shodan_data": {
                            "org": match.get("org"),
                            "asn": match.get("asn"),
                            "hostnames": match.get("hostnames", []),
                            "timestamp": match.get("timestamp")
                        }
                    }
                )
                
                proxies.append(proxy)
                
            except Exception as e:
                logger.debug(f"解析 Shodan 結果失敗: {e}")
                continue
        
        return proxies
    
    def _guess_protocol_from_port(self, port: int) -> ProxyProtocol:
        """根據端口推測協議類型"""
        if port in [1080, 1081]:
            return ProxyProtocol.SOCKS5
        elif port in [1085]:
            return ProxyProtocol.SOCKS4
        elif port in [443, 8443]:
            return ProxyProtocol.HTTPS
        else:
            return ProxyProtocol.HTTP
    
    def _deduplicate_proxies(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """代理去重"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()
            self.session = None


class CensysProxyFetcher(ProxyFetcher):
    """Censys API 代理發現器
    
    使用 Censys 搜尋引擎發現開放的代理服務
    """
    
    def __init__(self, api_id: str, api_secret: str):
        super().__init__("censys-proxy")
        self.api_id = api_id
        self.api_secret = api_secret
        self.base_url = "https://search.censys.io/api/v1"
        self.session: Optional[aiohttp.ClientSession] = None
        self.total_fetched = 0
        self.fetch_errors = 0
        self.last_fetch_time = None
        
        # Censys 搜尋查詢
        self.search_queries = [
            "services.port:8080 AND services.service_name:HTTP",
            "services.port:3128 AND services.service_name:HTTP", 
            "services.port:1080 AND services.service_name:SOCKS",
            "services.port:1081 AND services.service_name:SOCKS",
            "services.port:9050 AND services.service_name:TOR"
        ]
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建 HTTP 會話"""
        if not self.session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            timeout = aiohttp.ClientTimeout(total=60)
            self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self.session
    
    async def fetch_proxies(self, limit: Optional[int] = None) -> List[ProxyNode]:
        """從 Censys 發現代理"""
        all_proxies = []
        session = await self._get_session()
        
        for query in self.search_queries:
            try:
                proxies = await self._search_censys(session, query, limit=50)
                all_proxies.extend(proxies)
                
                if limit and len(all_proxies) >= limit:
                    break
                
                # Censys API 有速率限制
                await asyncio.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"❌ Censys 搜尋失敗 '{query}': {e}")
                self.fetch_errors += 1
        
        # 去重並限制數量
        unique_proxies = self._deduplicate_proxies(all_proxies)
        result = unique_proxies[:limit] if limit else unique_proxies
        
        self.last_fetch_time = datetime.now()
        self.total_fetched += len(result)
        
        logger.info(f"✅ Censys 發現 {len(result)} 個潛在代理")
        return result
    
    async def _search_censys(self, session: aiohttp.ClientSession, query: str, limit: int = 50) -> List[ProxyNode]:
        """執行 Censys 搜尋"""
        # 使用 Basic Auth
        auth = aiohttp.BasicAuth(self.api_id, self.api_secret)
        
        params = {
            "q": query,
            "per_page": min(limit, 100),  # Censys 每頁最多 100 個結果
            "page": 1
        }
        
        url = f"{self.base_url}/hosts/search"
        
        async with session.get(url, params=params, auth=auth) as response:
            if response.status == 200:
                data = await response.json()
                return self._parse_censys_results(data, query)
            elif response.status == 401:
                logger.error("❌ Censys API 憑證無效")
                return []
            else:
                logger.warning(f"Censys API 響應錯誤: {response.status}")
                return []
    
    def _parse_censys_results(self, data: Dict[str, Any], query: str) -> List[ProxyNode]:
        """解析 Censys 搜尋結果"""
        proxies = []
        
        for result in data.get("result", {}).get("hits", []):
            try:
                host = result.get("ip")
                services = result.get("services", [])
                
                if not host or not services:
                    continue
                
                # 從服務中提取端口和協議信息
                for service in services:
                    port = service.get("port")
                    service_name = service.get("service_name", "").upper()
                    
                    if not port:
                        continue
                    
                    # 根據服務名稱推測協議
                    protocol = self._guess_protocol_from_service(service_name, port)
                    
                    # 提取地理位置信息
                    location = result.get("location", {})
                    
                    proxy = ProxyNode(
                        host=host,
                        port=port,
                        protocol=protocol,
                        status=ProxyStatus.INACTIVE,
                        country=location.get("country"),
                        region=location.get("province"),
                        city=location.get("city"),
                        isp=result.get("autonomous_system", {}).get("name"),
                        source=self.name,
                        tags=["censys", "discovered"],
                        metadata={
                            "censys_query": query,
                            "censys_data": {
                                "asn": result.get("autonomous_system", {}).get("asn"),
                                "protocols": [s.get("service_name") for s in services],
                                "timestamp": result.get("timestamp")
                            }
                        }
                    )
                    
                    proxies.append(proxy)
                
            except Exception as e:
                logger.debug(f"解析 Censys 結果失敗: {e}")
                continue
        
        return proxies
    
    def _guess_protocol_from_service(self, service_name: str, port: int) -> ProxyProtocol:
        """根據服務名稱和端口推測協議類型"""
        service_lower = service_name.lower()
        
        if "socks" in service_lower or port in [1080, 1081]:
            return ProxyProtocol.SOCKS5
        elif "tor" in service_lower or port in [9050, 9051]:
            return ProxyProtocol.SOCKS5
        elif "https" in service_lower or port in [443, 8443]:
            return ProxyProtocol.HTTPS
        else:
            return ProxyProtocol.HTTP
    
    def _deduplicate_proxies(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """代理去重"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()
            self.session = None


class AdvancedProxyFetcherManager:
    """高級代理獲取器管理器
    
    整合多個高級代理來源，提供統一的代理獲取介面
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fetchers: List[ProxyFetcher] = []
        self._setup_advanced_fetchers()
    
    def _setup_advanced_fetchers(self):
        """設置高級獲取器"""
        # ProxyScrape API
        proxyscrape_key = self.config.get("proxyscrape_api_key")
        self.add_fetcher(ProxyScrapeApiFetcher(proxyscrape_key))
        
        # GitHub 專案
        github_token = self.config.get("github_token")
        self.add_fetcher(GitHubProxyFetcher(github_token))
        
        # Shodan（需要 API 金鑰）
        shodan_key = self.config.get("shodan_api_key")
        if shodan_key:
            self.add_fetcher(ShodanProxyFetcher(shodan_key))
        else:
            logger.info("⚠️ 未配置 Shodan API 金鑰，跳過 Shodan 代理發現")
        
        # Censys（需要 API 憑證）
        censys_api_id = self.config.get("censys_api_id")
        censys_api_secret = self.config.get("censys_api_secret")
        if censys_api_id and censys_api_secret:
            self.add_fetcher(CensysProxyFetcher(censys_api_id, censys_api_secret))
        else:
            logger.info("⚠️ 未配置 Censys API 憑證，跳過 Censys 代理發現")
    
    def add_fetcher(self, fetcher: ProxyFetcher):
        """添加獲取器"""
        self.fetchers.append(fetcher)
        logger.info(f"✅ 添加高級代理獲取器: {fetcher.name}")
    
    async def fetch_all_proxies(self, limit_per_fetcher: Optional[int] = None) -> List[ProxyNode]:
        """從所有啟用的獲取器獲取代理"""
        all_proxies = []
        
        for fetcher in self.fetchers:
            if not fetcher.enabled:
                continue
            
            try:
                logger.info(f"🔄 開始從 {fetcher.name} 獲取代理...")
                proxies = await fetcher.fetch_proxies(limit_per_fetcher)
                all_proxies.extend(proxies)
                logger.info(f"✅ {fetcher.name} 獲取到 {len(proxies)} 個代理")
                
            except Exception as e:
                logger.error(f"❌ {fetcher.name} 獲取失敗: {e}")
                fetcher.fetch_errors += 1
        
        # 全局去重
        unique_proxies = self._global_deduplicate(all_proxies)
        
        logger.info(f"🎯 總共獲取到 {len(unique_proxies)} 個唯一代理")
        return unique_proxies
    
    def _global_deduplicate(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """全局代理去重"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """獲取綜合統計信息"""
        total_fetchers = len(self.fetchers)
        enabled_fetchers = len([f for f in self.fetchers if f.enabled])
        total_fetched = sum(f.total_fetched for f in self.fetchers)
        total_errors = sum(f.fetch_errors for f in self.fetchers)
        
        return {
            "total_fetchers": total_fetchers,
            "enabled_fetchers": enabled_fetchers,
            "total_proxies_fetched": total_fetched,
            "total_fetch_errors": total_errors,
            "success_rate": (total_fetched / (total_fetched + total_errors)) * 100 if (total_fetched + total_errors) > 0 else 0,
            "fetchers": [f.get_stats() for f in self.fetchers]
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            'total_fetchers': len(self.fetchers),
            'enabled_fetchers': len([f for f in self.fetchers if f.enabled]),
            'total_proxies_fetched': sum(f.total_fetched for f in self.fetchers),
            'total_fetch_errors': sum(f.fetch_errors for f in self.fetchers),
            'fetchers': [f.get_stats() for f in self.fetchers]
        }
    
    async def close(self):
        """關閉所有獲取器"""
        for fetcher in self.fetchers:
            if hasattr(fetcher, 'close'):
                await fetcher.close()
        
        logger.info("✅ 所有高級代理獲取器已關閉")