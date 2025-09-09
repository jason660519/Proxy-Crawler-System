"""代理爬蟲基礎類別模組

此模組定義了所有代理爬蟲的基礎類別和共用功能，包含：
- 統一的爬蟲介面
- 反檢測機制
- 錯誤處理
- 數據格式化
- 速率限制
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from loguru import logger


@dataclass
class ProxyNode:
    """代理節點數據模型
    
    Attributes:
        ip: IP 地址
        port: 端口號
        protocol: 協議類型 (HTTP, HTTPS, SOCKS4, SOCKS5)
        anonymity: 匿名等級 (Elite, Anonymous, Transparent)
        country: 國家代碼
        response_time: 響應時間 (毫秒)
        last_checked: 最後檢查時間
        is_working: 是否可用
        source: 數據來源
    """
    ip: str
    port: int
    protocol: str = "HTTP"
    anonymity: str = "Unknown"
    country: str = "Unknown"
    response_time: Optional[float] = None
    last_checked: Optional[float] = None
    is_working: Optional[bool] = None
    source: str = "Unknown"
    
    def __post_init__(self):
        """初始化後處理"""
        if self.last_checked is None:
            self.last_checked = time.time()
    
    @property
    def proxy_url(self) -> str:
        """獲取代理 URL 格式"""
        protocol_value = self.protocol.value if hasattr(self.protocol, 'value') else str(self.protocol)
        protocol = protocol_value.lower()
        if protocol in ['socks4', 'socks5']:
            return f"{protocol}://{self.ip}:{self.port}"
        else:
            return f"http://{self.ip}:{self.port}"
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'ip': self.ip,
            'port': self.port,
            'protocol': self.protocol,
            'anonymity': self.anonymity,
            'country': self.country,
            'response_time': self.response_time,
            'last_checked': self.last_checked,
            'is_working': self.is_working,
            'source': self.source,
            'proxy_url': self.proxy_url
        }


class UserAgentManager:
    """User-Agent 管理器
    
    提供智能的 User-Agent 輪換機制，避免被網站檢測
    """
    
    def __init__(self):
        self.user_agents = [
            # Chrome on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            # Firefox on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
            # Edge on Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # Chrome on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            # Safari on macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        ]
        self.last_used_index = -1
    
    def get_random_ua(self) -> str:
        """獲取隨機 User-Agent"""
        return random.choice(self.user_agents)
    
    def get_next_ua(self) -> str:
        """獲取下一個 User-Agent (輪換)"""
        self.last_used_index = (self.last_used_index + 1) % len(self.user_agents)
        return self.user_agents[self.last_used_index]


class BaseCrawler(ABC):
    """代理爬蟲基礎類別
    
    所有具體的代理爬蟲都應該繼承此類別並實現抽象方法
    """
    
    def __init__(self, 
                 source_name: str,
                 base_url: str,
                 delay_range: tuple = (1.0, 3.0),
                 timeout: int = 30,
                 max_retries: int = 3):
        """
        初始化爬蟲
        
        Args:
            source_name: 數據源名稱
            base_url: 基礎 URL
            delay_range: 請求間隔範圍 (秒)
            timeout: 請求超時時間 (秒)
            max_retries: 最大重試次數
        """
        self.source_name = source_name
        self.base_url = base_url
        self.delay_range = delay_range
        self.timeout = timeout
        self.max_retries = max_retries
        
        # 初始化管理器
        self.ua_manager = UserAgentManager()
        
        # 會話配置
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 統計信息
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'proxies_found': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.close_session()
    
    async def start_session(self):
        """啟動 HTTP 會話"""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            logger.info(f"[{self.source_name}] HTTP 會話已啟動")
    
    async def close_session(self):
        """關閉 HTTP 會話"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info(f"[{self.source_name}] HTTP 會話已關閉")
    
    async def make_request(self, url: str, **kwargs) -> Optional[str]:
        """發送 HTTP 請求
        
        Args:
            url: 請求 URL
            **kwargs: 額外的請求參數
            
        Returns:
            響應內容或 None (如果失敗)
        """
        if not self.session:
            await self.start_session()
        
        headers = kwargs.pop('headers', {})
        headers['User-Agent'] = self.ua_manager.get_random_ua()
        
        for attempt in range(self.max_retries):
            try:
                self.stats['total_requests'] += 1
                
                logger.debug(f"[{self.source_name}] 請求 {url} (嘗試 {attempt + 1}/{self.max_retries})")
                
                async with self.session.get(url, headers=headers, **kwargs) as response:
                    if response.status == 200:
                        content = await response.text()
                        self.stats['successful_requests'] += 1
                        logger.debug(f"[{self.source_name}] 請求成功: {url}")
                        return content
                    else:
                        logger.warning(f"[{self.source_name}] HTTP {response.status}: {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"[{self.source_name}] 請求超時: {url} (嘗試 {attempt + 1})")
            except Exception as e:
                logger.error(f"[{self.source_name}] 請求錯誤: {url} - {str(e)} (嘗試 {attempt + 1})")
            
            # 重試前等待
            if attempt < self.max_retries - 1:
                await asyncio.sleep(random.uniform(1, 2))
        
        self.stats['failed_requests'] += 1
        logger.error(f"[{self.source_name}] 請求最終失敗: {url}")
        return None
    
    async def respect_rate_limit(self):
        """遵守速率限制"""
        delay = random.uniform(*self.delay_range)
        logger.debug(f"[{self.source_name}] 等待 {delay:.2f} 秒")
        await asyncio.sleep(delay)
    
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """解析 HTML 內容
        
        Args:
            html_content: HTML 字符串
            
        Returns:
            BeautifulSoup 對象
        """
        return BeautifulSoup(html_content, 'lxml')
    
    def validate_proxy_data(self, proxy: ProxyNode) -> bool:
        """驗證代理數據的有效性
        
        Args:
            proxy: 代理節點對象
            
        Returns:
            是否有效
        """
        # 檢查 IP 格式
        ip_parts = proxy.host.split('.')
        if len(ip_parts) != 4:
            return False
        
        try:
            for part in ip_parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
        except ValueError:
            return False
        
        # 檢查端口範圍
        if not 1 <= proxy.port <= 65535:
            return False
        
        # 檢查協議
        protocol_value = proxy.protocol.value if hasattr(proxy.protocol, 'value') else str(proxy.protocol)
        if protocol_value.upper() not in ['HTTP', 'HTTPS', 'SOCKS4', 'SOCKS5']:
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取爬蟲統計信息"""
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['duration'] = stats['end_time'] - stats['start_time']
            if stats['duration'] > 0:
                stats['requests_per_second'] = stats['total_requests'] / stats['duration']
        return stats
    
    @abstractmethod
    async def fetch_proxies(self) -> List[ProxyNode]:
        """抓取代理列表
        
        子類必須實現此方法來定義具體的抓取邏輯
        
        Returns:
            代理節點列表
        """
        pass
    
    @abstractmethod
    def parse_proxy_page(self, html_content: str) -> List[ProxyNode]:
        """解析代理頁面
        
        子類必須實現此方法來定義具體的解析邏輯
        
        Args:
            html_content: HTML 內容
            
        Returns:
            代理節點列表
        """
        pass
    
    async def crawl(self) -> List[ProxyNode]:
        """執行完整的爬蟲流程
        
        Returns:
            有效的代理節點列表
        """
        self.stats['start_time'] = time.time()
        logger.info(f"[{self.source_name}] 開始爬取代理")
        
        try:
            # 抓取代理
            proxies = await self.fetch_proxies()
            
            # 過濾有效代理
            valid_proxies = []
            for proxy in proxies:
                if self.validate_proxy_data(proxy):
                    valid_proxies.append(proxy)
                else:
                    logger.debug(f"[{self.source_name}] 無效代理: {proxy.host}:{proxy.port}")
            
            self.stats['proxies_found'] = len(valid_proxies)
            logger.info(f"[{self.source_name}] 爬取完成，找到 {len(valid_proxies)} 個有效代理")
            
            return valid_proxies
            
        except Exception as e:
            logger.error(f"[{self.source_name}] 爬取失敗: {str(e)}")
            return []
        
        finally:
            self.stats['end_time'] = time.time()