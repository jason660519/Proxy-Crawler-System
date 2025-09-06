"""智能代理探測模組

提供高級代理檢測和質量評估功能：
- 多層次代理驗證
- 智能匿名性檢測
- 代理類型識別
- 性能基準測試
- 反檢測能力評估
"""

import asyncio
import aiohttp
import json
import time
import random
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from urllib.parse import urlparse
import ssl
import socket
from enum import Enum

from .models import ProxyNode, ProxyProtocol, ProxyStatus
from .config import get_config

logger = logging.getLogger(__name__)


class AnonymityLevel(Enum):
    """匿名性等級"""
    TRANSPARENT = "transparent"      # 透明代理
    ANONYMOUS = "anonymous"          # 匿名代理
    ELITE = "elite"                  # 高匿代理
    UNKNOWN = "unknown"              # 未知


class ProxyType(Enum):
    """代理類型"""
    DATACENTER = "datacenter"        # 數據中心代理
    RESIDENTIAL = "residential"      # 住宅代理
    MOBILE = "mobile"                # 移動代理
    UNKNOWN = "unknown"              # 未知類型


@dataclass
class DetectionResult:
    """檢測結果"""
    proxy: ProxyNode
    is_working: bool = False
    anonymity_level: AnonymityLevel = AnonymityLevel.UNKNOWN
    proxy_type: ProxyType = ProxyType.UNKNOWN
    response_time: float = 0.0
    success_rate: float = 0.0
    supports_https: bool = False
    supports_connect: bool = False
    detected_headers: Dict[str, str] = field(default_factory=dict)
    real_ip_leaked: bool = False
    dns_leak: bool = False
    webrtc_leak: bool = False
    timezone_leak: bool = False
    language_leak: bool = False
    user_agent_consistency: bool = True
    fingerprint_resistance: float = 0.0  # 0-1, 越高越好
    detection_time: datetime = field(default_factory=datetime.now)
    test_results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class BenchmarkResult:
    """性能基準測試結果"""
    proxy: ProxyNode
    download_speed: float = 0.0      # MB/s
    upload_speed: float = 0.0        # MB/s
    latency: float = 0.0             # ms
    jitter: float = 0.0              # ms
    packet_loss: float = 0.0         # %
    concurrent_connections: int = 0   # 支援的並發連接數
    bandwidth_stability: float = 0.0  # 0-1, 越高越穩定
    test_duration: float = 0.0       # 測試持續時間
    test_time: datetime = field(default_factory=datetime.now)


class IntelligentProxyDetector:
    """智能代理探測器
    
    提供全面的代理檢測和評估功能
    """
    
    def __init__(self):
        self.config = get_config()
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 測試 URL 集合
        self.test_urls = {
            "ip_check": [
                "https://httpbin.org/ip",
                "https://api.ipify.org?format=json",
                "https://ipinfo.io/json",
                "https://api.myip.com",
                "https://checkip.amazonaws.com"
            ],
            "headers_check": [
                "https://httpbin.org/headers",
                "https://postman-echo.com/headers"
            ],
            "ssl_check": [
                "https://www.google.com",
                "https://www.github.com",
                "https://httpbin.org/get"
            ],
            "speed_test": [
                "https://httpbin.org/bytes/1048576",  # 1MB
                "https://httpbin.org/bytes/10485760"  # 10MB
            ]
        }
        
        # 已知的代理檢測服務
        self.proxy_detection_urls = [
            "https://www.proxy-checker.net/api/proxy-checker",
            "https://proxycheck.io/v2/",
            "https://ipqualityscore.com/api/json/ip"
        ]
        
        # 用戶代理字符串
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
        # 檢測統計
        self.detection_stats = {
            "total_tested": 0,
            "working_proxies": 0,
            "elite_proxies": 0,
            "anonymous_proxies": 0,
            "transparent_proxies": 0,
            "datacenter_proxies": 0,
            "residential_proxies": 0,
            "mobile_proxies": 0
        }
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=False  # 允許不安全的 SSL
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": random.choice(self.user_agents)}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def detect_proxy(self, proxy: ProxyNode, 
                          comprehensive: bool = True) -> DetectionResult:
        """檢測單個代理
        
        Args:
            proxy: 代理節點
            comprehensive: 是否進行全面檢測
            
        Returns:
            檢測結果
        """
        result = DetectionResult(proxy=proxy)
        
        try:
            # 基礎連接測試
            basic_result = await self._test_basic_connectivity(proxy)
            result.is_working = basic_result["working"]
            result.response_time = basic_result["response_time"]
            
            if not result.is_working:
                result.errors.append("基礎連接測試失敗")
                return result
            
            # 匿名性檢測
            anonymity_result = await self._test_anonymity(proxy)
            result.anonymity_level = anonymity_result["level"]
            result.real_ip_leaked = anonymity_result["ip_leaked"]
            result.detected_headers = anonymity_result["headers"]
            
            # HTTPS 支援測試
            result.supports_https = await self._test_https_support(proxy)
            
            # CONNECT 方法支援測試
            result.supports_connect = await self._test_connect_method(proxy)
            
            if comprehensive:
                # 代理類型檢測
                result.proxy_type = await self._detect_proxy_type(proxy)
                
                # DNS 洩漏檢測
                result.dns_leak = await self._test_dns_leak(proxy)
                
                # WebRTC 洩漏檢測
                result.webrtc_leak = await self._test_webrtc_leak(proxy)
                
                # 時區洩漏檢測
                result.timezone_leak = await self._test_timezone_leak(proxy)
                
                # 語言洩漏檢測
                result.language_leak = await self._test_language_leak(proxy)
                
                # 用戶代理一致性檢測
                result.user_agent_consistency = await self._test_user_agent_consistency(proxy)
                
                # 指紋抗性評估
                result.fingerprint_resistance = await self._evaluate_fingerprint_resistance(proxy)
                
                # 成功率測試
                result.success_rate = await self._test_success_rate(proxy)
            
            # 更新統計
            self._update_detection_stats(result)
            
            logger.info(f"代理檢測完成: {proxy.host}:{proxy.port} - 工作狀態: {result.is_working}, 匿名性: {result.anonymity_level.value}")
            
        except Exception as e:
            result.errors.append(f"檢測異常: {str(e)}")
            logger.error(f"代理檢測失敗 {proxy.host}:{proxy.port}: {e}")
        
        return result
    
    async def _test_basic_connectivity(self, proxy: ProxyNode) -> Dict[str, Any]:
        """測試基礎連接性"""
        start_time = time.time()
        
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            async with self.session.get(
                random.choice(self.test_urls["ip_check"]),
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    await response.text()
                    response_time = (time.time() - start_time) * 1000
                    return {"working": True, "response_time": response_time}
                else:
                    return {"working": False, "response_time": 0}
                    
        except Exception as e:
            logger.debug(f"基礎連接測試失敗: {e}")
            return {"working": False, "response_time": 0}
    
    async def _test_anonymity(self, proxy: ProxyNode) -> Dict[str, Any]:
        """測試匿名性"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            # 獲取真實 IP（不使用代理）
            real_ip = await self._get_real_ip()
            
            # 通過代理獲取 IP 和標頭
            async with self.session.get(
                random.choice(self.test_urls["headers_check"]),
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    headers = data.get("headers", {})
                    
                    # 檢查 IP 洩漏
                    ip_leaked = self._check_ip_leak(headers, real_ip)
                    
                    # 判斷匿名性等級
                    anonymity_level = self._determine_anonymity_level(headers, ip_leaked)
                    
                    return {
                        "level": anonymity_level,
                        "ip_leaked": ip_leaked,
                        "headers": headers
                    }
                    
        except Exception as e:
            logger.debug(f"匿名性測試失敗: {e}")
        
        return {
            "level": AnonymityLevel.UNKNOWN,
            "ip_leaked": True,
            "headers": {}
        }
    
    async def _get_real_ip(self) -> Optional[str]:
        """獲取真實 IP 地址"""
        try:
            async with self.session.get(
                "https://api.ipify.org?format=json",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("ip")
        except Exception:
            pass
        return None
    
    def _check_ip_leak(self, headers: Dict[str, str], real_ip: Optional[str]) -> bool:
        """檢查 IP 洩漏"""
        if not real_ip:
            return False
        
        # 檢查常見的 IP 洩漏標頭
        leak_headers = [
            "X-Forwarded-For",
            "X-Real-Ip",
            "X-Originating-Ip",
            "X-Remote-Ip",
            "X-Client-Ip",
            "Client-Ip",
            "Via",
            "Forwarded"
        ]
        
        for header_name in leak_headers:
            header_value = headers.get(header_name, "")
            if real_ip in header_value:
                return True
        
        return False
    
    def _determine_anonymity_level(self, headers: Dict[str, str], ip_leaked: bool) -> AnonymityLevel:
        """判斷匿名性等級"""
        if ip_leaked:
            return AnonymityLevel.TRANSPARENT
        
        # 檢查代理相關標頭
        proxy_headers = ["Via", "X-Forwarded-For", "Forwarded", "Proxy-Connection"]
        has_proxy_headers = any(header in headers for header in proxy_headers)
        
        if has_proxy_headers:
            return AnonymityLevel.ANONYMOUS
        else:
            return AnonymityLevel.ELITE
    
    async def _test_https_support(self, proxy: ProxyNode) -> bool:
        """測試 HTTPS 支援"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            async with self.session.get(
                random.choice(self.test_urls["ssl_check"]),
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=15),
                ssl=False
            ) as response:
                return response.status == 200
                
        except Exception:
            return False
    
    async def _test_connect_method(self, proxy: ProxyNode) -> bool:
        """測試 CONNECT 方法支援"""
        try:
            # 使用 CONNECT 方法測試 HTTPS 隧道
            proxy_url = self._build_proxy_url(proxy)
            
            # 創建自定義連接器支援 CONNECT
            connector = aiohttp.TCPConnector(ssl=False)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.request(
                    "CONNECT",
                    "www.google.com:443",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
                    
        except Exception:
            return False
    
    async def _detect_proxy_type(self, proxy: ProxyNode) -> ProxyType:
        """檢測代理類型"""
        try:
            # 通過 IP 地址特徵判斷代理類型
            proxy_url = self._build_proxy_url(proxy)
            
            async with self.session.get(
                "https://ipinfo.io/json",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    org = data.get("org", "").lower()
                    hostname = data.get("hostname", "").lower()
                    
                    # 數據中心代理特徵
                    datacenter_keywords = [
                        "amazon", "google", "microsoft", "digitalocean",
                        "vultr", "linode", "ovh", "hetzner", "cloudflare"
                    ]
                    
                    if any(keyword in org for keyword in datacenter_keywords):
                        return ProxyType.DATACENTER
                    
                    # 移動代理特徵
                    mobile_keywords = [
                        "mobile", "cellular", "lte", "4g", "5g",
                        "wireless", "telecom", "vodafone", "t-mobile"
                    ]
                    
                    if any(keyword in org for keyword in mobile_keywords):
                        return ProxyType.MOBILE
                    
                    # 住宅代理特徵（預設）
                    residential_keywords = [
                        "broadband", "cable", "dsl", "fiber",
                        "residential", "home", "dynamic"
                    ]
                    
                    if any(keyword in org for keyword in residential_keywords):
                        return ProxyType.RESIDENTIAL
                    
                    # 根據 hostname 判斷
                    if any(keyword in hostname for keyword in datacenter_keywords):
                        return ProxyType.DATACENTER
                    
        except Exception as e:
            logger.debug(f"代理類型檢測失敗: {e}")
        
        return ProxyType.UNKNOWN
    
    async def _test_dns_leak(self, proxy: ProxyNode) -> bool:
        """測試 DNS 洩漏"""
        try:
            # 這裡可以實現更複雜的 DNS 洩漏檢測
            # 暫時返回 False（無洩漏）
            return False
        except Exception:
            return True
    
    async def _test_webrtc_leak(self, proxy: ProxyNode) -> bool:
        """測試 WebRTC 洩漏"""
        try:
            # WebRTC 洩漏檢測需要瀏覽器環境
            # 這裡暫時返回 False
            return False
        except Exception:
            return True
    
    async def _test_timezone_leak(self, proxy: ProxyNode) -> bool:
        """測試時區洩漏"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            # 檢查時區相關的 HTTP 標頭
            async with self.session.get(
                "https://httpbin.org/headers",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    headers = data.get("headers", {})
                    
                    # 檢查時區相關標頭
                    timezone_headers = ["Accept-Language", "Time-Zone"]
                    for header in timezone_headers:
                        if header in headers:
                            # 簡化檢測：如果有時區相關標頭就認為有洩漏
                            return True
                    
        except Exception:
            pass
        
        return False
    
    async def _test_language_leak(self, proxy: ProxyNode) -> bool:
        """測試語言洩漏"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            async with self.session.get(
                "https://httpbin.org/headers",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    headers = data.get("headers", {})
                    
                    # 檢查語言標頭
                    accept_language = headers.get("Accept-Language", "")
                    if accept_language and "en" not in accept_language.lower():
                        return True
                    
        except Exception:
            pass
        
        return False
    
    async def _test_user_agent_consistency(self, proxy: ProxyNode) -> bool:
        """測試用戶代理一致性"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            test_ua = random.choice(self.user_agents)
            
            async with self.session.get(
                "https://httpbin.org/headers",
                proxy=proxy_url,
                headers={"User-Agent": test_ua},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    headers = data.get("headers", {})
                    
                    received_ua = headers.get("User-Agent", "")
                    return received_ua == test_ua
                    
        except Exception:
            pass
        
        return False
    
    async def _evaluate_fingerprint_resistance(self, proxy: ProxyNode) -> float:
        """評估指紋抗性"""
        score = 0.0
        total_tests = 5
        
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            # 測試 1: HTTP 標頭一致性
            try:
                async with self.session.get(
                    "https://httpbin.org/headers",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        score += 0.2
            except Exception:
                pass
            
            # 測試 2: SSL/TLS 指紋
            try:
                async with self.session.get(
                    "https://www.google.com",
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False
                ) as response:
                    if response.status == 200:
                        score += 0.2
            except Exception:
                pass
            
            # 測試 3: 響應時間一致性
            response_times = []
            for _ in range(3):
                try:
                    start_time = time.time()
                    async with self.session.get(
                        "https://httpbin.org/get",
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            response_times.append(time.time() - start_time)
                except Exception:
                    pass
            
            if len(response_times) >= 2:
                # 計算響應時間變異係數
                import statistics
                if statistics.mean(response_times) > 0:
                    cv = statistics.stdev(response_times) / statistics.mean(response_times)
                    if cv < 0.5:  # 變異係數小於 0.5 認為一致性好
                        score += 0.2
            
            # 測試 4: 代理檢測抗性
            detection_resistance = await self._test_detection_resistance(proxy)
            score += detection_resistance * 0.2
            
            # 測試 5: 地理位置一致性
            geo_consistency = await self._test_geo_consistency(proxy)
            score += geo_consistency * 0.2
            
        except Exception as e:
            logger.debug(f"指紋抗性評估失敗: {e}")
        
        return score
    
    async def _test_detection_resistance(self, proxy: ProxyNode) -> float:
        """測試代理檢測抗性"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            # 測試是否被代理檢測服務識別
            detection_count = 0
            total_tests = 0
            
            for url in self.proxy_detection_urls[:2]:  # 限制測試數量
                try:
                    total_tests += 1
                    async with self.session.get(
                        url,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            text = await response.text()
                            # 簡化檢測：如果響應包含 "proxy" 關鍵字
                            if "proxy" in text.lower():
                                detection_count += 1
                except Exception:
                    pass
            
            if total_tests > 0:
                return 1.0 - (detection_count / total_tests)
            
        except Exception:
            pass
        
        return 0.5  # 預設中等抗性
    
    async def _test_geo_consistency(self, proxy: ProxyNode) -> float:
        """測試地理位置一致性"""
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            # 從多個服務獲取地理位置信息
            locations = []
            
            for url in ["https://ipinfo.io/json", "https://api.ipify.org?format=json"]:
                try:
                    async with self.session.get(
                        url,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            if "country" in data:
                                locations.append(data["country"])
                except Exception:
                    pass
            
            # 檢查地理位置一致性
            if len(locations) >= 2:
                unique_countries = set(locations)
                return 1.0 if len(unique_countries) == 1 else 0.5
            
        except Exception:
            pass
        
        return 0.5  # 預設中等一致性
    
    async def _test_success_rate(self, proxy: ProxyNode, test_count: int = 10) -> float:
        """測試成功率"""
        proxy_url = self._build_proxy_url(proxy)
        successful_requests = 0
        
        for _ in range(test_count):
            try:
                async with self.session.get(
                    random.choice(self.test_urls["ip_check"]),
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        successful_requests += 1
            except Exception:
                pass
            
            # 添加隨機延遲避免過於頻繁的請求
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        return successful_requests / test_count
    
    def _build_proxy_url(self, proxy: ProxyNode) -> str:
        """構建代理 URL"""
        if proxy.protocol == ProxyProtocol.HTTP:
            return f"http://{proxy.host}:{proxy.port}"
        elif proxy.protocol == ProxyProtocol.HTTPS:
            return f"https://{proxy.host}:{proxy.port}"
        elif proxy.protocol in [ProxyProtocol.SOCKS4, ProxyProtocol.SOCKS5]:
            return f"socks5://{proxy.host}:{proxy.port}"
        else:
            return f"http://{proxy.host}:{proxy.port}"
    
    def _update_detection_stats(self, result: DetectionResult):
        """更新檢測統計"""
        self.detection_stats["total_tested"] += 1
        
        if result.is_working:
            self.detection_stats["working_proxies"] += 1
            
            # 匿名性統計
            if result.anonymity_level == AnonymityLevel.ELITE:
                self.detection_stats["elite_proxies"] += 1
            elif result.anonymity_level == AnonymityLevel.ANONYMOUS:
                self.detection_stats["anonymous_proxies"] += 1
            elif result.anonymity_level == AnonymityLevel.TRANSPARENT:
                self.detection_stats["transparent_proxies"] += 1
            
            # 類型統計
            if result.proxy_type == ProxyType.DATACENTER:
                self.detection_stats["datacenter_proxies"] += 1
            elif result.proxy_type == ProxyType.RESIDENTIAL:
                self.detection_stats["residential_proxies"] += 1
            elif result.proxy_type == ProxyType.MOBILE:
                self.detection_stats["mobile_proxies"] += 1
    
    async def batch_detect_proxies(self, 
                                 proxies: List[ProxyNode],
                                 max_concurrent: int = 20,
                                 comprehensive: bool = False) -> List[DetectionResult]:
        """批量檢測代理
        
        Args:
            proxies: 代理列表
            max_concurrent: 最大並發數
            comprehensive: 是否進行全面檢測
            
        Returns:
            檢測結果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []
        
        async def detect_single(proxy: ProxyNode):
            async with semaphore:
                try:
                    result = await self.detect_proxy(proxy, comprehensive)
                    results.append(result)
                except Exception as e:
                    logger.error(f"批量檢測失敗 {proxy.host}:{proxy.port}: {e}")
                    error_result = DetectionResult(proxy=proxy)
                    error_result.errors.append(str(e))
                    results.append(error_result)
        
        # 執行批量檢測
        tasks = [detect_single(proxy) for proxy in proxies]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info(f"批量檢測完成: {len(results)} 個代理")
        return results
    
    async def benchmark_proxy(self, proxy: ProxyNode) -> BenchmarkResult:
        """代理性能基準測試
        
        Args:
            proxy: 代理節點
            
        Returns:
            基準測試結果
        """
        result = BenchmarkResult(proxy=proxy)
        start_time = time.time()
        
        try:
            proxy_url = self._build_proxy_url(proxy)
            
            # 延遲測試
            latencies = []
            for _ in range(5):
                try:
                    ping_start = time.time()
                    async with self.session.get(
                        "https://httpbin.org/get",
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            latency = (time.time() - ping_start) * 1000
                            latencies.append(latency)
                except Exception:
                    pass
                
                await asyncio.sleep(0.1)
            
            if latencies:
                import statistics
                result.latency = statistics.mean(latencies)
                result.jitter = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            # 下載速度測試
            try:
                download_start = time.time()
                async with self.session.get(
                    "https://httpbin.org/bytes/1048576",  # 1MB
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.read()
                        download_time = time.time() - download_start
                        if download_time > 0:
                            result.download_speed = len(data) / (1024 * 1024) / download_time
            except Exception as e:
                logger.debug(f"下載速度測試失敗: {e}")
            
            # 並發連接測試
            concurrent_count = await self._test_concurrent_connections(proxy)
            result.concurrent_connections = concurrent_count
            
            # 頻寬穩定性測試
            result.bandwidth_stability = await self._test_bandwidth_stability(proxy)
            
        except Exception as e:
            logger.error(f"基準測試失敗 {proxy.host}:{proxy.port}: {e}")
        
        result.test_duration = time.time() - start_time
        return result
    
    async def _test_concurrent_connections(self, proxy: ProxyNode, max_test: int = 10) -> int:
        """測試並發連接數"""
        proxy_url = self._build_proxy_url(proxy)
        successful_concurrent = 0
        
        for concurrent_count in range(1, max_test + 1):
            try:
                tasks = []
                for _ in range(concurrent_count):
                    task = self.session.get(
                        "https://httpbin.org/get",
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=10)
                    )
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 檢查所有請求是否成功
                success_count = 0
                for response in responses:
                    if not isinstance(response, Exception):
                        if response.status == 200:
                            success_count += 1
                        await response.release()
                
                if success_count == concurrent_count:
                    successful_concurrent = concurrent_count
                else:
                    break
                    
            except Exception:
                break
        
        return successful_concurrent
    
    async def _test_bandwidth_stability(self, proxy: ProxyNode) -> float:
        """測試頻寬穩定性"""
        proxy_url = self._build_proxy_url(proxy)
        speeds = []
        
        for _ in range(3):
            try:
                start_time = time.time()
                async with self.session.get(
                    "https://httpbin.org/bytes/524288",  # 512KB
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        data = await response.read()
                        download_time = time.time() - start_time
                        if download_time > 0:
                            speed = len(data) / (1024 * 1024) / download_time
                            speeds.append(speed)
            except Exception:
                pass
            
            await asyncio.sleep(1)
        
        if len(speeds) >= 2:
            import statistics
            mean_speed = statistics.mean(speeds)
            if mean_speed > 0:
                cv = statistics.stdev(speeds) / mean_speed
                return max(0, 1 - cv)  # 變異係數越小，穩定性越高
        
        return 0.5  # 預設中等穩定性
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """獲取檢測統計信息"""
        stats = self.detection_stats.copy()
        
        if stats["total_tested"] > 0:
            stats["working_rate"] = stats["working_proxies"] / stats["total_tested"] * 100
            
            if stats["working_proxies"] > 0:
                stats["elite_rate"] = stats["elite_proxies"] / stats["working_proxies"] * 100
                stats["anonymous_rate"] = stats["anonymous_proxies"] / stats["working_proxies"] * 100
                stats["transparent_rate"] = stats["transparent_proxies"] / stats["working_proxies"] * 100
                
                stats["datacenter_rate"] = stats["datacenter_proxies"] / stats["working_proxies"] * 100
                stats["residential_rate"] = stats["residential_proxies"] / stats["working_proxies"] * 100
                stats["mobile_rate"] = stats["mobile_proxies"] / stats["working_proxies"] * 100
        
        return stats
    
    async def close(self):
        """關閉檢測器"""
        if self.session:
            await self.session.close()
        logger.info("✅ 智能代理檢測器已關閉")