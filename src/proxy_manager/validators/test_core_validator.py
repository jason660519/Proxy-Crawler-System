"""CoreValidator 測試模組

此模組提供CoreValidator的完整測試功能：
- 單個代理驗證測試
- 批量代理驗證測試
- 質量評分算法測試
- 過濾和排序功能測試
- 配置選項測試
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from loguru import logger

from .core_validator import (
    CoreValidator,
    ValidationConfig,
    ValidationLevel,
    QualityScore,
    QualityMetric,
    EnhancedValidationResult
)
from .proxy_validator import ProxyStatus, AnonymityLevel
from ..crawlers.base_crawler import ProxyNode
from ..storage.redis_storage_manager import RedisStorageManager, StorageConfig


class TestCoreValidator:
    """CoreValidator測試類"""
    
    @pytest.fixture
    def sample_proxies(self) -> List[ProxyNode]:
        """創建測試代理列表"""
        return [
            ProxyNode(
                ip="192.168.1.1",
                port=8080,
                protocol="HTTP",
                anonymity="Elite",
                country="US",
                source="Test"
            ),
            ProxyNode(
                ip="10.0.0.1",
                port=3128,
                protocol="HTTP",
                anonymity="Anonymous",
                country="CN",
                source="Test"
            ),
            ProxyNode(
                ip="172.16.0.1",
                port=1080,
                protocol="SOCKS5",
                anonymity="Transparent",
                country="JP",
                source="Test"
            )
        ]
    
    @pytest.fixture
    def basic_config(self) -> ValidationConfig:
        """創建基礎配置"""
        return ValidationConfig(
            level=ValidationLevel.STANDARD,
            timeout=5.0,
            max_concurrent=10,
            test_anonymity=True,
            test_geolocation=True,
            test_https_support=True,
            test_speed=False  # 測試時關閉速度測試以加快執行
        )
    
    @pytest.fixture
    def comprehensive_config(self) -> ValidationConfig:
        """創建全面配置"""
        return ValidationConfig(
            level=ValidationLevel.COMPREHENSIVE,
            timeout=3.0,
            max_concurrent=5,
            test_anonymity=True,
            test_geolocation=True,
            test_https_support=True,
            test_speed=True,
            custom_test_urls=["http://httpbin.org/ip", "http://httpbin.org/headers"],
            min_speed_threshold=2.0,
            required_anonymity_levels=[AnonymityLevel.ELITE, AnonymityLevel.ANONYMOUS],
            allowed_countries=["US", "CN", "JP"]
        )
    
    @pytest.fixture
    async def mock_storage_manager(self):
        """創建模擬存儲管理器"""
        storage = Mock(spec=RedisStorageManager)
        storage.connect = AsyncMock()
        storage.disconnect = AsyncMock()
        storage.get_proxy_stats = AsyncMock(return_value=None)
        storage.get_validation_history = AsyncMock(return_value=[])
        storage.save_validation_result = AsyncMock()
        storage.update_proxy_stats = AsyncMock()
        return storage
    
    def test_validator_initialization(self, basic_config):
        """測試驗證器初始化"""
        validator = CoreValidator(basic_config)
        
        assert validator.config == basic_config
        assert validator.proxy_validator is not None
        assert validator.batch_validator is not None
        assert validator.stats['total_validated'] == 0
        assert validator.stats['successful_validations'] == 0
        assert validator.stats['failed_validations'] == 0
    
    def test_validator_initialization_without_config(self):
        """測試無配置初始化"""
        validator = CoreValidator()
        
        assert validator.config is not None
        assert validator.config.level == ValidationLevel.STANDARD
        assert validator.config.timeout == 10.0
        assert validator.config.max_concurrent == 50
    
    @pytest.mark.asyncio
    async def test_single_proxy_validation_success(self, basic_config, sample_proxies, mock_storage_manager):
        """測試單個代理驗證成功"""
        validator = CoreValidator(basic_config, mock_storage_manager)
        
        # 模擬成功的驗證結果
        with patch.object(validator.proxy_validator, 'validate_proxy') as mock_validate:
            from .proxy_validator import ValidationResult
            mock_validate.return_value = ValidationResult(
                proxy=sample_proxies[0],
                status=ProxyStatus.WORKING,
                response_time=1.5,
                anonymity_level=AnonymityLevel.ELITE,
                supports_https=True,
                real_ip="8.8.8.8",
                detected_country="US"
            )
            
            result = await validator.validate_proxy(sample_proxies[0])
            
            assert isinstance(result, EnhancedValidationResult)
            assert result.status == ProxyStatus.WORKING
            assert result.response_time == 1.5
            assert result.anonymity_level == AnonymityLevel.ELITE
            assert result.supports_https is True
            assert result.detected_ip == "8.8.8.8"
            assert result.detected_country == "US"
            assert result.quality_score.overall > 0
    
    @pytest.mark.asyncio
    async def test_single_proxy_validation_failure(self, basic_config, sample_proxies):
        """測試單個代理驗證失敗"""
        validator = CoreValidator(basic_config)
        
        # 模擬失敗的驗證結果
        with patch.object(validator.proxy_validator, 'validate_proxy') as mock_validate:
            from .proxy_validator import ValidationResult
            mock_validate.return_value = ValidationResult(
                proxy=sample_proxies[0],
                status=ProxyStatus.FAILED,
                error_message="Connection timeout"
            )
            
            result = await validator.validate_proxy(sample_proxies[0])
            
            assert result.status == ProxyStatus.FAILED
            assert "Connection timeout" in result.error_messages
            assert result.quality_score.overall == 0.0
    
    @pytest.mark.asyncio
    async def test_batch_proxy_validation(self, basic_config, sample_proxies):
        """測試批量代理驗證"""
        validator = CoreValidator(basic_config)
        
        # 模擬驗證結果
        with patch.object(validator, 'validate_proxy') as mock_validate:
            mock_results = []
            for i, proxy in enumerate(sample_proxies):
                result = EnhancedValidationResult(
                    proxy=proxy,
                    status=ProxyStatus.WORKING if i % 2 == 0 else ProxyStatus.FAILED,
                    response_time=1.0 + i * 0.5
                )
                result.quality_score = QualityScore(overall=80.0 - i * 10)
                mock_results.append(result)
            
            mock_validate.side_effect = mock_results
            
            # 進度回調測試
            progress_calls = []
            def progress_callback(current, total):
                progress_calls.append((current, total))
            
            results = await validator.validate_proxies(sample_proxies, progress_callback)
            
            assert len(results) == len(sample_proxies)
            assert len(progress_calls) == len(sample_proxies)
            assert progress_calls[-1] == (len(sample_proxies), len(sample_proxies))
            
            # 檢查統計信息
            stats = validator.get_stats()
            assert stats['total_validated'] == len(sample_proxies)
            assert stats['successful_validations'] > 0
            assert stats['success_rate'] > 0
    
    def test_quality_score_calculation(self):
        """測試質量評分計算"""
        validator = CoreValidator()
        
        # 創建測試結果
        result = EnhancedValidationResult(
            proxy=ProxyNode("192.168.1.1", 8080, "HTTP", "Elite", "US", "Test"),
            status=ProxyStatus.WORKING,
            response_time=1.0,
            anonymity_level=AnonymityLevel.ELITE,
            supports_https=True,
            detected_country="US",
            success_rate=0.9
        )
        
        # 測試各項評分算法
        speed_score = asyncio.run(validator._calculate_speed_score(result))
        assert speed_score == 100.0  # 1秒響應時間應該得滿分
        
        stability_score = asyncio.run(validator._calculate_stability_score(result))
        assert stability_score == 90.0  # 90%成功率
        
        anonymity_score = asyncio.run(validator._calculate_anonymity_score(result))
        assert anonymity_score == 100.0  # Elite匿名等級
        
        availability_score = asyncio.run(validator._calculate_availability_score(result))
        assert availability_score >= 100.0  # 基礎分+HTTPS支援
        
        geographic_score = asyncio.run(validator._calculate_geographic_score(result))
        assert geographic_score >= 75.0  # 有國家信息且匹配
    
    def test_filter_criteria(self, comprehensive_config):
        """測試過濾條件"""
        validator = CoreValidator(comprehensive_config)
        
        # 測試通過過濾的代理
        good_result = EnhancedValidationResult(
            proxy=ProxyNode("192.168.1.1", 8080, "HTTP", "Elite", "US", "Test"),
            status=ProxyStatus.WORKING,
            response_time=1.5,  # 小於閾值2.0
            anonymity_level=AnonymityLevel.ELITE,  # 在允許列表中
            detected_country="US"  # 在允許國家列表中
        )
        
        assert validator._passes_filter_criteria(good_result) is True
        
        # 測試不通過過濾的代理（速度太慢）
        slow_result = EnhancedValidationResult(
            proxy=ProxyNode("192.168.1.2", 8080, "HTTP", "Elite", "US", "Test"),
            status=ProxyStatus.WORKING,
            response_time=3.0,  # 大於閾值2.0
            anonymity_level=AnonymityLevel.ELITE,
            detected_country="US"
        )
        
        assert validator._passes_filter_criteria(slow_result) is False
        
        # 測試不通過過濾的代理（匿名等級不符）
        transparent_result = EnhancedValidationResult(
            proxy=ProxyNode("192.168.1.3", 8080, "HTTP", "Transparent", "US", "Test"),
            status=ProxyStatus.WORKING,
            response_time=1.0,
            anonymity_level=AnonymityLevel.TRANSPARENT,  # 不在允許列表中
            detected_country="US"
        )
        
        assert validator._passes_filter_criteria(transparent_result) is False
        
        # 測試不通過過濾的代理（國家不符）
        blocked_country_result = EnhancedValidationResult(
            proxy=ProxyNode("192.168.1.4", 8080, "HTTP", "Elite", "RU", "Test"),
            status=ProxyStatus.WORKING,
            response_time=1.0,
            anonymity_level=AnonymityLevel.ELITE,
            detected_country="RU"  # 不在允許國家列表中
        )
        
        assert validator._passes_filter_criteria(blocked_country_result) is False
    
    def test_result_filtering_and_sorting(self, sample_proxies):
        """測試結果過濾和排序"""
        validator = CoreValidator()
        
        # 創建測試結果
        results = []
        for i, proxy in enumerate(sample_proxies):
            result = EnhancedValidationResult(
                proxy=proxy,
                status=ProxyStatus.WORKING,
                response_time=1.0 + i * 0.5,
                anonymity_level=[AnonymityLevel.ELITE, AnonymityLevel.ANONYMOUS, AnonymityLevel.TRANSPARENT][i]
            )
            result.quality_score = QualityScore(overall=90.0 - i * 20)
            results.append(result)
        
        # 測試質量評分過濾
        high_quality = validator.filter_results(results, min_quality_score=60.0)
        assert len(high_quality) == 2  # 只有前兩個滿足條件
        
        # 測試響應時間過濾
        fast_proxies = validator.filter_results(results, max_response_time=1.5)
        assert len(fast_proxies) == 2  # 只有前兩個滿足條件
        
        # 測試匿名性過濾
        anonymous_proxies = validator.filter_results(
            results, 
            required_anonymity=[AnonymityLevel.ELITE, AnonymityLevel.ANONYMOUS]
        )
        assert len(anonymous_proxies) == 2  # 排除透明代理
        
        # 測試排序
        sorted_results = validator.sort_by_quality(results)
        assert sorted_results[0].quality_score.overall >= sorted_results[1].quality_score.overall
        assert sorted_results[1].quality_score.overall >= sorted_results[2].quality_score.overall
    
    def test_stats_calculation(self, basic_config, sample_proxies):
        """測試統計信息計算"""
        validator = CoreValidator(basic_config)
        
        # 模擬一些驗證結果
        results = []
        for i, proxy in enumerate(sample_proxies):
            result = EnhancedValidationResult(
                proxy=proxy,
                status=ProxyStatus.WORKING if i < 2 else ProxyStatus.FAILED
            )
            result.quality_score = QualityScore(overall=80.0 if i < 2 else 0.0)
            validator._update_stats(result)
            results.append(result)
        
        validator._calculate_batch_stats(results)
        
        stats = validator.get_stats()
        assert stats['total_validated'] == 3
        assert stats['successful_validations'] == 2
        assert stats['failed_validations'] == 1
        assert stats['success_rate'] == 2/3
        assert stats['average_quality_score'] == 80.0
    
    def test_build_proxy_url(self):
        """測試代理URL構建"""
        validator = CoreValidator()
        
        # HTTP代理
        http_proxy = ProxyNode("192.168.1.1", 8080, "HTTP", "Elite", "US", "Test")
        http_url = validator._build_proxy_url(http_proxy)
        assert http_url == "http://192.168.1.1:8080"
        
        # SOCKS5代理
        socks5_proxy = ProxyNode("192.168.1.2", 1080, "SOCKS5", "Elite", "US", "Test")
        socks5_url = validator._build_proxy_url(socks5_proxy)
        assert socks5_url == "socks5://192.168.1.2:1080"
        
        # SOCKS4代理
        socks4_proxy = ProxyNode("192.168.1.3", 1080, "SOCKS4", "Elite", "US", "Test")
        socks4_url = validator._build_proxy_url(socks4_proxy)
        assert socks4_url == "socks4://192.168.1.3:1080"
    
    @pytest.mark.asyncio
    async def test_historical_data_integration(self, basic_config, sample_proxies, mock_storage_manager):
        """測試歷史數據整合"""
        # 設置模擬歷史數據
        mock_storage_manager.get_validation_history.return_value = [
            Mock(status='SUCCESS', timestamp=datetime.utcnow() - timedelta(hours=1)),
            Mock(status='SUCCESS', timestamp=datetime.utcnow() - timedelta(hours=2)),
            Mock(status='FAILED', timestamp=datetime.utcnow() - timedelta(hours=3))
        ]
        
        validator = CoreValidator(basic_config, mock_storage_manager)
        
        # 測試歷史數據獲取
        historical_data = await validator._get_historical_data(sample_proxies[0])
        
        assert historical_data is not None
        assert 'success_rate' in historical_data
        assert historical_data['success_rate'] == 2/3  # 2成功，1失敗
        assert 'failure_count' in historical_data
        assert historical_data['failure_count'] == 1
    
    @pytest.mark.asyncio
    async def test_comprehensive_validation_level(self, comprehensive_config, sample_proxies):
        """測試全面驗證等級"""
        validator = CoreValidator(comprehensive_config)
        
        # 模擬基礎驗證成功
        with patch.object(validator.proxy_validator, 'validate_proxy') as mock_validate:
            from .proxy_validator import ValidationResult
            mock_validate.return_value = ValidationResult(
                proxy=sample_proxies[0],
                status=ProxyStatus.WORKING,
                response_time=1.0,
                anonymity_level=AnonymityLevel.ELITE,
                supports_https=True
            )
            
            # 模擬HTTP請求
            with patch('aiohttp.ClientSession') as mock_session:
                mock_response = Mock()
                mock_response.status = 200
                mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
                
                result = await validator.validate_proxy(sample_proxies[0])
                
                assert result.status == ProxyStatus.WORKING
                assert len(result.test_results) > 0  # 應該有額外的測試結果
    
    @pytest.mark.asyncio
    async def test_error_handling(self, basic_config, sample_proxies):
        """測試錯誤處理"""
        validator = CoreValidator(basic_config)
        
        # 模擬驗證過程中的異常
        with patch.object(validator.proxy_validator, 'validate_proxy') as mock_validate:
            mock_validate.side_effect = Exception("Network error")
            
            result = await validator.validate_proxy(sample_proxies[0])
            
            assert result.status == ProxyStatus.FAILED
            assert "Network error" in result.error_messages
            assert result.test_duration is not None
    
    @pytest.mark.asyncio
    async def test_cleanup(self, basic_config):
        """測試資源清理"""
        validator = CoreValidator(basic_config)
        
        # 模擬清理方法
        validator.proxy_validator.cleanup = AsyncMock()
        validator.batch_validator.cleanup = AsyncMock()
        
        await validator.cleanup()
        
        # 驗證清理方法被調用
        validator.proxy_validator.cleanup.assert_called_once()
        validator.batch_validator.cleanup.assert_called_once()


async def run_integration_test():
    """運行整合測試"""
    logger.info("開始CoreValidator整合測試...")
    
    # 創建測試代理
    test_proxies = [
        ProxyNode(ip="8.8.8.8", port=80, protocol="HTTP", anonymity="Unknown", country="US", source="Test"),
        ProxyNode(ip="1.1.1.1", port=80, protocol="HTTP", anonymity="Unknown", country="US", source="Test"),
    ]
    
    # 創建配置
    config = ValidationConfig(
        level=ValidationLevel.STANDARD,
        timeout=5.0,
        max_concurrent=2,
        test_anonymity=True,
        test_geolocation=False,  # 關閉地理位置測試以加快速度
        test_https_support=True,
        test_speed=False  # 關閉速度測試以加快速度
    )
    
    # 創建驗證器
    validator = CoreValidator(config)
    
    try:
        logger.info("測試單個代理驗證...")
        result = await validator.validate_proxy(test_proxies[0])
        logger.info(f"代理 {result.proxy.ip}:{result.proxy.port} 驗證結果: {result.status.value}")
        logger.info(f"質量評分: {result.quality_score.overall:.1f}")
        
        logger.info("測試批量代理驗證...")
        
        def progress_callback(current: int, total: int):
            logger.info(f"驗證進度: {current}/{total}")
        
        results = await validator.validate_proxies(test_proxies, progress_callback)
        
        # 顯示結果
        working_count = sum(1 for r in results if r.status == ProxyStatus.WORKING)
        logger.info(f"驗證完成，工作代理: {working_count}/{len(results)}")
        
        # 顯示統計信息
        stats = validator.get_stats()
        logger.info(f"統計信息: {stats}")
        
        # 測試過濾功能
        high_quality = validator.filter_results(results, min_quality_score=50.0)
        logger.info(f"高質量代理數量: {len(high_quality)}")
        
        # 測試排序功能
        sorted_results = validator.sort_by_quality(results)
        logger.info("按質量排序的前3個代理:")
        for i, result in enumerate(sorted_results[:3]):
            logger.info(f"  {i+1}. {result.proxy.ip}:{result.proxy.port} - 評分: {result.quality_score.overall:.1f}")
        
        logger.info("整合測試完成！")
        
    except Exception as e:
        logger.error(f"整合測試失敗: {str(e)}")
        raise
    
    finally:
        await validator.cleanup()


if __name__ == "__main__":
    # 運行整合測試
    asyncio.run(run_integration_test())
    
    # 如果要運行pytest測試，使用以下命令：
    # pytest test_core_validator.py -v