"""代理獲取器模組

提供多種代理獲取方式，包括：
- 多種代理來源集成
- 手動網站爬取（備用）
- 本地文件導入
- API 接口獲取
"""

import asyncio
import aiohttp
import json
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import logging
from pathlib import Path

from .models import ProxyNode, ProxyProtocol, ProxyAnonymity, ProxyStatus
from prometheus_client import Counter
from .api_shared import FETCH_SOURCE_COUNT  # reuse existing counter
from .config import get_config

logger = logging.getLogger(__name__)

# 使用 api_shared.FETCH_SOURCE_COUNT 作為統一計數器


class ProxyFetcher(ABC):
    """代理獲取器基類"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.last_fetch_time: Optional[datetime] = None
        self.total_fetched = 0
        self.fetch_errors = 0
    
    @abstractmethod
    async def fetch_proxies(self, limit: Optional[int] = None) -> List[ProxyNode]:
        """獲取代理列表
        
        Args:
            limit: 限制獲取數量
            
        Returns:
            代理節點列表
        """
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "last_fetch_time": self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            "total_fetched": self.total_fetched,
            "fetch_errors": self.fetch_errors
        }


# FreeProxyFetcher 類已移除，改用其他代理來源


class JsonFileFetcher(ProxyFetcher):
    """JSON 文件代理獲取器"""
    
    def __init__(self, file_path: str):
        super().__init__(f"json-file-{Path(file_path).name}")
        self.file_path = Path(file_path)
    
    async def fetch_proxies(self, limit: Optional[int] = None) -> List[ProxyNode]:
        """從JSON文件獲取代理"""
        if not self.file_path.exists():
            logger.warning(f"代理文件不存在: {self.file_path}")
            return []
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            proxies = []
            proxy_list = data.get("proxies", []) if isinstance(data, dict) else data
            
            for proxy_data in proxy_list:
                if isinstance(proxy_data, str):
                    # 格式: "ip:port"
                    proxy_node = self._parse_simple_proxy(proxy_data)
                elif isinstance(proxy_data, dict):
                    # 格式: {"host": "ip", "port": port, ...}
                    proxy_node = ProxyNode.from_dict(proxy_data)
                else:
                    continue
                
                if proxy_node:
                    proxy_node.source = self.name
                    proxies.append(proxy_node)
                
                if limit and len(proxies) >= limit:
                    break
            
            self.last_fetch_time = datetime.now()
            self.total_fetched += len(proxies)
            
            logger.info(f"✅ 從 {self.file_path.name} 獲取到 {len(proxies)} 個代理")
            return proxies
            
        except Exception as e:
            logger.error(f"❌ 讀取代理文件失敗 {self.file_path}: {e}")
            self.fetch_errors += 1
            return []
    
    def _parse_simple_proxy(self, proxy_str: str) -> Optional[ProxyNode]:
        """解析簡單的代理字符串"""
        try:
            host, port_str = proxy_str.split(":")
            port = int(port_str)
            
            return ProxyNode(
                host=host.strip(),
                port=port,
                protocol=ProxyProtocol.HTTP,
                status=ProxyStatus.INACTIVE,
                source=self.name
            )
        except Exception as e:
            logger.warning(f"解析代理字符串失敗 {proxy_str}: {e}")
            return None


class WebScrapeFetcher(ProxyFetcher):
    """網站爬取代理獲取器（備用方案）"""
    
    def __init__(self, name: str, url: str, parser_func=None):
        super().__init__(f"web-scrape-{name}")
        self.url = url
        self.parser_func = parser_func
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def fetch_proxies(self, limit: Optional[int] = None) -> List[ProxyNode]:
        """從網站爬取代理"""
        if not self.parser_func:
            logger.warning(f"網站 {self.url} 沒有配置解析函數")
            return []
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
            
            async with self.session.get(self.url) as response:
                if response.status == 200:
                    content = await response.text()
                    proxies = await self.parser_func(content)
                    
                    # 設置來源
                    for proxy in proxies:
                        proxy.source = self.name
                    
                    self.last_fetch_time = datetime.now()
                    self.total_fetched += len(proxies)
                    
                    logger.info(f"✅ 從 {self.url} 爬取到 {len(proxies)} 個代理")
                    return proxies[:limit] if limit else proxies
                else:
                    logger.warning(f"網站響應錯誤 {self.url}: {response.status}")
                    self.fetch_errors += 1
                    return []
                    
        except Exception as e:
            logger.error(f"❌ 爬取網站失敗 {self.url}: {e}")
            self.fetch_errors += 1
            return []
    
    async def close(self):
        """關閉會話"""
        if self.session:
            await self.session.close()
            self.session = None


class ProxyFetcherManager:
    """代理獲取器管理器
    
    統一管理多個代理獲取器，支援並發獲取和結果聚合。
    整合了高級獲取器功能。
    """
    
    def __init__(self):
        self.fetchers: List[ProxyFetcher] = []
        self.advanced_manager: Optional[AdvancedProxyFetcherManager] = None
        self._setup_default_fetchers()
        
        # 延遲初始化高級獲取器
        self._init_advanced_fetchers()
    
    def _setup_default_fetchers(self):
        """設置默認的獲取器"""
        # 添加本地JSON文件獲取器
        json_file_path = Path("proxy_list.json")
        if json_file_path.exists():
            self.add_fetcher(JsonFileFetcher(str(json_file_path)))
    
    def _init_advanced_fetchers(self):
        """初始化高級獲取器。"""
        try:
            # 延遲導入以避免循環導入
            from .advanced_fetchers import AdvancedProxyFetcherManager
            
            config = get_config()
            self.advanced_manager = AdvancedProxyFetcherManager(config.api)
            
            logger.info(f"已初始化高級獲取器管理器")
            
        except Exception as e:
            logger.error(f"初始化高級獲取器失敗: {e}")
    
    def add_fetcher(self, fetcher: ProxyFetcher):
        """添加獲取器"""
        self.fetchers.append(fetcher)
        logger.info(f"✅ 添加代理獲取器: {fetcher.name}")
    
    def remove_fetcher(self, name: str) -> bool:
        """移除獲取器"""
        for i, fetcher in enumerate(self.fetchers):
            if fetcher.name == name:
                self.fetchers.pop(i)
                logger.info(f"✅ 移除代理獲取器: {name}")
                return True
        return False
    
    def enable_fetcher(self, name: str) -> bool:
        """啟用獲取器"""
        for fetcher in self.fetchers:
            if fetcher.name == name:
                fetcher.enabled = True
                return True
        return False
    
    def disable_fetcher(self, name: str) -> bool:
        """禁用獲取器"""
        for fetcher in self.fetchers:
            if fetcher.name == name:
                fetcher.enabled = False
                return True
        return False
    
    async def fetch_all_proxies(self, limit_per_fetcher: Optional[int] = None) -> List[ProxyNode]:
        """從所有啟用的獲取器獲取代理"""
        all_proxies = []
        
        # 從傳統獲取器獲取
    for fetcher in self.fetchers:
            if not fetcher.enabled:
                continue
            
            try:
        proxies = await fetcher.fetch_proxies(limit_per_fetcher)
        all_proxies.extend(proxies)
                outcome = "success" if proxies else "empty"
                FETCH_SOURCE_COUNT.labels(source=fetcher.name, outcome=outcome).inc()
        logger.info(f"✅ {fetcher.name} 獲取到 {len(proxies)} 個代理")
            except Exception as e:
                logger.error(f"❌ {fetcher.name} 獲取失敗: {e}")
                fetcher.fetch_errors += 1
                FETCH_SOURCE_COUNT.labels(source=fetcher.name, outcome="error").inc()
        
        # 從高級獲取器獲取
    if self.advanced_manager:
            try:
        advanced_proxies = await self.advanced_manager.fetch_all_proxies()
        all_proxies.extend(advanced_proxies)
                outcome = "success" if advanced_proxies else "empty"
                FETCH_SOURCE_COUNT.labels(source="advanced", outcome=outcome).inc()
        logger.info(f"✅ 高級獲取器獲取到 {len(advanced_proxies)} 個代理")
            except Exception as e:
                logger.error(f"❌ 高級獲取器失敗: {e}")
                FETCH_SOURCE_COUNT.labels(source="advanced", outcome="error").inc()
        
        # 去重（基於 host:port）
        unique_proxies = {}
        for proxy in all_proxies:
            key = f"{proxy.host}:{proxy.port}"
            if key not in unique_proxies:
                unique_proxies[key] = proxy
        
        result = list(unique_proxies.values())
        logger.info(f"✅ 總共獲取到 {len(result)} 個唯一代理")
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取所有獲取器的統計信息"""
        stats = {
            "total_fetchers": len(self.fetchers),
            "enabled_fetchers": len([f for f in self.fetchers if f.enabled]),
            "fetchers": [f.get_stats() for f in self.fetchers]
        }
        
        # 添加高級獲取器統計
        if self.advanced_manager:
            stats["advanced_fetchers"] = self.advanced_manager.get_stats()
        
        return stats
    
    async def close(self):
        """關閉所有獲取器"""
        for fetcher in self.fetchers:
            if hasattr(fetcher, 'close'):
                await fetcher.close()
        
        if self.advanced_manager:
            await self.advanced_manager.close()