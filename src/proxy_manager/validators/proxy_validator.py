"""代理驗證器模組

此模組提供全面的代理驗證功能，包括：
- 連通性測試
- 速度測試
- 匿名性檢測
- 地理位置驗證
- 協議支援檢測

驗證器支援多種測試目標和並發驗證，確保代理的可用性和品質。
"""

import asyncio
import time
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from urllib.parse import urlparse

import aiohttp
from loguru import logger

from ..crawlers.base_crawler import ProxyNode


class ProxyStatus(Enum):
    """代理狀態枚舉"""
    WORKING = "working"
    FAILED = "failed"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class AnonymityLevel(Enum):
    """匿名等級枚舉"""
    TRANSPARENT = "transparent"  # 透明代理
    ANONYMOUS = "anonymous"      # 匿名代理
    ELITE = "elite"              # 高匿代理
    UNKNOWN = "unknown"          # 未知


@dataclass
class ValidationResult:
    """代理驗證結果"""
    proxy: ProxyNode
    status: ProxyStatus
    response_time: Optional[float] = None  # 響應時間（秒）
    anonymity_level: AnonymityLevel = AnonymityLevel.UNKNOWN
    real_ip: Optional[str] = None  # 真實IP（用於匿名性檢測）
    detected_country: Optional[str] = None  # 檢測到的國家
    supports_https: bool = False
    error_message: Optional[str] = None
    test_timestamp: Optional[float] = None
    test_url: Optional[str] = None
    
    def __post_init__(self):
        if self.test_timestamp is None:
            self.test_timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = asdict(self)
        # 轉換枚舉為字符串
        result['status'] = self.status.value
        result['anonymity_level'] = self.anonymity_level.value
        result['proxy'] = asdict(self.proxy)
        return result


class ProxyValidator:
    """代理驗證器
    
    提供全面的代理驗證功能，包括連通性、速度、匿名性等測試
    """
    
    def __init__(self, 
                 timeout: float = 10.0,
                 max_concurrent: int = 50,
                 real_ip: Optional[str] = None):
        """初始化代理驗證器
        
        Args:
            timeout: 請求超時時間（秒）
            max_concurrent: 最大並發數
            real_ip: 本機真實IP（用於匿名性檢測）
        """
        self.timeout = timeout
        self.max_concurrent = max_concurrent
        self.real_ip = real_ip
        
        # 測試目標URL列表
        self.test_urls = {
            'http': [
                'http://httpbin.org/ip',
                'http://icanhazip.com',
                'http://ipinfo.io/ip',
                'http://api.ipify.org',
            ],
            'https': [
                'https://httpbin.org/ip',
                'https://icanhazip.com',
                'https://ipinfo.io/ip',
                'https://api.ipify.org',
            ]
        }
        
        # 匿名性檢測URL
        self.anonymity_test_urls = [
            'http://httpbin.org/headers',
            'https://httpbin.org/headers',
        ]
        
        # 地理位置檢測URL
        self.geo_test_urls = [
            'http://ipinfo.io/json',
            'https://ipapi.co/json/',
        ]
        
        # 統計信息
        self.stats = {
            'total_tested': 0,
            'working': 0,
            'failed': 0,
            'timeout': 0,
            'average_response_time': 0.0
        }
    
    async def validate_proxy(self, proxy: ProxyNode, 
                           test_anonymity: bool = True,
                           test_geo: bool = True) -> ValidationResult:
        """驗證單個代理
        
        Args:
            proxy: 要驗證的代理節點
            test_anonymity: 是否測試匿名性
            test_geo: 是否測試地理位置
            
        Returns:
            驗證結果
        """
        start_time = time.time()
        
        try:
            # 構建代理URL
            proxy_url = self._build_proxy_url(proxy)
            
            # 選擇測試URL
            test_urls = self.test_urls.get('https' if proxy.protocol.upper() == 'HTTPS' else 'http', 
                                         self.test_urls['http'])
            
            # 基本連通性測試
            connectivity_result = await self._test_connectivity(proxy_url, test_urls[0])
            
            if connectivity_result['status'] != ProxyStatus.WORKING:
                return ValidationResult(
                    proxy=proxy,
                    status=connectivity_result['status'],
                    response_time=connectivity_result.get('response_time'),
                    error_message=connectivity_result.get('error'),
                    test_url=test_urls[0]
                )
            
            result = ValidationResult(
                proxy=proxy,
                status=ProxyStatus.WORKING,
                response_time=connectivity_result['response_time'],
                test_url=test_urls[0]
            )
            
            # 測試HTTPS支援
            if proxy.protocol.upper() in ['HTTP', 'HTTPS']:
                https_support = await self._test_https_support(proxy_url)
                result.supports_https = https_support
            
            # 匿名性測試
            if test_anonymity:
                anonymity_level = await self._test_anonymity(proxy_url)
                result.anonymity_level = anonymity_level
            
            # 地理位置測試
            if test_geo:
                geo_info = await self._test_geolocation(proxy_url)
                if geo_info:
                    result.detected_country = geo_info.get('country')
                    result.real_ip = geo_info.get('ip')
            
            return result
            
        except Exception as e:
            logger.error(f"驗證代理 {proxy.ip}:{proxy.port} 時發生錯誤: {str(e)}")
            return ValidationResult(
                proxy=proxy,
                status=ProxyStatus.FAILED,
                error_message=str(e)
            )
        
        finally:
            # 更新統計信息
            self.stats['total_tested'] += 1
    
    async def validate_proxies(self, proxies: List[ProxyNode], 
                             test_anonymity: bool = True,
                             test_geo: bool = False) -> List[ValidationResult]:
        """批量驗證代理
        
        Args:
            proxies: 代理列表
            test_anonymity: 是否測試匿名性
            test_geo: 是否測試地理位置
            
        Returns:
            驗證結果列表
        """
        logger.info(f"開始批量驗證 {len(proxies)} 個代理")
        
        # 創建信號量控制並發數
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def validate_with_semaphore(proxy):
            async with semaphore:
                return await self.validate_proxy(proxy, test_anonymity, test_geo)
        
        # 並發執行驗證
        tasks = [validate_with_semaphore(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"驗證代理 {proxies[i].ip}:{proxies[i].port} 時發生異常: {str(result)}")
                valid_results.append(ValidationResult(
                    proxy=proxies[i],
                    status=ProxyStatus.FAILED,
                    error_message=str(result)
                ))
            else:
                valid_results.append(result)
        
        # 更新統計信息
        self._update_stats(valid_results)
        
        logger.info(f"驗證完成，{self.stats['working']} 個可用，{self.stats['failed']} 個失敗")
        
        return valid_results
    
    def _build_proxy_url(self, proxy: ProxyNode) -> str:
        """構建代理URL
        
        Args:
            proxy: 代理節點
            
        Returns:
            代理URL字符串
        """
        protocol = proxy.protocol.lower()
        if protocol in ['socks4', 'socks5']:
            return f"{protocol}://{proxy.ip}:{proxy.port}"
        else:
            return f"http://{proxy.ip}:{proxy.port}"
    
    async def _test_connectivity(self, proxy_url: str, test_url: str) -> Dict[str, Any]:
        """測試代理連通性
        
        Args:
            proxy_url: 代理URL
            test_url: 測試目標URL
            
        Returns:
            測試結果字典
        """
        start_time = time.time()
        
        try:
            # 配置代理
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                
                # 根據代理類型配置請求
                if proxy_url.startswith('socks'):
                    # SOCKS代理需要特殊處理
                    # 這裡簡化處理，實際可能需要使用 aiohttp-socks
                    proxy = proxy_url
                else:
                    proxy = proxy_url
                
                async with session.get(test_url, proxy=proxy) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        return {
                            'status': ProxyStatus.WORKING,
                            'response_time': response_time
                        }
                    else:
                        return {
                            'status': ProxyStatus.FAILED,
                            'error': f"HTTP {response.status}"
                        }
        
        except asyncio.TimeoutError:
            return {
                'status': ProxyStatus.TIMEOUT,
                'error': 'Request timeout'
            }
        except Exception as e:
            return {
                'status': ProxyStatus.FAILED,
                'error': str(e)
            }
    
    async def _test_https_support(self, proxy_url: str) -> bool:
        """測試HTTPS支援
        
        Args:
            proxy_url: 代理URL
            
        Returns:
            是否支援HTTPS
        """
        try:
            https_test_url = 'https://httpbin.org/ip'
            result = await self._test_connectivity(proxy_url, https_test_url)
            return result['status'] == ProxyStatus.WORKING
        except Exception:
            return False
    
    async def _test_anonymity(self, proxy_url: str) -> AnonymityLevel:
        """測試代理匿名性
        
        Args:
            proxy_url: 代理URL
            
        Returns:
            匿名等級
        """
        try:
            test_url = 'http://httpbin.org/headers'
            
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                
                async with session.get(test_url, proxy=proxy_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        headers = data.get('headers', {})
                        
                        # 檢查是否洩露真實IP
                        real_ip_headers = [
                            'X-Real-IP', 'X-Forwarded-For', 'X-Originating-IP',
                            'Client-IP', 'X-Client-IP', 'Via'
                        ]
                        
                        has_real_ip = any(header in headers for header in real_ip_headers)
                        has_proxy_headers = 'Via' in headers or 'X-Forwarded-For' in headers
                        
                        if not has_real_ip and not has_proxy_headers:
                            return AnonymityLevel.ELITE
                        elif not has_real_ip:
                            return AnonymityLevel.ANONYMOUS
                        else:
                            return AnonymityLevel.TRANSPARENT
            
        except Exception as e:
            logger.debug(f"匿名性測試失敗: {str(e)}")
        
        return AnonymityLevel.UNKNOWN
    
    async def _test_geolocation(self, proxy_url: str) -> Optional[Dict[str, str]]:
        """測試代理地理位置
        
        Args:
            proxy_url: 代理URL
            
        Returns:
            地理位置信息字典或None
        """
        for test_url in self.geo_test_urls:
            try:
                connector = aiohttp.TCPConnector()
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                ) as session:
                    
                    async with session.get(test_url, proxy=proxy_url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # 提取標準化的地理信息
                            geo_info = {}
                            
                            # 處理不同API的響應格式
                            if 'country' in data:
                                geo_info['country'] = data['country']
                            elif 'country_name' in data:
                                geo_info['country'] = data['country_name']
                            
                            if 'ip' in data:
                                geo_info['ip'] = data['ip']
                            elif 'query' in data:
                                geo_info['ip'] = data['query']
                            
                            if 'city' in data:
                                geo_info['city'] = data['city']
                            
                            if 'region' in data:
                                geo_info['region'] = data['region']
                            elif 'regionName' in data:
                                geo_info['region'] = data['regionName']
                            
                            return geo_info
                            
            except Exception as e:
                logger.debug(f"地理位置測試失敗 ({test_url}): {str(e)}")
                continue
        
        return None
    
    def _update_stats(self, results: List[ValidationResult]):
        """更新統計信息
        
        Args:
            results: 驗證結果列表
        """
        working_count = 0
        failed_count = 0
        timeout_count = 0
        total_response_time = 0.0
        valid_response_count = 0
        
        for result in results:
            if result.status == ProxyStatus.WORKING:
                working_count += 1
                if result.response_time:
                    total_response_time += result.response_time
                    valid_response_count += 1
            elif result.status == ProxyStatus.FAILED:
                failed_count += 1
            elif result.status == ProxyStatus.TIMEOUT:
                timeout_count += 1
        
        self.stats['working'] = working_count
        self.stats['failed'] = failed_count
        self.stats['timeout'] = timeout_count
        
        if valid_response_count > 0:
            self.stats['average_response_time'] = total_response_time / valid_response_count
    
    def get_working_proxies(self, results: List[ValidationResult]) -> List[ProxyNode]:
        """獲取可用的代理列表
        
        Args:
            results: 驗證結果列表
            
        Returns:
            可用代理列表
        """
        return [result.proxy for result in results if result.status == ProxyStatus.WORKING]
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息
        
        Returns:
            統計信息字典
        """
        return self.stats.copy()
    
    def filter_by_criteria(self, results: List[ValidationResult], 
                          min_speed: Optional[float] = None,
                          anonymity_levels: Optional[List[AnonymityLevel]] = None,
                          countries: Optional[List[str]] = None,
                          protocols: Optional[List[str]] = None) -> List[ValidationResult]:
        """根據條件過濾驗證結果
        
        Args:
            results: 驗證結果列表
            min_speed: 最小速度要求（響應時間上限）
            anonymity_levels: 允許的匿名等級列表
            countries: 允許的國家列表
            protocols: 允許的協議列表
            
        Returns:
            過濾後的結果列表
        """
        filtered = []
        
        for result in results:
            # 只考慮可用的代理
            if result.status != ProxyStatus.WORKING:
                continue
            
            # 速度過濾
            if min_speed and result.response_time and result.response_time > min_speed:
                continue
            
            # 匿名性過濾
            if anonymity_levels and result.anonymity_level not in anonymity_levels:
                continue
            
            # 國家過濾
            if countries:
                proxy_country = result.detected_country or result.proxy.country
                if proxy_country not in countries:
                    continue
            
            # 協議過濾
            if protocols and result.proxy.protocol not in protocols:
                continue
            
            filtered.append(result)
        
        return filtered


async def main():
    """測試函數"""
    # 創建測試代理
    test_proxies = [
        ProxyNode(ip="8.8.8.8", port=80, protocol="HTTP", anonymity="Unknown", country="US", source="Test"),
        ProxyNode(ip="1.1.1.1", port=80, protocol="HTTP", anonymity="Unknown", country="US", source="Test"),
    ]
    
    # 創建驗證器
    validator = ProxyValidator(timeout=5.0, max_concurrent=10)
    
    # 驗證代理
    logger.info("開始驗證測試代理...")
    results = await validator.validate_proxies(test_proxies, test_anonymity=True, test_geo=True)
    
    # 顯示結果
    for result in results:
        logger.info(f"代理 {result.proxy.ip}:{result.proxy.port}")
        logger.info(f"  狀態: {result.status.value}")
        if result.response_time:
            logger.info(f"  響應時間: {result.response_time:.2f}s")
        logger.info(f"  匿名等級: {result.anonymity_level.value}")
        if result.detected_country:
            logger.info(f"  檢測國家: {result.detected_country}")
        if result.error_message:
            logger.info(f"  錯誤: {result.error_message}")
        logger.info("")
    
    # 顯示統計信息
    stats = validator.get_stats()
    logger.info(f"驗證統計: {stats}")
    
    # 獲取可用代理
    working_proxies = validator.get_working_proxies(results)
    logger.info(f"可用代理數量: {len(working_proxies)}")


if __name__ == "__main__":
    asyncio.run(main())