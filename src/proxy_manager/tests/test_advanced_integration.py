"""代理管理器高級整合測試

測試高級代理獲取器、掃描器和配置系統的整合功能。
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock

from src.proxy_manager.config import (
    ProxyManagerConfig, ApiConfig, ScannerConfig, 
    ValidationConfig, FetcherConfig
)
from src.proxy_manager.models import ProxyNode, ProxyProtocol, ProxyAnonymity, ProxyStatus
from src.proxy_manager.advanced_fetchers import (
    ProxyScrapeApiFetcher, GitHubProxyFetcher, 
    AdvancedProxyFetcherManager
)


class TestAdvancedFetchers:
    """測試高級代理獲取器。"""
    
    @pytest.fixture
    def api_config(self):
        """創建測試用的API配置。"""
        return ApiConfig(
            proxyscrape_api_key="test_key",
            github_token="test_token"
        )
    
    @pytest.mark.asyncio
    async def test_proxyscrape_fetcher(self, api_config):
        """測試ProxyScrape API獲取器。"""
        fetcher = ProxyScrapeApiFetcher(api_config.proxyscrape_api_key)
        
        # 模擬API回應
        mock_response = "1.2.3.4:8080\n5.6.7.8:3128\n"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aenter__.return_value.status = 200
            
            proxies = await fetcher.fetch_proxies(limit=10)
            
            # 驗證結果
            assert isinstance(proxies, list)
            # 檢查統計信息存在
            assert hasattr(fetcher, 'stats')
            assert isinstance(fetcher.stats, dict)
    
    @pytest.mark.asyncio
    async def test_github_fetcher(self, api_config):
        """測試GitHub代理獲取器。"""
        fetcher = GitHubProxyFetcher(api_config.github_token)
        
        # 模擬GitHub API回應
        mock_search_response = {
            "items": [
                {
                    "name": "proxy-list",
                    "download_url": "https://raw.githubusercontent.com/test/proxy-list/main/proxies.txt"
                }
            ]
        }
        
        mock_file_content = "1.2.3.4:8080\n5.6.7.8:3128\n"
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            # 第一次調用返回搜索結果
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_search_response)
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(return_value=mock_file_content)
            mock_get.return_value.__aenter__.return_value.status = 200
            
            proxies = await fetcher.fetch_proxies()
            
            assert isinstance(proxies, list)
            # 檢查統計信息存在
            assert hasattr(fetcher, 'stats')
            assert isinstance(fetcher.stats, dict)
    
    def test_advanced_fetcher_manager(self, api_config):
        """測試高級獲取器管理器。"""
        # 創建配置字典
        config_dict = {
            "proxyscrape_api_key": api_config.proxyscrape_api_key,
            "github_token": api_config.github_token
        }
        manager = AdvancedProxyFetcherManager(config_dict)
        
        # 檢查是否正確初始化獲取器
        assert hasattr(manager, 'fetchers')
        assert isinstance(manager.fetchers, list)


class TestConfig:
    """測試配置系統。"""
    
    def test_scanner_config_creation(self):
        """測試掃描器配置創建。"""
        config = ScannerConfig(
            max_concurrent=50,
            timeout=5.0,
            retry_attempts=2
        )
        
        assert config.max_concurrent == 50
        assert config.timeout == 5.0
        assert config.retry_attempts == 2
        assert isinstance(config.test_urls, list)
        assert len(config.test_urls) > 0
    
    def test_proxy_manager_config_save_load(self):
        """測試代理管理器配置的保存和載入。"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.api.proxyscrape_api_key = "test"
            config.scanner.max_concurrent = 5
            
            # 保存配置
            config.save_config(str(config_path))
            assert config_path.exists()
            
            # 載入配置
            loaded_config = ProxyManagerConfig(str(config_path))
            assert loaded_config.api.proxyscrape_api_key == "test"
            assert loaded_config.scanner.max_concurrent == 5
            
        finally:
            if config_path.exists():
                config_path.unlink()


class TestProxyManagerIntegration:
    """測試代理管理器整合功能。"""
    
    @pytest.fixture
    def temp_config(self):
        """創建臨時配置用於測試。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = ProxyManagerConfig()
            config.api.proxyscrape_api_key = "test_key"
            config.scanner.max_concurrent = 2
            config.validation.max_response_time = 5.0
            yield config
    
    def test_proxy_manager_config_initialization(self, temp_config):
        """測試代理管理器配置初始化。"""
        # 檢查配置是否正確初始化
        assert temp_config.api.proxyscrape_api_key == "test_key"
        assert temp_config.scanner.max_concurrent == 2
        assert temp_config.validation.max_response_time == 5.0
        
        # 檢查默認配置
        assert isinstance(temp_config.scanner.test_urls, list)
        assert len(temp_config.scanner.test_urls) > 0
    
    def test_config_components(self, temp_config):
        """測試配置組件。"""
        # 測試API配置
        assert hasattr(temp_config, 'api')
        assert isinstance(temp_config.api, ApiConfig)
        
        # 測試掃描器配置
        assert hasattr(temp_config, 'scanner')
        assert isinstance(temp_config.scanner, ScannerConfig)
        
        # 測試驗證配置
        assert hasattr(temp_config, 'validation')
        assert isinstance(temp_config.validation, ValidationConfig)
        
        # 測試獲取器配置
        assert hasattr(temp_config, 'fetcher')
        assert isinstance(temp_config.fetcher, FetcherConfig)
    
    def test_config_serialization(self, temp_config):
        """測試配置序列化。"""
        # 測試轉換為字典
        config_dict = temp_config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'api' in config_dict
        assert 'scanner' in config_dict
        assert 'validation' in config_dict
        assert 'fetcher' in config_dict