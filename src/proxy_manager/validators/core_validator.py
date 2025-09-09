"""CoreValidator 核心驗證器

此模組提供統一的代理驗證接口，整合所有驗證功能：
- 基礎連通性驗證
- 匿名性檢測
- 地理位置驗證
- 性能測試
- 質量評分
- 結果聚合
"""

import asyncio
import time
import json
from typing import List, Dict, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

import aiohttp
from loguru import logger

from .proxy_validator import ProxyValidator, ValidationResult as BaseValidationResult, ProxyStatus, AnonymityLevel
from .batch_validator import BatchValidator
from ..crawlers.base_crawler import ProxyNode
from ..storage.redis_storage_manager import RedisStorageManager, ValidationData, ValidationStatus


class ValidationLevel(Enum):
    """驗證等級枚舉"""
    BASIC = "basic"          # 基礎連通性測試
    STANDARD = "standard"    # 標準測試（連通性+匿名性）
    COMPREHENSIVE = "comprehensive"  # 全面測試（所有功能）
    CUSTOM = "custom"        # 自定義測試


class QualityMetric(Enum):
    """質量指標枚舉"""
    SPEED = "speed"                    # 速度指標
    STABILITY = "stability"            # 穩定性指標
    ANONYMITY = "anonymity"            # 匿名性指標
    AVAILABILITY = "availability"      # 可用性指標
    GEOGRAPHIC = "geographic"          # 地理位置指標


@dataclass
class QualityScore:
    """質量評分數據類"""
    overall: float = 0.0              # 總體評分 (0-100)
    speed: float = 0.0                # 速度評分 (0-100)
    stability: float = 0.0            # 穩定性評分 (0-100)
    anonymity: float = 0.0            # 匿名性評分 (0-100)
    availability: float = 0.0         # 可用性評分 (0-100)
    geographic: float = 0.0           # 地理位置評分 (0-100)
    
    def to_dict(self) -> Dict[str, float]:
        """轉換為字典格式"""
        return {
            'overall': self.overall,
            'speed': self.speed,
            'stability': self.stability,
            'anonymity': self.anonymity,
            'availability': self.availability,
            'geographic': self.geographic
        }


@dataclass
class ValidationConfig:
    """驗證配置類"""
    level: ValidationLevel = ValidationLevel.STANDARD
    timeout: float = 10.0
    max_concurrent: int = 50
    retry_count: int = 3
    retry_delay: float = 1.0
    
    # 測試選項
    test_anonymity: bool = True
    test_geolocation: bool = True
    test_https_support: bool = True
    test_speed: bool = True
    
    # 質量評分權重
    quality_weights: Dict[str, float] = field(default_factory=lambda: {
        'speed': 0.3,
        'stability': 0.25,
        'anonymity': 0.2,
        'availability': 0.15,
        'geographic': 0.1
    })
    
    # 自定義測試URL
    custom_test_urls: List[str] = field(default_factory=list)
    
    # 過濾條件
    min_speed_threshold: Optional[float] = None  # 最小速度要求（秒）
    required_anonymity_levels: List[AnonymityLevel] = field(default_factory=list)
    allowed_countries: List[str] = field(default_factory=list)
    blocked_countries: List[str] = field(default_factory=list)


@dataclass
class EnhancedValidationResult:
    """增強的驗證結果"""
    proxy: ProxyNode
    status: ProxyStatus
    quality_score: QualityScore = field(default_factory=QualityScore)
    
    # 基礎測試結果
    response_time: Optional[float] = None
    anonymity_level: AnonymityLevel = AnonymityLevel.UNKNOWN
    supports_https: bool = False
    
    # 地理位置信息
    detected_ip: Optional[str] = None
    detected_country: Optional[str] = None
    detected_city: Optional[str] = None
    detected_region: Optional[str] = None
    detected_isp: Optional[str] = None
    
    # 性能指標
    avg_response_time: Optional[float] = None
    success_rate: float = 0.0
    stability_score: float = 0.0
    
    # 測試詳情
    test_results: List[Dict[str, Any]] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    test_timestamp: datetime = field(default_factory=datetime.utcnow)
    test_duration: Optional[float] = None
    
    # 歷史數據
    historical_success_rate: Optional[float] = None
    last_working_time: Optional[datetime] = None
    failure_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'proxy': {
                'ip': self.proxy.host,
                'port': self.proxy.port,
                'protocol': self.proxy.protocol,
                'country': self.proxy.country,
                'source': self.proxy.source
            },
            'status': self.status.value,
            'quality_score': self.quality_score.to_dict(),
            'response_time': self.response_time,
            'anonymity_level': self.anonymity_level.value,
            'supports_https': self.supports_https,
            'detected_ip': self.detected_ip,
            'detected_country': self.detected_country,
            'detected_city': self.detected_city,
            'detected_region': self.detected_region,
            'detected_isp': self.detected_isp,
            'avg_response_time': self.avg_response_time,
            'success_rate': self.success_rate,
            'stability_score': self.stability_score,
            'test_results': self.test_results,
            'error_messages': self.error_messages,
            'test_timestamp': self.test_timestamp.isoformat(),
            'test_duration': self.test_duration,
            'historical_success_rate': self.historical_success_rate,
            'last_working_time': self.last_working_time.isoformat() if self.last_working_time else None,
            'failure_count': self.failure_count
        }


class CoreValidator:
    """核心驗證器
    
    統一的代理驗證接口，提供全面的驗證功能和質量評分
    """
    
    def __init__(self, 
                 config: Optional[ValidationConfig] = None,
                 storage_manager: Optional[RedisStorageManager] = None):
        """初始化核心驗證器
        
        Args:
            config: 驗證配置
            storage_manager: 存儲管理器（可選）
        """
        self.config = config or ValidationConfig()
        self.storage_manager = storage_manager
        
        # 初始化基礎驗證器
        self.proxy_validator = ProxyValidator(
            timeout=self.config.timeout,
            max_concurrent=self.config.max_concurrent
        )
        
        self.batch_validator = BatchValidator(
            batch_size=min(self.config.max_concurrent, 100)
        )
        
        # 統計信息
        self.stats = {
            'total_validated': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'average_quality_score': 0.0,
            'validation_start_time': None,
            'validation_end_time': None
        }
        
        # 質量評分算法
        self.quality_algorithms = {
            QualityMetric.SPEED: self._calculate_speed_score,
            QualityMetric.STABILITY: self._calculate_stability_score,
            QualityMetric.ANONYMITY: self._calculate_anonymity_score,
            QualityMetric.AVAILABILITY: self._calculate_availability_score,
            QualityMetric.GEOGRAPHIC: self._calculate_geographic_score
        }
        
        logger.info(f"CoreValidator 初始化完成，驗證等級: {self.config.level.value}")
    
    async def validate_proxy(self, 
                           proxy: ProxyNode,
                           include_history: bool = True) -> EnhancedValidationResult:
        """驗證單個代理
        
        Args:
            proxy: 要驗證的代理
            include_history: 是否包含歷史數據
            
        Returns:
            增強的驗證結果
        """
        start_time = time.time()
        
        try:
            logger.debug(f"開始驗證代理 {proxy.host}:{proxy.port}")
            
            # 獲取歷史數據
            historical_data = None
            if include_history and self.storage_manager:
                historical_data = await self._get_historical_data(proxy)
            
            # 執行基礎驗證
            base_result = await self.proxy_validator.validate_proxy(
                proxy,
                test_anonymity=self.config.test_anonymity,
                test_geo=self.config.test_geolocation
            )
            
            # 創建增強結果
            enhanced_result = await self._create_enhanced_result(
                proxy, base_result, historical_data
            )
            
            # 執行額外測試
            if self.config.level in [ValidationLevel.COMPREHENSIVE, ValidationLevel.CUSTOM]:
                await self._perform_comprehensive_tests(enhanced_result)
            
            # 計算質量評分
            enhanced_result.quality_score = await self._calculate_quality_score(enhanced_result)
            
            # 應用過濾條件
            if not self._passes_filter_criteria(enhanced_result):
                enhanced_result.status = ProxyStatus.FAILED
                enhanced_result.error_messages.append("未通過過濾條件")
            
            # 記錄測試時長
            enhanced_result.test_duration = time.time() - start_time
            
            # 保存驗證結果
            if self.storage_manager:
                await self._save_validation_result(enhanced_result)
            
            # 更新統計信息
            self._update_stats(enhanced_result)
            
            logger.debug(f"代理 {proxy.host}:{proxy.port} 驗證完成，狀態: {enhanced_result.status.value}")
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"驗證代理 {proxy.host}:{proxy.port} 時發生錯誤: {str(e)}")
            
            error_result = EnhancedValidationResult(
                proxy=proxy,
                status=ProxyStatus.FAILED,
                error_messages=[str(e)],
                test_duration=time.time() - start_time
            )
            
            self._update_stats(error_result)
            return error_result
    
    async def validate_proxies(self, 
                             proxies: List[ProxyNode],
                             progress_callback: Optional[Callable[[int, int], None]] = None) -> List[EnhancedValidationResult]:
        """批量驗證代理
        
        Args:
            proxies: 代理列表
            progress_callback: 進度回調函數
            
        Returns:
            驗證結果列表
        """
        logger.info(f"開始批量驗證 {len(proxies)} 個代理")
        self.stats['validation_start_time'] = datetime.utcnow()
        
        # 創建信號量控制並發
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def validate_with_semaphore(i: int, proxy: ProxyNode):
            async with semaphore:
                result = await self.validate_proxy(proxy)
                if progress_callback:
                    progress_callback(i + 1, len(proxies))
                return result
        
        # 並發執行驗證
        tasks = [validate_with_semaphore(i, proxy) for i, proxy in enumerate(proxies)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"驗證代理 {proxies[i].ip}:{proxies[i].port} 時發生異常: {str(result)}")
                error_result = EnhancedValidationResult(
                    proxy=proxies[i],
                    status=ProxyStatus.FAILED,
                    error_messages=[str(result)]
                )
                valid_results.append(error_result)
            else:
                valid_results.append(result)
        
        self.stats['validation_end_time'] = datetime.utcnow()
        
        # 計算總體統計
        self._calculate_batch_stats(valid_results)
        
        logger.info(f"批量驗證完成，成功: {self.stats['successful_validations']}, 失敗: {self.stats['failed_validations']}")
        
        return valid_results
    
    async def _create_enhanced_result(self, 
                                    proxy: ProxyNode, 
                                    base_result: BaseValidationResult,
                                    historical_data: Optional[Dict[str, Any]]) -> EnhancedValidationResult:
        """創建增強的驗證結果
        
        Args:
            proxy: 代理節點
            base_result: 基礎驗證結果
            historical_data: 歷史數據
            
        Returns:
            增強的驗證結果
        """
        enhanced_result = EnhancedValidationResult(
            proxy=proxy,
            status=base_result.status,
            response_time=base_result.response_time,
            anonymity_level=base_result.anonymity_level,
            supports_https=base_result.supports_https,
            detected_ip=base_result.real_ip,
            detected_country=base_result.detected_country
        )
        
        # 添加錯誤信息
        if base_result.error_message:
            enhanced_result.error_messages.append(base_result.error_message)
        
        # 整合歷史數據
        if historical_data:
            enhanced_result.historical_success_rate = historical_data.get('success_rate')
            enhanced_result.last_working_time = historical_data.get('last_working_time')
            enhanced_result.failure_count = historical_data.get('failure_count', 0)
        
        return enhanced_result
    
    async def _perform_comprehensive_tests(self, result: EnhancedValidationResult):
        """執行全面測試
        
        Args:
            result: 驗證結果（會被修改）
        """
        if result.status != ProxyStatus.WORKING:
            return
        
        # 多次測試以評估穩定性
        if self.config.test_speed:
            await self._perform_speed_tests(result)
        
        # 自定義URL測試
        if self.config.custom_test_urls:
            await self._test_custom_urls(result)
    
    async def _perform_speed_tests(self, result: EnhancedValidationResult, test_count: int = 3):
        """執行速度測試
        
        Args:
            result: 驗證結果（會被修改）
            test_count: 測試次數
        """
        response_times = []
        successful_tests = 0
        
        proxy_url = self._build_proxy_url(result.proxy)
        test_url = 'http://httpbin.org/ip'
        
        for i in range(test_count):
            try:
                start_time = time.time()
                
                connector = aiohttp.TCPConnector()
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                ) as session:
                    async with session.get(test_url, proxy=proxy_url) as response:
                        if response.status == 200:
                            response_time = time.time() - start_time
                            response_times.append(response_time)
                            successful_tests += 1
                
                # 測試間隔
                if i < test_count - 1:
                    await asyncio.sleep(0.5)
                    
            except Exception as e:
                result.test_results.append({
                    'test_type': 'speed_test',
                    'test_number': i + 1,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # 計算平均響應時間和成功率
        if response_times:
            result.avg_response_time = sum(response_times) / len(response_times)
        
        result.success_rate = successful_tests / test_count
        
        # 記錄測試結果
        result.test_results.append({
            'test_type': 'speed_test',
            'total_tests': test_count,
            'successful_tests': successful_tests,
            'success_rate': result.success_rate,
            'avg_response_time': result.avg_response_time,
            'response_times': response_times
        })
    
    async def _test_custom_urls(self, result: EnhancedValidationResult):
        """測試自定義URL
        
        Args:
            result: 驗證結果（會被修改）
        """
        proxy_url = self._build_proxy_url(result.proxy)
        custom_test_results = []
        
        for test_url in self.config.custom_test_urls:
            try:
                start_time = time.time()
                
                connector = aiohttp.TCPConnector()
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                ) as session:
                    async with session.get(test_url, proxy=proxy_url) as response:
                        response_time = time.time() - start_time
                        
                        custom_test_results.append({
                            'url': test_url,
                            'status_code': response.status,
                            'response_time': response_time,
                            'success': response.status == 200
                        })
                        
            except Exception as e:
                custom_test_results.append({
                    'url': test_url,
                    'error': str(e),
                    'success': False
                })
        
        result.test_results.append({
            'test_type': 'custom_urls',
            'results': custom_test_results
        })
    
    def _build_proxy_url(self, proxy: ProxyNode) -> str:
        """構建代理URL
        
        Args:
            proxy: 代理節點
            
        Returns:
            代理URL字符串
        """
        protocol = proxy.protocol.value.lower()
        if protocol in ['socks4', 'socks5']:
            return f"{protocol}://{proxy.host}:{proxy.port}"
        else:
            return f"http://{proxy.host}:{proxy.port}"
    
    async def _calculate_quality_score(self, result: EnhancedValidationResult) -> QualityScore:
        """計算質量評分
        
        Args:
            result: 驗證結果
            
        Returns:
            質量評分
        """
        if result.status != ProxyStatus.WORKING:
            return QualityScore()
        
        scores = {}
        
        # 計算各項指標評分
        for metric, algorithm in self.quality_algorithms.items():
            try:
                scores[metric.value] = await algorithm(result)
            except Exception as e:
                logger.warning(f"計算 {metric.value} 評分時發生錯誤: {str(e)}")
                scores[metric.value] = 0.0
        
        # 計算加權總分
        overall_score = 0.0
        total_weight = 0.0
        
        for metric, weight in self.config.quality_weights.items():
            if metric in scores:
                overall_score += scores[metric] * weight
                total_weight += weight
        
        if total_weight > 0:
            overall_score = overall_score / total_weight
        
        return QualityScore(
            overall=overall_score,
            speed=scores.get('speed', 0.0),
            stability=scores.get('stability', 0.0),
            anonymity=scores.get('anonymity', 0.0),
            availability=scores.get('availability', 0.0),
            geographic=scores.get('geographic', 0.0)
        )
    
    async def _calculate_speed_score(self, result: EnhancedValidationResult) -> float:
        """計算速度評分
        
        Args:
            result: 驗證結果
            
        Returns:
            速度評分 (0-100)
        """
        if not result.response_time:
            return 0.0
        
        # 速度評分算法：響應時間越短評分越高
        # 1秒以內 = 100分，5秒以上 = 0分
        if result.response_time <= 1.0:
            return 100.0
        elif result.response_time >= 5.0:
            return 0.0
        else:
            # 線性插值
            return 100.0 * (5.0 - result.response_time) / 4.0
    
    async def _calculate_stability_score(self, result: EnhancedValidationResult) -> float:
        """計算穩定性評分
        
        Args:
            result: 驗證結果
            
        Returns:
            穩定性評分 (0-100)
        """
        # 基於成功率和歷史數據計算穩定性
        base_score = result.success_rate * 100
        
        # 考慮歷史成功率
        if result.historical_success_rate is not None:
            historical_weight = 0.3
            base_score = (base_score * (1 - historical_weight) + 
                         result.historical_success_rate * 100 * historical_weight)
        
        # 考慮失敗次數
        if result.failure_count > 0:
            failure_penalty = min(result.failure_count * 5, 30)  # 最多扣30分
            base_score = max(0, base_score - failure_penalty)
        
        return base_score
    
    async def _calculate_anonymity_score(self, result: EnhancedValidationResult) -> float:
        """計算匿名性評分
        
        Args:
            result: 驗證結果
            
        Returns:
            匿名性評分 (0-100)
        """
        anonymity_scores = {
            AnonymityLevel.ELITE: 100.0,
            AnonymityLevel.ANONYMOUS: 75.0,
            AnonymityLevel.TRANSPARENT: 25.0,
            AnonymityLevel.UNKNOWN: 0.0
        }
        
        return anonymity_scores.get(result.anonymity_level, 0.0)
    
    async def _calculate_availability_score(self, result: EnhancedValidationResult) -> float:
        """計算可用性評分
        
        Args:
            result: 驗證結果
            
        Returns:
            可用性評分 (0-100)
        """
        # 基礎可用性評分
        if result.status != ProxyStatus.WORKING:
            return 0.0
        
        base_score = 100.0
        
        # HTTPS支援加分
        if result.supports_https:
            base_score += 10.0
        
        # 最近工作時間考慮
        if result.last_working_time:
            time_diff = datetime.utcnow() - result.last_working_time
            if time_diff.total_seconds() > 86400:  # 超過24小時
                age_penalty = min(time_diff.days * 2, 20)  # 最多扣20分
                base_score -= age_penalty
        
        return min(100.0, max(0.0, base_score))
    
    async def _calculate_geographic_score(self, result: EnhancedValidationResult) -> float:
        """計算地理位置評分
        
        Args:
            result: 驗證結果
            
        Returns:
            地理位置評分 (0-100)
        """
        base_score = 50.0  # 基礎分
        
        # 有檢測到的國家信息
        if result.detected_country:
            base_score += 25.0
            
            # 國家匹配代理聲明的國家
            if (result.proxy.country and 
                result.detected_country.upper() == result.proxy.country.upper()):
                base_score += 25.0
        
        # 有詳細地理信息（城市、地區）
        if result.detected_city:
            base_score += 10.0
        
        if result.detected_region:
            base_score += 10.0
        
        # ISP信息
        if result.detected_isp:
            base_score += 5.0
        
        return min(100.0, base_score)
    
    def _passes_filter_criteria(self, result: EnhancedValidationResult) -> bool:
        """檢查是否通過過濾條件
        
        Args:
            result: 驗證結果
            
        Returns:
            是否通過過濾條件
        """
        if result.status != ProxyStatus.WORKING:
            return False
        
        # 速度過濾
        if (self.config.min_speed_threshold and 
            result.response_time and 
            result.response_time > self.config.min_speed_threshold):
            return False
        
        # 匿名性過濾
        if (self.config.required_anonymity_levels and 
            result.anonymity_level not in self.config.required_anonymity_levels):
            return False
        
        # 國家過濾
        detected_country = result.detected_country or result.proxy.country
        
        if self.config.allowed_countries and detected_country:
            if detected_country.upper() not in [c.upper() for c in self.config.allowed_countries]:
                return False
        
        if self.config.blocked_countries and detected_country:
            if detected_country.upper() in [c.upper() for c in self.config.blocked_countries]:
                return False
        
        return True
    
    async def _get_historical_data(self, proxy: ProxyNode) -> Optional[Dict[str, Any]]:
        """獲取代理的歷史數據
        
        Args:
            proxy: 代理節點
            
        Returns:
            歷史數據字典或None
        """
        try:
            proxy_id = f"{proxy.host}:{proxy.port}"
            
            # 獲取統計數據
            stats = await self.storage_manager.get_proxy_stats(proxy_id)
            if not stats:
                return None
            
            # 獲取最近的驗證歷史
            history = await self.storage_manager.get_validation_history(proxy_id, limit=10)
            
            # 計算歷史成功率
            if history:
                successful = sum(1 for h in history if h.status == ValidationStatus.SUCCESS)
                success_rate = successful / len(history)
                
                # 找到最後一次成功的時間
                last_working = None
                for h in history:
                    if h.status == ValidationStatus.SUCCESS:
                        last_working = h.timestamp
                        break
                
                return {
                    'success_rate': success_rate,
                    'last_working_time': last_working,
                    'failure_count': len(history) - successful,
                    'total_tests': len(history)
                }
            
            return stats
            
        except Exception as e:
            logger.warning(f"獲取代理 {proxy.host}:{proxy.port} 歷史數據時發生錯誤: {str(e)}")
            return None
    
    async def _save_validation_result(self, result: EnhancedValidationResult):
        """保存驗證結果
        
        Args:
            result: 驗證結果
        """
        try:
            proxy_id = f"{result.proxy.host}:{result.proxy.port}"
            
            # 創建驗證數據
            validation_data = ValidationData(
                validation_id=f"{proxy_id}_{int(time.time())}",
                proxy_id=proxy_id,
                status=ValidationStatus.SUCCESS if result.status == ProxyStatus.WORKING else ValidationStatus.FAILED,
                response_time=result.response_time,
                error_message='; '.join(result.error_messages) if result.error_messages else None,
                test_url=result.test_results[0].get('url') if result.test_results else None,
                quality_score=result.quality_score.overall,
                timestamp=result.test_timestamp
            )
            
            # 保存驗證結果
            await self.storage_manager.save_validation_result(validation_data)
            
            # 更新代理統計
            stats = {
                'last_test_time': result.test_timestamp.isoformat(),
                'last_response_time': result.response_time,
                'last_quality_score': result.quality_score.overall,
                'last_status': result.status.value,
                'test_count': 1  # 這裡簡化，實際應該累加
            }
            
            await self.storage_manager.update_proxy_stats(proxy_id, stats)
            
        except Exception as e:
            logger.error(f"保存驗證結果時發生錯誤: {str(e)}")
    
    def _update_stats(self, result: EnhancedValidationResult):
        """更新統計信息
        
        Args:
            result: 驗證結果
        """
        self.stats['total_validated'] += 1
        
        if result.status == ProxyStatus.WORKING:
            self.stats['successful_validations'] += 1
        else:
            self.stats['failed_validations'] += 1
    
    def _calculate_batch_stats(self, results: List[EnhancedValidationResult]):
        """計算批量統計信息
        
        Args:
            results: 驗證結果列表
        """
        if not results:
            return
        
        # 計算平均質量評分
        working_results = [r for r in results if r.status == ProxyStatus.WORKING]
        if working_results:
            total_score = sum(r.quality_score.overall for r in working_results)
            self.stats['average_quality_score'] = total_score / len(working_results)
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息
        
        Returns:
            統計信息字典
        """
        stats = self.stats.copy()
        
        # 計算成功率
        if stats['total_validated'] > 0:
            stats['success_rate'] = stats['successful_validations'] / stats['total_validated']
        else:
            stats['success_rate'] = 0.0
        
        # 計算驗證時長
        if stats['validation_start_time'] and stats['validation_end_time']:
            duration = stats['validation_end_time'] - stats['validation_start_time']
            stats['validation_duration'] = duration.total_seconds()
        
        return stats
    
    def filter_results(self, 
                      results: List[EnhancedValidationResult],
                      min_quality_score: Optional[float] = None,
                      max_response_time: Optional[float] = None,
                      required_anonymity: Optional[List[AnonymityLevel]] = None,
                      required_countries: Optional[List[str]] = None) -> List[EnhancedValidationResult]:
        """過濾驗證結果
        
        Args:
            results: 驗證結果列表
            min_quality_score: 最小質量評分
            max_response_time: 最大響應時間
            required_anonymity: 要求的匿名等級
            required_countries: 要求的國家列表
            
        Returns:
            過濾後的結果列表
        """
        filtered = []
        
        for result in results:
            if result.status != ProxyStatus.WORKING:
                continue
            
            # 質量評分過濾
            if min_quality_score and result.quality_score.overall < min_quality_score:
                continue
            
            # 響應時間過濾
            if max_response_time and result.response_time and result.response_time > max_response_time:
                continue
            
            # 匿名性過濾
            if required_anonymity and result.anonymity_level not in required_anonymity:
                continue
            
            # 國家過濾
            if required_countries:
                proxy_country = result.detected_country or result.proxy.country
                # 確保proxy_country是字符串
                if hasattr(proxy_country, 'value'):
                    proxy_country = proxy_country.value
                proxy_country_str = str(proxy_country) if proxy_country else None
                if not proxy_country_str or proxy_country_str.upper() not in [c.upper() for c in required_countries]:
                    continue
            
            filtered.append(result)
        
        return filtered
    
    def sort_by_quality(self, results: List[EnhancedValidationResult]) -> List[EnhancedValidationResult]:
        """按質量評分排序
        
        Args:
            results: 驗證結果列表
            
        Returns:
            排序後的結果列表
        """
        return sorted(results, key=lambda r: r.quality_score.overall, reverse=True)
    
    async def cleanup(self):
        """清理資源"""
        try:
            if hasattr(self.proxy_validator, 'cleanup'):
                await self.proxy_validator.cleanup()
            
            if hasattr(self.batch_validator, 'cleanup'):
                await self.batch_validator.cleanup()
            
            logger.info("CoreValidator 資源清理完成")
            
        except Exception as e:
            logger.error(f"清理資源時發生錯誤: {str(e)}")


async def main():
    """測試函數"""
    from ..storage.redis_storage_manager import RedisStorageManager, StorageConfig
    
    # 創建測試代理
    test_proxies = [
        ProxyNode(ip="8.8.8.8", port=80, protocol="HTTP", anonymity="Unknown", country="US", source="Test"),
        ProxyNode(ip="1.1.1.1", port=80, protocol="HTTP", anonymity="Unknown", country="US", source="Test"),
    ]
    
    # 創建存儲管理器（可選）
    storage_config = StorageConfig(
        host="localhost",
        port=6379,
        db=15  # 測試數據庫
    )
    storage_manager = RedisStorageManager(storage_config)
    
    try:
        await storage_manager.connect()
        
        # 創建核心驗證器
        config = ValidationConfig(
            level=ValidationLevel.COMPREHENSIVE,
            timeout=5.0,
            max_concurrent=5,
            test_anonymity=True,
            test_geolocation=True,
            test_https_support=True,
            test_speed=True
        )
        
        validator = CoreValidator(config, storage_manager)
        
        # 驗證代理
        logger.info("開始核心驗證測試...")
        
        def progress_callback(current: int, total: int):
            logger.info(f"驗證進度: {current}/{total} ({current/total*100:.1f}%)")
        
        results = await validator.validate_proxies(test_proxies, progress_callback)
        
        # 顯示結果
        for result in results:
            logger.info(f"\n代理 {result.proxy.host}:{result.proxy.port}")
            logger.info(f"  狀態: {result.status.value}")
            logger.info(f"  質量評分: {result.quality_score.overall:.1f}")
            logger.info(f"  速度評分: {result.quality_score.speed:.1f}")
            logger.info(f"  穩定性評分: {result.quality_score.stability:.1f}")
            logger.info(f"  匿名性評分: {result.quality_score.anonymity:.1f}")
            if result.response_time:
                logger.info(f"  響應時間: {result.response_time:.2f}s")
            logger.info(f"  匿名等級: {result.anonymity_level.value}")
            if result.detected_country:
                logger.info(f"  檢測國家: {result.detected_country}")
            if result.error_messages:
                logger.info(f"  錯誤: {'; '.join(result.error_messages)}")
        
        # 顯示統計信息
        stats = validator.get_stats()
        logger.info(f"\n驗證統計:")
        logger.info(f"  總計: {stats['total_validated']}")
        logger.info(f"  成功: {stats['successful_validations']}")
        logger.info(f"  失敗: {stats['failed_validations']}")
        logger.info(f"  成功率: {stats['success_rate']:.1%}")
        logger.info(f"  平均質量評分: {stats['average_quality_score']:.1f}")
        
        # 過濾高質量代理
        high_quality = validator.filter_results(
            results,
            min_quality_score=70.0,
            max_response_time=2.0
        )
        logger.info(f"\n高質量代理數量: {len(high_quality)}")
        
        # 清理
        await validator.cleanup()
        
    finally:
        await storage_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(main())