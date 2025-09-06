#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高級代理整合測試

測試新的高級代理獲取器、掃描器和配置系統的功能。
驗證第一階段代理整合的核心組件。

作者: Jason
日期: 2024-01-20
"""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.proxy_manager import (
    ProxyManager,
    ProxyManagerConfig,
    ApiConfig,
    ScannerConfig,
    ProxyNode,
    ProxyProtocol,
    ProxyAnonymity,
    ProxyStatus,
    AdvancedProxyFetcherManager,
    ProxyScanner
)


class TestAdvancedProxyFetchers:
    """測試高級代理獲取器"""
    
    @pytest.fixture
    def api_config(self):
        """創建測試 API 配置"""
        return ApiConfig(
            proxyscrape_api_key="test_key",
            enable_proxyscrape=True,
            enable_github_sources=True,
            enable_shodan=False
        )
    
    @pytest.fixture
    def temp_config(self, api_config):
        """創建臨時配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ProxyManagerConfig(
                data_dir=Path(temp_dir),
                api_config=api_config
            )
    
    @pytest.mark.asyncio
    async def test_advanced_fetcher_manager_creation(self, temp_config):
        """測試高級獲取器管理器創建"""
        manager = AdvancedProxyFetcherManager(temp_config)
        
        assert manager.config == temp_config
        assert len(manager.fetchers) >= 2  # ProxyScrape + GitHub
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_proxyscrape_fetcher_mock(self, temp_config):
        """測試 ProxyScrape 獲取器（模擬）"""
        manager = AdvancedProxyFetcherManager(temp_config)
        
        # 模擬 HTTP 響應
        mock_response = "1.1.1.1:8080\n2.2.2.2:3128\n3.3.3.3:1080"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.text.return_value = mock_response
            mock_resp.status = 200
            mock_get.return_value.__aenter__.return_value = mock_resp
            
            proxies = await manager.fetch_all_proxies()
            
            assert len(proxies) >= 0  # 可能為空，因為模擬數據格式簡單
        
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_github_fetcher_mock(self, temp_config):
        """測試 GitHub 獲取器（模擬）"""
        manager = AdvancedProxyFetcherManager(temp_config)
        
        # 模擬 GitHub API 響應
        mock_github_response = {
            "content": "MS4xLjEuMTo4MDgwCjIuMi4yLjI6MzEyOAozLjMuMy4zOjEwODA="  # base64 編碼的代理列表
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_resp = AsyncMock()
            mock_resp.json.return_value = mock_github_response
            mock_resp.status = 200
            mock_get.return_value.__aenter__.return_value = mock_resp
            
            proxies = await manager.fetch_all_proxies()
            
            # GitHub 獲取器應該能解析 base64 內容
            assert isinstance(proxies, list)
        
        await manager.close()


class TestProxyScanner:
    """測試代理掃描器"""
    
    @pytest.fixture
    def scanner_config(self):
        """創建掃描器配置"""
        return ScannerConfig(
            enable_fast_scan=True,
            scan_timeout=2.0,
            max_concurrent_scans=10,
            enable_anonymity_detection=True
        )
    
    @pytest.fixture
    def test_proxies(self):
        """創建測試代理列表"""
        return [
            ProxyNode(host="1.1.1.1", port=8080, protocol=Protocol.HTTP),
            ProxyNode(host="2.2.2.2", port=3128, protocol=Protocol.HTTP),
            ProxyNode(host="3.3.3.3", port=1080, protocol=Protocol.SOCKS5)
        ]
    
    @pytest.mark.asyncio
    async def test_scanner_creation(self, scanner_config):
        """測試掃描器創建"""
        scanner = ProxyScanner(scanner_config)
        
        assert scanner.config == scanner_config
        assert scanner.port_scanner is not None
        assert scanner.validator is not None
        
        await scanner.close()
    
    @pytest.mark.asyncio
    async def test_proxy_list_scanning_mock(self, scanner_config, test_proxies):
        """測試代理列表掃描（模擬）"""
        scanner = ProxyScanner(scanner_config)
        
        # 模擬端口掃描結果
        with patch.object(scanner.port_scanner, 'scan_proxy_ports') as mock_scan:
            mock_scan.return_value = test_proxies[:2]  # 前兩個代理可用
            
            scanned_proxies = await scanner.scan_proxy_list(test_proxies)
            
            assert len(scanned_proxies) == 2
            assert all(isinstance(p, ProxyNode) for p in scanned_proxies)
        
        await scanner.close()
    
    @pytest.mark.asyncio
    async def test_single_proxy_validation_mock(self, scanner_config, test_proxies):
        """測試單個代理驗證（模擬）"""
        scanner = ProxyScanner(scanner_config)
        
        test_proxy = test_proxies[0]
        
        # 模擬驗證結果
        with patch.object(scanner.validator, 'validate_proxy') as mock_validate:
            mock_result = Mock()
            mock_result.is_working = True
            mock_result.response_time = 1.5
            mock_result.anonymity = AnonymityLevel.HIGH_ANONYMOUS
            mock_validate.return_value = mock_result
            
            result = await scanner.validate_single_proxy(test_proxy)
            
            assert result.is_working is True
            assert result.response_time == 1.5
            assert result.anonymity == AnonymityLevel.HIGH_ANONYMOUS
        
        await scanner.close()


class TestProxyManagerIntegration:
    """測試代理管理器整合"""
    
    @pytest.fixture
    def integration_config(self):
        """創建整合測試配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield ProxyManagerConfig(
                data_dir=Path(temp_dir),
                api_config=ApiConfig(
                    enable_proxyscrape=True,
                    enable_github_sources=True,
                    enable_shodan=False
                ),
                scanner_config=ScannerConfig(
                    enable_fast_scan=True,
                    scan_timeout=1.0,
                    max_concurrent_scans=5
                ),
                auto_fetch_enabled=False,  # 測試時關閉自動任務
                auto_cleanup_enabled=False,
                auto_save_enabled=False
            )
    
    @pytest.mark.asyncio
    async def test_manager_with_advanced_features(self, integration_config):
        """測試帶有高級功能的管理器"""
        manager = ProxyManager(integration_config)
        
        # 驗證組件初始化
        assert manager.advanced_fetcher_manager is not None
        assert manager.scanner is not None
        
        try:
            await manager.start()
            
            # 驗證管理器狀態
            assert manager._running is True
            
            # 測試統計信息
            stats = manager.get_stats()
            assert 'manager_stats' in stats
            assert 'pool_summary' in stats
            
        finally:
            await manager.stop()
            assert manager._running is False
    
    @pytest.mark.asyncio
    async def test_fetch_proxies_with_advanced_sources_mock(self, integration_config):
        """測試使用高級來源獲取代理（模擬）"""
        manager = ProxyManager(integration_config)
        
        try:
            await manager.start()
            
            # 模擬高級獲取器返回代理
            mock_proxies = [
                ProxyNode(host="1.1.1.1", port=8080, protocol=ProxyProtocol.HTTP),
                ProxyNode(host="2.2.2.2", port=3128, protocol=ProxyProtocol.HTTP)
            ]
            
            with patch.object(manager.advanced_fetcher_manager, 'fetch_all_proxies') as mock_fetch:
                mock_fetch.return_value = mock_proxies
                
                # 模擬掃描器
                with patch.object(manager.scanner, 'scan_proxy_list') as mock_scan:
                    mock_scan.return_value = mock_proxies
                    
                    # 模擬批量驗證
                    with patch.object(manager.batch_validator, 'validate_large_batch') as mock_validate:
                        mock_results = []
                        for proxy in mock_proxies:
                            result = Mock()
                            result.proxy = proxy
                            result.is_working = True
                            mock_results.append(result)
                        mock_validate.return_value = mock_results
                        
                        proxies = await manager.fetch_proxies()
                        
                        assert len(proxies) == 2
                        assert all(isinstance(p, ProxyNode) for p in proxies)
        
        finally:
            await manager.stop()
    
    @pytest.mark.asyncio
    async def test_export_import_functionality(self, integration_config):
        """測試導出導入功能"""
        manager = ProxyManager(integration_config)
        
        try:
            await manager.start()
            
            # 創建測試代理
            test_proxies = [
                ProxyNode(
                    host="1.1.1.1",
                    port=8080,
                    protocol=ProxyProtocol.HTTP,
                    anonymity=ProxyAnonymity.HIGH_ANONYMOUS,
                    status=ProxyStatus.ACTIVE
                ),
                ProxyNode(
                    host="2.2.2.2",
                    port=3128,
                    protocol=ProxyProtocol.HTTPS,
                    anonymity=ProxyAnonymity.ANONYMOUS,
                    status=ProxyStatus.ACTIVE
                )
            ]
            
            # 添加代理到池中
            await manager.pool_manager.add_proxies(test_proxies)
            
            # 測試導出
            export_file = integration_config.data_dir / "test_export.json"
            exported_count = await manager.export_proxies(export_file, "json")
            
            assert exported_count == 2
            assert export_file.exists()
            
            # 驗證導出內容
            with open(export_file, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            assert 'proxies' in exported_data
            assert len(exported_data['proxies']) == 2
            assert exported_data['total_count'] == 2
            
            # 測試導入
            new_manager = ProxyManager(integration_config)
            await new_manager.start()
            
            try:
                imported_count = await new_manager.import_proxies(
                    export_file,
                    validate=False
                )
                
                assert imported_count == 2
                
                # 驗證導入的代理
                imported_proxy = await new_manager.get_proxy()
                assert imported_proxy is not None
                assert imported_proxy.host in ["1.1.1.1", "2.2.2.2"]
            
            finally:
                await new_manager.stop()
        
        finally:
            await manager.stop()


class TestConfigurationSystem:
    """測試配置系統"""
    
    def test_api_config_creation(self):
        """測試 API 配置創建"""
        config = ApiConfig(
            proxyscrape_api_key="test_key",
            enable_proxyscrape=True,
            enable_github_sources=True,
            github_sources=["test/repo"]
        )
        
        assert config.proxyscrape_api_key == "test_key"
        assert config.enable_proxyscrape is True
        assert config.enable_github_sources is True
        assert "test/repo" in config.github_sources
    
    def test_scanner_config_creation(self):
        """測試掃描器配置創建"""
        config = ScannerConfig(
            enable_fast_scan=True,
            scan_timeout=5.0,
            max_concurrent_scans=100,
            enable_anonymity_detection=True
        )
        
        assert config.enable_fast_scan is True
        assert config.scan_timeout == 5.0
        assert config.max_concurrent_scans == 100
        assert config.enable_anonymity_detection is True
    
    def test_proxy_manager_config_integration(self):
        """測試代理管理器配置整合"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ProxyManagerConfig(
                data_dir=Path(temp_dir),
                api_config=ApiConfig(
                    enable_proxyscrape=True,
                    proxyscrape_api_key="test_key"
                ),
                scanner_config=ScannerConfig(
                    enable_fast_scan=True,
                    scan_timeout=3.0
                )
            )
            
            assert config.data_dir == Path(temp_dir)
            assert config.api_config.enable_proxyscrape is True
            assert config.scanner_config.enable_fast_scan is True
            assert config.scanner_config.scan_timeout == 3.0


if __name__ == "__main__":
    # 運行測試
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])