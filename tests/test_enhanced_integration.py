#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強代理整合測試模組

測試第二階段增強功能：
- ZMap 整合
- 智能代理探測
- 地理位置增強檢測
- 質量評估
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.proxy_manager.models import ProxyNode, ProxyStatus, ProxyProtocol, ProxyAnonymity
from src.proxy_manager.intelligent_detection import AnonymityLevel, DetectionResult
from src.proxy_manager.scanner import EnhancedProxyScanner
from src.proxy_manager.zmap_integration import ZMapIntegration, IntelligentTargetDiscovery
from src.proxy_manager.geolocation_enhanced import (
    EnhancedGeolocationDetector, GeolocationInfo, IntelligentProxyRouter
)
from src.proxy_manager.intelligent_detection import IntelligentProxyDetector, BenchmarkResult
from src.proxy_manager.quality_assessment import (
    ProxyQualityAssessor, QualityGrade, QualityMetrics
)


class TestZMapIntegration:
    """ZMap 整合測試"""
    
    @pytest.fixture
    def zmap_integration(self):
        """ZMap 整合實例"""
        return ZMapIntegration()
    
    def test_zmap_integration_init(self, zmap_integration):
        """測試 ZMap 整合初始化"""
        assert hasattr(zmap_integration, 'available_tools')
        assert hasattr(zmap_integration, 'compliance_rules')
        assert hasattr(zmap_integration, 'common_proxy_ports')
        assert isinstance(zmap_integration.available_tools, dict)
    
    @pytest.mark.asyncio
    async def test_check_compliance(self, zmap_integration):
        """測試合規性檢查"""
        # 測試內部網路（應該通過）
        result = await zmap_integration._compliance_check(["192.168.1.0/24"], 1000)
        assert result is True
        
        # 測試本地主機（應該通過）
        result = await zmap_integration._compliance_check(["127.0.0.1"], 1000)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_scan_range_simulation(self, zmap_integration):
        """測試範圍掃描模擬"""
        # 使用模擬模式測試
        ip_ranges = ["192.168.1.0/28"]
        ports = [80, 8080]
        
        with patch.object(zmap_integration, '_execute_scan') as mock_scan:
            from src.proxy_manager.zmap_integration import ScanResult, ScanTarget
            from datetime import datetime
            mock_result = ScanResult(
                target=ScanTarget(ip_range="192.168.1.0/28", ports=[80, 8080]),
                open_ports=[("192.168.1.1", 80), ("192.168.1.2", 8080)],
                scan_time=datetime.now(),
                duration=1.0,
                total_hosts=16,
                responsive_hosts=2,
                scan_rate=1000.0
            )
            mock_scan.return_value = mock_result
            
            with patch.object(zmap_integration, '_compliance_check', return_value=True):
                results = await zmap_integration.scan_for_proxies(ip_ranges, ports)
                
                assert isinstance(results, list)
                assert len(results) > 0
                
                # 檢查結果格式
                for proxy in results:
                    assert isinstance(proxy, ProxyNode)
                    assert proxy.host is not None
                    assert proxy.port in [80, 8080]
                    assert proxy.protocol in [ProxyProtocol.HTTP, ProxyProtocol.HTTPS]


class TestIntelligentTargetDiscovery:
    """智能目標發現測試"""
    
    @pytest.fixture
    def target_discovery(self):
        """目標發現實例"""
        zmap_integration = ZMapIntegration()
        return IntelligentTargetDiscovery(zmap_integration)
    
    def test_target_discovery_init(self, target_discovery):
        """測試目標發現初始化"""
        assert hasattr(target_discovery, 'zmap')
        assert hasattr(target_discovery, 'config')
        assert hasattr(target_discovery, 'proxy_provider_asns')
    
    @pytest.mark.asyncio
    async def test_generate_smart_targets_simulation(self, target_discovery):
        """測試智能目標生成模擬"""
        # 模擬方法調用
        with patch.object(target_discovery, 'discover_targets_from_shodan', return_value=["192.168.1.1/32"]):
            with patch.object(target_discovery, 'discover_targets_from_censys', return_value=["192.168.1.2/32"]):
                targets = await target_discovery.generate_smart_targets(
                    ["192.168.1.0/24"], 
                    intelligence_sources=['shodan', 'censys']
                )
                
                assert isinstance(targets, list)
                assert len(targets) >= 1
                
                for target in targets:
                    assert isinstance(target, str)
                    assert "/" in target or "." in target


class TestEnhancedGeolocationDetector:
    """增強地理位置檢測測試"""
    
    @pytest.fixture
    def geo_detector(self):
        """地理位置檢測器實例"""
        return EnhancedGeolocationDetector()
    
    def test_geo_detector_init(self, geo_detector):
        """測試地理位置檢測器初始化"""
        assert hasattr(geo_detector, 'cache')
        assert hasattr(geo_detector, 'config')
        assert hasattr(geo_detector, 'api_limits')
    
    @pytest.mark.asyncio
    async def test_detect_location_simulation(self, geo_detector):
        """測試地理位置檢測模擬"""
        # 模擬地理位置檢測結果
        mock_geo_info = GeolocationInfo(
            ip="8.8.8.8",
            country="US",
            country_code="US",
            city="Mountain View",
            latitude=37.4056,
            longitude=-122.0775
        )
        
        with patch.object(geo_detector, 'detect_location', return_value=mock_geo_info):
            geo_info = await geo_detector.detect_location("8.8.8.8")
            
            assert isinstance(geo_info, GeolocationInfo)
            assert geo_info.ip == "8.8.8.8"
            assert geo_info.country_code is not None
            assert geo_info.latitude is not None
            assert geo_info.longitude is not None
    
    @pytest.mark.asyncio
    async def test_batch_detect_location(self, geo_detector):
        """測試批量地理位置檢測"""
        ips = ["8.8.8.8", "1.1.1.1", "208.67.222.222"]
        
        with patch.object(geo_detector, 'detect_location') as mock_detect:
            mock_detect.side_effect = [
                GeolocationInfo(ip="8.8.8.8", country="US", city="Mountain View", latitude=37.4056, longitude=-122.0775),
                GeolocationInfo(ip="1.1.1.1", country="US", city="San Francisco", latitude=37.7749, longitude=-122.4194),
                GeolocationInfo(ip="208.67.222.222", country="US", city="San Francisco", latitude=37.7749, longitude=-122.4194)
            ]
            results = await geo_detector.batch_detect_locations(ips)
            
            assert isinstance(results, dict)
            assert len(results) == len(ips)
            
            for ip in ips:
                if ip in results:
                    result = results[ip]
                    assert isinstance(result, GeolocationInfo)
                    assert result.ip == ip


class TestIntelligentProxyDetector:
    """智能代理檢測測試"""
    
    @pytest.fixture
    def intelligent_detector(self):
        """智能檢測器實例"""
        return IntelligentProxyDetector()
    
    def test_intelligent_detector_init(self, intelligent_detector):
        """測試智能檢測器初始化"""
        assert hasattr(intelligent_detector, 'config')
        assert hasattr(intelligent_detector, 'test_urls')
        assert len(intelligent_detector.test_urls) > 0
    
    @pytest.mark.asyncio
    async def test_detect_proxy_simulation(self, intelligent_detector):
        """測試代理檢測模擬"""
        proxy = ProxyNode(
            host="127.0.0.1",
            port=8080,
            protocol=ProxyProtocol.HTTP
        )
        
        with patch.object(intelligent_detector, '_test_basic_connectivity', return_value={"working": True, "response_time": 0.5}):
            with patch.object(intelligent_detector, '_test_anonymity', return_value={"level": AnonymityLevel.ELITE, "ip_leaked": False, "headers": {}}):
                result = await intelligent_detector.detect_proxy(proxy, comprehensive=False)
                
                assert isinstance(result, DetectionResult)
                assert result.proxy == proxy
                assert isinstance(result.is_working, bool)
                assert 0 <= result.success_rate <= 1
                assert isinstance(result.anonymity_level, AnonymityLevel)
    
    @pytest.mark.asyncio
    async def test_performance_benchmark_simulation(self, intelligent_detector):
        """測試性能基準測試模擬"""
        proxy = ProxyNode(
            host="127.0.0.1",
            port=8080,
            protocol=ProxyProtocol.HTTP
        )
        
        # 模擬基準測試結果
        mock_result = BenchmarkResult(
            proxy=proxy,
            latency=100.0,
            download_speed=1000.0,
            upload_speed=500.0
        )
        
        with patch.object(intelligent_detector, 'benchmark_proxy', return_value=mock_result):
            result = await intelligent_detector.benchmark_proxy(proxy)
            
            assert isinstance(result, BenchmarkResult)
            assert result.proxy == proxy
            assert result.latency >= 0
            assert result.download_speed >= 0
            assert result.upload_speed >= 0


class TestProxyQualityAssessor:
    """代理質量評估測試"""
    
    @pytest.fixture
    def quality_assessor(self):
        """質量評估器實例"""
        return ProxyQualityAssessor()
    
    def test_quality_assessor_init(self, quality_assessor):
        """測試質量評估器初始化"""
        assert hasattr(quality_assessor, 'performance_history')
        assert hasattr(quality_assessor, 'weights')
        assert isinstance(quality_assessor.weights, dict)
    
    def test_assess_quality(self, quality_assessor):
        """測試質量評估"""
        proxy = ProxyNode(
            host="127.0.0.1",
            port=8080,
            protocol=ProxyProtocol.HTTP,
            status=ProxyStatus.ACTIVE,
            anonymity=AnonymityLevel.ELITE
        )
        # 設置響應時間
        proxy.metrics.response_time_ms = 100
        
        detection_result = DetectionResult(
            proxy=proxy,
            is_working=True,
            success_rate=0.9,
            anonymity_level=AnonymityLevel.ELITE
        )
        
        benchmark_result = BenchmarkResult(
            proxy=proxy,
            latency=100.0,
            download_speed=1000.0,
            upload_speed=500.0,
            concurrent_connections=10
        )
        
        quality_metrics = quality_assessor.assess_proxy_quality(
            proxy, detection_result, benchmark_result
        )
        
        assert isinstance(quality_metrics, QualityMetrics)
        assert isinstance(quality_metrics.quality_grade, QualityGrade)
        assert 0 <= quality_metrics.overall_score <= 100
        assert isinstance(quality_metrics.performance_score, (int, float))
        assert isinstance(quality_metrics.reliability_score, (int, float))
        assert isinstance(quality_metrics.security_score, (int, float))
    
    def test_batch_assess_quality(self, quality_assessor):
        """測試批量質量評估"""
        proxies_data = []
        
        for i in range(3):
            proxy = ProxyNode(
                host=f"127.0.0.{i+1}",
                port=8080,
                protocol=ProxyProtocol.HTTP,
                status=ProxyStatus.ACTIVE
            )
            
            detection_result = DetectionResult(
                proxy=proxy,
                is_working=True,
                success_rate=0.8,
                anonymity_level=AnonymityLevel.ANONYMOUS
            )
            
            proxies_data.append((proxy, detection_result, None))
        
        quality_metrics_list = quality_assessor.batch_assess_quality(proxies_data)
        
        assert isinstance(quality_metrics_list, list)
        assert len(quality_metrics_list) == 3
        
        for metrics in quality_metrics_list:
            assert isinstance(metrics, QualityMetrics)
            assert isinstance(metrics.quality_grade, QualityGrade)


class TestEnhancedProxyScanner:
    """增強代理掃描器測試"""
    
    @pytest.fixture
    def enhanced_scanner(self):
        """增強掃描器實例"""
        return EnhancedProxyScanner(
            max_concurrent=10,
            timeout=5.0
        )
    
    def test_enhanced_scanner_init(self, enhanced_scanner):
        """測試增強掃描器初始化"""
        assert enhanced_scanner.max_concurrent == 10
        assert enhanced_scanner.timeout == 5.0
        assert hasattr(enhanced_scanner, 'basic_scanner')
        assert hasattr(enhanced_scanner, 'intelligent_detector')
        assert hasattr(enhanced_scanner, 'geolocation_detector')
        assert hasattr(enhanced_scanner, 'quality_assessor')
        assert hasattr(enhanced_scanner, 'zmap_integration')
        assert hasattr(enhanced_scanner, 'target_discovery')
    
    @pytest.mark.asyncio
    async def test_comprehensive_scan_with_existing_proxies(self, enhanced_scanner):
        """測試使用現有代理的綜合掃描"""
        # 創建測試代理
        test_proxies = [
            ProxyNode(
                host="127.0.0.1",
                port=8080,
                protocol=ProxyProtocol.HTTP
            ),
            ProxyNode(
                host="127.0.0.1",
                port=1080,
                protocol=ProxyProtocol.SOCKS5
            )
        ]
        
        # 模擬所有組件
        with patch.object(enhanced_scanner.basic_scanner, 'scan_proxy_batch') as mock_scan, \
             patch.object(enhanced_scanner.intelligent_detector, 'detect_proxy') as mock_detect, \
             patch.object(enhanced_scanner.geolocation_detector, 'batch_detect_locations') as mock_geo, \
             patch.object(enhanced_scanner.quality_assessor, 'batch_assess_quality') as mock_quality:
            
            # 設置模擬返回值
            mock_scan.return_value = [
                ProxyNode(
                    host="127.0.0.1",
                    port=8080,
                    protocol=ProxyProtocol.HTTP,
                    status=ProxyStatus.ACTIVE
                )
            ]
            
            mock_detect.return_value = DetectionResult(
                proxy=test_proxies[0],
                is_working=True,
                response_time=0.5,
                anonymity_level=AnonymityLevel.ELITE,
                success_rate=0.9
            )
            
            mock_geo.return_value = {
                "127.0.0.1": GeolocationInfo(
                    ip="127.0.0.1",
                    country="US",
                    city="San Francisco",
                    region="CA",
                    latitude=37.7749,
                    longitude=-122.4194
                )
            }
            
            mock_quality.return_value = [
                QualityMetrics(
                    quality_grade=QualityGrade.GOOD,
                    overall_score=85,
                    performance_score=80,
                    reliability_score=90,
                    security_score=85
                )
            ]
            
            # 執行綜合掃描
            results = await enhanced_scanner.comprehensive_scan(
                existing_proxies=test_proxies,
                enable_zmap=False,
                enable_intelligence=True,
                enable_quality_assessment=True
            )
            
            # 驗證結果
            assert isinstance(results, dict)
            assert "analyzed_proxies" in results
            assert "detection_results" in results
            assert "geographic_info" in results
            assert "quality_metrics" in results
            assert "statistics" in results
            
            # 驗證統計信息
            stats = enhanced_scanner.get_enhanced_statistics()
            assert isinstance(stats, dict)
            assert "total_analyzed" in stats
            assert "high_quality_count" in stats
    
    def test_get_enhanced_statistics(self, enhanced_scanner):
        """測試獲取增強統計信息"""
        # 設置一些測試數據
        enhanced_scanner.enhanced_stats["total_discovered"] = 100
        enhanced_scanner.enhanced_stats["total_analyzed"] = 80
        enhanced_scanner.enhanced_stats["high_quality_count"] = 20
        
        stats = enhanced_scanner.get_enhanced_statistics()
        
        assert isinstance(stats, dict)
        assert stats["total_discovered"] == 100
        assert stats["total_analyzed"] == 80
        assert stats["high_quality_count"] == 20
        assert "discovery_to_analysis_rate" in stats
        assert "high_quality_rate" in stats
        
        # 檢查計算的比率
        assert stats["discovery_to_analysis_rate"] == 80.0
        assert stats["high_quality_rate"] == 25.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])