"""代理驗證器模組

提供全面的代理驗證功能，包括：
- 可用性測試
- 速度檢測
- 匿名度驗證
- 地理位置檢測
- 多維度評分
"""

import asyncio
import aiohttp
import time
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from urllib.parse import urlparse

from .models import ProxyNode, ProxyStatus, ProxyAnonymity, ProxyProtocol

logger = logging.getLogger(__name__)


@dataclass
class ValidationConfig:
    """驗證配置"""
    timeout: int = 10  # 超時時間（秒）
    max_concurrent: int = 50  # 最大併發數
    test_urls: List[str] = None  # 測試URL列表
    anonymity_check_url: str = "http://httpbin.org/ip"  # 匿名度檢測URL
    geo_check_url: str = "http://ip-api.com/json/"  # 地理位置檢測URL
    retry_count: int = 2  # 重試次數
    retry_delay: float = 1.0  # 重試延遲（秒）
    
    def __post_init__(self):
        if self.test_urls is None:
            self.test_urls = [
                "http://httpbin.org/ip",
                "https://httpbin.org/ip",
                "http://www.google.com",
                "https://www.github.com"
            ]


@dataclass
class ValidationResult:
    """驗證結果"""
    proxy: ProxyNode
    is_working: bool = False
    response_time_ms: Optional[int] = None
    anonymity: ProxyAnonymity = ProxyAnonymity.UNKNOWN
    country: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    error_message: Optional[str] = None
    test_details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.test_details is None:
            self.test_details = {}


class ProxyValidator:
    """代理驗證器"""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.real_ip: Optional[str] = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        """啟動驗證器"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=self.config.max_concurrent * 2,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
        
        # 獲取真實IP地址
        await self._get_real_ip()
    
    async def close(self):
        """關閉驗證器"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def _get_real_ip(self):
        """獲取真實IP地址（用於匿名度檢測）"""
        try:
            async with self.session.get(self.config.anonymity_check_url) as response:
                if response.status == 200:
                    data = await response.json()
                    self.real_ip = data.get('origin', '').split(',')[0].strip()
                    logger.info(f"✅ 獲取真實IP: {self.real_ip}")
        except Exception as e:
            logger.warning(f"⚠️ 無法獲取真實IP: {e}")
            self.real_ip = None
    
    async def validate_proxy(self, proxy: ProxyNode) -> ValidationResult:
        """驗證單個代理"""
        async with self._semaphore:
            result = ValidationResult(proxy=proxy)
            
            try:
                # 基本連接測試
                connectivity_result = await self._test_connectivity(proxy)
                result.is_working = connectivity_result['is_working']
                result.response_time_ms = connectivity_result['response_time_ms']
                result.error_message = connectivity_result.get('error')
                result.test_details['connectivity'] = connectivity_result
                
                if result.is_working:
                    # 匿名度檢測
                    anonymity_result = await self._test_anonymity(proxy)
                    result.anonymity = anonymity_result['anonymity']
                    result.test_details['anonymity'] = anonymity_result
                    
                    # 地理位置檢測
                    geo_result = await self._test_geolocation(proxy)
                    result.country = geo_result.get('country')
                    result.region = geo_result.get('region')
                    result.city = geo_result.get('city')
                    result.isp = geo_result.get('isp')
                    result.test_details['geolocation'] = geo_result
                    
                    # 更新代理節點信息
                    proxy.status = ProxyStatus.ACTIVE
                    proxy.anonymity = result.anonymity
                    proxy.country = result.country
                    proxy.region = result.region
                    proxy.city = result.city
                    proxy.isp = result.isp
                    proxy.last_checked = datetime.now()
                    proxy.metrics.update_success(result.response_time_ms)
                else:
                    proxy.status = ProxyStatus.INACTIVE
                    proxy.last_checked = datetime.now()
                    proxy.metrics.update_failure()
                
                proxy.updated_at = datetime.now()
                
            except Exception as e:
                logger.error(f"❌ 驗證代理失敗 {proxy.url}: {e}")
                result.error_message = str(e)
                proxy.status = ProxyStatus.INACTIVE
                proxy.metrics.update_failure()
            
            return result
    
    async def validate_proxies(self, proxies: List[ProxyNode]) -> List[ValidationResult]:
        """批量驗證代理"""
        logger.info(f"🔍 開始驗證 {len(proxies)} 個代理...")
        
        tasks = [self.validate_proxy(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 驗證代理異常 {proxies[i].url}: {result}")
                # 創建失敗結果
                failed_result = ValidationResult(
                    proxy=proxies[i],
                    is_working=False,
                    error_message=str(result)
                )
                valid_results.append(failed_result)
            else:
                valid_results.append(result)
        
        # 統計結果
        working_count = sum(1 for r in valid_results if r.is_working)
        logger.info(f"✅ 驗證完成: {working_count}/{len(proxies)} 個代理可用")
        
        return valid_results
    
    async def _test_connectivity(self, proxy: ProxyNode) -> Dict[str, Any]:
        """測試代理連接性"""
        proxy_url = f"{proxy.protocol.value}://{proxy.host}:{proxy.port}"
        
        for attempt in range(self.config.retry_count + 1):
            try:
                start_time = time.time()
                
                # 選擇測試URL
                test_url = self.config.test_urls[0]
                if proxy.protocol == ProxyProtocol.HTTPS:
                    test_url = next((url for url in self.config.test_urls if url.startswith('https')), test_url)
                
                async with self.session.get(
                    test_url,
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout)
                ) as response:
                    response_time_ms = int((time.time() - start_time) * 1000)
                    
                    if response.status == 200:
                        return {
                            'is_working': True,
                            'response_time_ms': response_time_ms,
                            'status_code': response.status,
                            'test_url': test_url,
                            'attempt': attempt + 1
                        }
                    else:
                        return {
                            'is_working': False,
                            'response_time_ms': response_time_ms,
                            'status_code': response.status,
                            'error': f'HTTP {response.status}',
                            'test_url': test_url,
                            'attempt': attempt + 1
                        }
                        
            except asyncio.TimeoutError:
                if attempt < self.config.retry_count:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                return {
                    'is_working': False,
                    'error': 'Timeout',
                    'attempt': attempt + 1
                }
            except Exception as e:
                if attempt < self.config.retry_count:
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                return {
                    'is_working': False,
                    'error': str(e),
                    'attempt': attempt + 1
                }
        
        return {'is_working': False, 'error': 'Max retries exceeded'}
    
    async def _test_anonymity(self, proxy: ProxyNode) -> Dict[str, Any]:
        """測試代理匿名度"""
        proxy_url = f"{proxy.protocol.value}://{proxy.host}:{proxy.port}"
        
        try:
            async with self.session.get(
                self.config.anonymity_check_url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    proxy_ip = data.get('origin', '').split(',')[0].strip()
                    
                    # 檢查是否洩露真實IP
                    if self.real_ip and self.real_ip in proxy_ip:
                        anonymity = ProxyAnonymity.TRANSPARENT
                    elif proxy_ip == proxy.host:
                        anonymity = ProxyAnonymity.ELITE
                    else:
                        anonymity = ProxyAnonymity.ANONYMOUS
                    
                    return {
                        'anonymity': anonymity,
                        'proxy_ip': proxy_ip,
                        'real_ip': self.real_ip,
                        'headers': dict(response.headers)
                    }
                else:
                    return {
                        'anonymity': ProxyAnonymity.UNKNOWN,
                        'error': f'HTTP {response.status}'
                    }
                    
        except Exception as e:
            return {
                'anonymity': ProxyAnonymity.UNKNOWN,
                'error': str(e)
            }
    
    async def _test_geolocation(self, proxy: ProxyNode) -> Dict[str, Any]:
        """測試代理地理位置"""
        proxy_url = f"{proxy.protocol.value}://{proxy.host}:{proxy.port}"
        
        try:
            # 使用代理IP檢測地理位置
            geo_url = f"{self.config.geo_check_url}{proxy.host}"
            
            async with self.session.get(
                geo_url,
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get('status') == 'success':
                        return {
                            'country': data.get('countryCode'),
                            'region': data.get('regionName'),
                            'city': data.get('city'),
                            'isp': data.get('isp'),
                            'timezone': data.get('timezone'),
                            'lat': data.get('lat'),
                            'lon': data.get('lon')
                        }
                    else:
                        return {'error': data.get('message', 'Unknown error')}
                else:
                    return {'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            return {'error': str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取驗證器統計信息"""
        return {
            'config': {
                'timeout': self.config.timeout,
                'max_concurrent': self.config.max_concurrent,
                'retry_count': self.config.retry_count,
                'test_urls_count': len(self.config.test_urls)
            },
            'real_ip': self.real_ip,
            'session_active': self.session is not None
        }