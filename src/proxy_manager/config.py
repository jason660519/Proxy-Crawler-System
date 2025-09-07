"""代理管理器配置模組

提供統一的配置管理功能，包括：
- 主配置類 ProxyManagerConfig
- API 配置 ApiConfig
- 掃描器配置 ScannerConfig
- 配置驗證功能
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from pathlib import Path

# from .validators import ValidationConfig  # 暫時註解掉，ValidationConfig類尚未實現

@dataclass
class ValidationConfig:
    """驗證配置類"""
    timeout: int = 10
    max_retries: int = 3
    test_urls: List[str] = field(default_factory=lambda: [
        "http://httpbin.org/ip",
        "https://httpbin.org/ip"
    ])
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return getattr(self, key, default)
if TYPE_CHECKING:
    from .pools import PoolConfig

# 全局配置實例
_global_config: Optional['ProxyManagerConfig'] = None


@dataclass
class ApiConfig:
    """API 配置類"""
    proxyscrape_api_key: Optional[str] = None
    github_token: Optional[str] = None
    shodan_api_key: Optional[str] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return getattr(self, key, default)


@dataclass
class ScannerConfig:
    """掃描器配置類"""
    timeout: int = 5
    max_concurrent: int = 100
    port_ranges: List[tuple] = field(default_factory=lambda: [(80, 80), (8080, 8080), (3128, 3128)])
    scan_timeout: int = 3
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return getattr(self, key, default)


@dataclass
class ConfigValidation:
    """配置驗證類"""
    strict_mode: bool = False
    validate_on_load: bool = True
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return getattr(self, key, default)


class ProxyManagerConfig:
    """代理管理器主配置類
    
    整合所有子配置模組，提供統一的配置接口。
    支援從 YAML 檔案載入配置。
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """初始化配置
        
        Args:
            config_file: 配置檔案路徑，如果為 None 則使用預設配置
        """
        # 初始化子配置模組
        self.api = ApiConfig()
        self.scanner = ScannerConfig()
        self.validation = ValidationConfig()
        self._pool = None  # 延遲初始化以避免循環導入
        self.save_config = ConfigValidation()
        
        # 基本配置屬性
        self.data_dir = Path("data/proxy_manager")
        self.backup_dir = Path("data/backups")
        self.enable_free_proxy = True
        self.enable_json_file = True
        self.json_file_path = Path("proxy_list.json")
        self.batch_validation_size = 100
        
        # 自動任務配置
        self.auto_fetch_enabled = False
        self.auto_cleanup_enabled = False
        self.auto_save_enabled = True
        self.auto_fetch_interval = 3600  # 1小時
        self.auto_cleanup_interval = 1800  # 30分鐘
        self.auto_save_interval = 300  # 5分鐘
        self.auto_save_interval_minutes = 5  # 自動保存間隔（分鐘）
        self.auto_fetch_interval_hours = 6  # 自動獲取間隔（小時）
        self.auto_cleanup_interval_hours = 12  # 自動清理間隔（小時）
        
        # 如果提供了配置檔案，則載入配置
        if config_file:
            self.load_config(config_file)
    
    @property
    def pool(self):
        """延遲初始化PoolConfig以避免循環導入"""
        if self._pool is None:
            from .pools import PoolConfig
            self._pool = PoolConfig()
        return self._pool
    
    @pool.setter
    def pool(self, value):
        """設置pool配置"""
        self._pool = value
    
    def load_config(self, config_file: str) -> None:
        """從 YAML 檔案載入配置
        
        Args:
            config_file: 配置檔案路徑
        """
        try:
            config_path = Path(config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # 更新配置
                self._update_from_dict(config_data)
            else:
                print(f"配置檔案不存在: {config_file}，使用預設配置")
        except Exception as e:
            print(f"載入配置檔案失敗: {e}，使用預設配置")
    
    def _update_from_dict(self, config_data: Dict[str, Any]) -> None:
        """從字典更新配置
        
        Args:
            config_data: 配置字典
        """
        # 更新 API 配置
        if 'api' in config_data:
            api_config = config_data['api']
            self.api.proxyscrape_api_key = api_config.get('proxyscrape_api_key')
            self.api.github_token = api_config.get('github_token')
            self.api.shodan_api_key = api_config.get('shodan_api_key')
        
        # 更新掃描器配置
        if 'scanner' in config_data:
            scanner_config = config_data['scanner']
            self.scanner.timeout = scanner_config.get('timeout', self.scanner.timeout)
            self.scanner.max_concurrent = scanner_config.get('max_concurrent', self.scanner.max_concurrent)
        
        # 更新驗證配置
        if 'validation' in config_data:
            validation_config = config_data['validation']
            self.validation.timeout = validation_config.get('timeout', self.validation.timeout)
            self.validation.max_concurrent = validation_config.get('max_concurrent', self.validation.max_concurrent)
        
        # 更新基本配置
        if 'data_dir' in config_data:
            self.data_dir = Path(config_data['data_dir'])
        
        if 'backup_dir' in config_data:
            self.backup_dir = Path(config_data['backup_dir'])
        
        if 'enable_free_proxy' in config_data:
            self.enable_free_proxy = config_data['enable_free_proxy']
        
        if 'enable_json_file' in config_data:
            self.enable_json_file = config_data['enable_json_file']
        
        if 'json_file_path' in config_data:
            self.json_file_path = Path(config_data['json_file_path'])
        
        if 'batch_validation_size' in config_data:
            self.batch_validation_size = config_data['batch_validation_size']
        
        # 更新自動任務配置
        if 'auto_fetch_enabled' in config_data:
            self.auto_fetch_enabled = config_data['auto_fetch_enabled']
        
        if 'auto_cleanup_enabled' in config_data:
            self.auto_cleanup_enabled = config_data['auto_cleanup_enabled']
        
        if 'auto_save_enabled' in config_data:
            self.auto_save_enabled = config_data['auto_save_enabled']
        
        if 'auto_fetch_interval_hours' in config_data:
            self.auto_fetch_interval_hours = config_data['auto_fetch_interval_hours']
        
        if 'auto_cleanup_interval_hours' in config_data:
            self.auto_cleanup_interval_hours = config_data['auto_cleanup_interval_hours']
        
        if 'auto_save_interval_minutes' in config_data:
            self.auto_save_interval_minutes = config_data['auto_save_interval_minutes']
    
    def to_dict(self) -> Dict[str, Any]:
        """將配置轉換為字典
        
        Returns:
            配置字典
        """
        return {
            'api': {
                'proxyscrape_api_key': self.api.proxyscrape_api_key,
                'github_token': self.api.github_token,
                'shodan_api_key': self.api.shodan_api_key
            },
            'scanner': {
                'timeout': self.scanner.timeout,
                'max_concurrent': self.scanner.max_concurrent,
                'port_ranges': self.scanner.port_ranges,
                'scan_timeout': self.scanner.scan_timeout
            },
            'validation': {
                'timeout': self.validation.timeout,
                'max_concurrent': self.validation.max_concurrent,
                'test_urls': self.validation.test_urls,
                'retry_count': self.validation.retry_count
            },
            'data_dir': str(self.data_dir),
            'backup_dir': str(self.backup_dir),
            'enable_free_proxy': self.enable_free_proxy,
            'enable_json_file': self.enable_json_file,
            'json_file_path': str(self.json_file_path),
            'batch_validation_size': self.batch_validation_size,
            'auto_fetch_enabled': self.auto_fetch_enabled,
            'auto_cleanup_enabled': self.auto_cleanup_enabled,
            'auto_save_enabled': self.auto_save_enabled,
            'auto_fetch_interval_hours': self.auto_fetch_interval_hours,
            'auto_cleanup_interval_hours': self.auto_cleanup_interval_hours,
            'auto_save_interval_minutes': self.auto_save_interval_minutes
        }
    
    def save_to_file(self, config_file: str) -> None:
        """將配置保存到 YAML 檔案
        
        Args:
            config_file: 配置檔案路徑
        """
        try:
            config_path = Path(config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
            
            print(f"配置已保存到: {config_file}")
        except Exception as e:
            print(f"保存配置檔案失敗: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值
        
        Args:
            key: 配置鍵
            default: 預設值
            
        Returns:
            配置值
        """
        return getattr(self, key, default)
    
    def __repr__(self) -> str:
        """字串表示"""
        return f"ProxyManagerConfig(data_dir={self.data_dir}, enable_free_proxy={self.enable_free_proxy})"


def get_config() -> ProxyManagerConfig:
    """獲取全局配置實例
    
    Returns:
        ProxyManagerConfig: 全局配置實例
    """
    global _global_config
    if _global_config is None:
        _global_config = ProxyManagerConfig()
    return _global_config


def set_config(config: ProxyManagerConfig) -> None:
    """設置全局配置實例
    
    Args:
        config: 配置實例
    """
    global _global_config
    _global_config = config


def load_config_from_file(config_file: str) -> ProxyManagerConfig:
    """從檔案載入配置並設為全局配置
    
    Args:
        config_file: 配置檔案路徑
        
    Returns:
        ProxyManagerConfig: 載入的配置實例
    """
    config = ProxyManagerConfig(config_file)
    set_config(config)
    return config


def get_config() -> ProxyManagerConfig:
    """獲取全局配置實例
    
    Returns:
        ProxyManagerConfig: 全局配置實例
    """
    global _global_config
    if _global_config is None:
        _global_config = ProxyManagerConfig()
    return _global_config