"""代理管理器配置模組

統一管理所有代理相關配置：
- API 金鑰管理
- 掃描參數配置
- 驗證規則設定
- 性能調優參數
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
from datetime import timedelta

from .models import ProxyProtocol, ProxyAnonymity, ProxySpeed

logger = logging.getLogger(__name__)


@dataclass
class ApiConfig:
    """API 配置"""
    shodan_api_key: Optional[str] = None
    censys_api_id: Optional[str] = None
    censys_api_secret: Optional[str] = None
    proxyscrape_api_key: Optional[str] = None
    github_token: Optional[str] = None
    ipapi_key: Optional[str] = None


@dataclass
class ScannerConfig:
    """掃描器配置"""
    max_concurrent: int = 100
    timeout: float = 10.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    enable_fast_scan: bool = True
    fast_scan_timeout: float = 3.0
    fast_scan_concurrent: int = 1000
    
    # 測試 URL 配置
    test_urls: List[str] = None
    anonymity_test_urls: List[str] = None
    
    def __post_init__(self):
        if self.test_urls is None:
            self.test_urls = [
                "http://httpbin.org/ip",
                "https://api.ipify.org?format=json",
                "http://icanhazip.com",
                "https://checkip.amazonaws.com",
                "http://ip-api.com/json"
            ]
        
        if self.anonymity_test_urls is None:
            self.anonymity_test_urls = [
                "http://httpbin.org/headers",
                "https://httpbin.org/headers"
            ]


@dataclass
class ValidationConfig:
    """驗證配置"""
    min_speed: ProxySpeed = ProxySpeed.SLOW
    required_anonymity: ProxyAnonymity = ProxyAnonymity.TRANSPARENT
    max_response_time: float = 10.0
    required_countries: Optional[List[str]] = None
    blocked_countries: Optional[List[str]] = None
    required_protocols: Optional[List[ProxyProtocol]] = None
    enable_geolocation_check: bool = True
    enable_anonymity_check: bool = True
    enable_speed_test: bool = True
    
    def __post_init__(self):
        if self.blocked_countries is None:
            self.blocked_countries = ["CN", "RU"]  # 示例配置


@dataclass
class FetcherConfig:
    """獲取器配置"""
    enable_proxyscrape: bool = True
    enable_github: bool = True
    enable_shodan: bool = False  # 需要 API 金鑰
    enable_censys: bool = False  # 需要 API 金鑰
    enable_web_scraping: bool = True
    
    # 獲取限制
    max_proxies_per_source: int = 1000
    fetch_interval_minutes: int = 60
    
    # GitHub 配置
    github_sources: List[Dict[str, Any]] = None
    
    # ProxyScrape 配置
    proxyscrape_protocols: List[str] = None
    
    def __post_init__(self):
        if self.github_sources is None:
            self.github_sources = [
                {
                    "name": "proxifly/free-proxy-list",
                    "files": ["proxies/http.txt", "proxies/https.txt", "proxies/socks4.txt", "proxies/socks5.txt"],
                    "format": "txt"
                },
                {
                    "name": "TheSpeedX/PROXY-List",
                    "files": ["http.txt", "socks4.txt", "socks5.txt"],
                    "format": "txt"
                },
                {
                    "name": "ShiftyTR/Proxy-List",
                    "files": ["http.txt", "https.txt", "socks4.txt", "socks5.txt"],
                    "format": "txt"
                }
            ]
        
        if self.proxyscrape_protocols is None:
            self.proxyscrape_protocols = ["http", "socks4", "socks5"]


@dataclass
class StorageConfig:
    """存儲配置"""
    data_directory: str = "data/proxies"
    backup_directory: str = "data/backups"
    export_formats: List[str] = None
    auto_backup: bool = True
    backup_interval_hours: int = 24
    max_backup_files: int = 7
    
    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["json", "csv", "txt"]


@dataclass
class LoggingConfig:
    """日誌配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "logs/proxy_manager.log"
    max_file_size: str = "10MB"
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True


@dataclass
class PerformanceConfig:
    """性能配置"""
    cache_size: int = 10000
    cache_ttl_minutes: int = 30
    enable_connection_pooling: bool = True
    connection_pool_size: int = 100
    dns_cache_ttl: int = 300
    enable_compression: bool = True
    
    # 記憶體管理
    max_memory_usage_mb: int = 512
    gc_threshold: int = 1000


class ProxyManagerConfig:
    """代理管理器主配置類"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "config/proxy_manager.yaml"
        
        # 初始化各個配置模組
        self.api = ApiConfig()
        self.scanner = ScannerConfig()
        self.validation = ValidationConfig()
        self.fetcher = FetcherConfig()
        self.storage = StorageConfig()
        self.logging = LoggingConfig()
        self.performance = PerformanceConfig()
        
        # 載入配置
        self.load_config()
        self._load_environment_variables()
    
    def load_config(self, config_file: Optional[str] = None) -> bool:
        """載入配置文件"""
        if config_file:
            self.config_file = config_file
        
        config_path = Path(self.config_file)
        
        if not config_path.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默認配置")
            self.save_config()  # 創建默認配置文件
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            self._update_from_dict(config_data)
            logger.info(f"✅ 配置文件載入成功: {config_path}")
            return True
        
        except Exception as e:
            logger.error(f"❌ 配置文件載入失敗: {e}")
            return False
    
    def save_config(self, config_file: Optional[str] = None) -> bool:
        """保存配置到文件"""
        if config_file:
            self.config_file = config_file
        
        config_path = Path(self.config_file)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            config_data = self.to_dict()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                    yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True, indent=2)
                else:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 配置文件保存成功: {config_path}")
            return True
        
        except Exception as e:
            logger.error(f"❌ 配置文件保存失敗: {e}")
            return False
    
    def _load_environment_variables(self):
        """從環境變量載入敏感配置"""
        # API 金鑰
        if os.getenv('SHODAN_API_KEY'):
            self.api.shodan_api_key = os.getenv('SHODAN_API_KEY')
        
        if os.getenv('CENSYS_API_ID'):
            self.api.censys_api_id = os.getenv('CENSYS_API_ID')
        
        if os.getenv('CENSYS_API_SECRET'):
            self.api.censys_api_secret = os.getenv('CENSYS_API_SECRET')
        
        if os.getenv('PROXYSCRAPE_API_KEY'):
            self.api.proxyscrape_api_key = os.getenv('PROXYSCRAPE_API_KEY')
        
        if os.getenv('GITHUB_TOKEN'):
            self.api.github_token = os.getenv('GITHUB_TOKEN')
        
        if os.getenv('IPAPI_KEY'):
            self.api.ipapi_key = os.getenv('IPAPI_KEY')
        
        # 其他環境變量
        if os.getenv('PROXY_MANAGER_LOG_LEVEL'):
            self.logging.level = os.getenv('PROXY_MANAGER_LOG_LEVEL')
        
        if os.getenv('PROXY_MANAGER_DATA_DIR'):
            self.storage.data_directory = os.getenv('PROXY_MANAGER_DATA_DIR')
    
    def _update_from_dict(self, config_data: Dict[str, Any]):
        """從字典更新配置"""
        if 'api' in config_data:
            self._update_dataclass(self.api, config_data['api'])
        
        if 'scanner' in config_data:
            self._update_dataclass(self.scanner, config_data['scanner'])
        
        if 'validation' in config_data:
            self._update_dataclass(self.validation, config_data['validation'])
        
        if 'fetcher' in config_data:
            self._update_dataclass(self.fetcher, config_data['fetcher'])
        
        if 'storage' in config_data:
            self._update_dataclass(self.storage, config_data['storage'])
        
        if 'logging' in config_data:
            self._update_dataclass(self.logging, config_data['logging'])
        
        if 'performance' in config_data:
            self._update_dataclass(self.performance, config_data['performance'])
    
    def _update_dataclass(self, obj, data: Dict[str, Any]):
        """更新 dataclass 對象"""
        for key, value in data.items():
            if hasattr(obj, key):
                # 處理枚舉類型
                if key in ['min_speed', 'required_anonymity'] and isinstance(value, str):
                    if key == 'min_speed':
                        setattr(obj, key, ProxySpeed[value.upper()])
                    elif key == 'required_anonymity':
                        setattr(obj, key, ProxyAnonymity[value.upper()])
                elif key == 'required_protocols' and isinstance(value, list):
                    protocols = [ProxyProtocol[p.upper()] for p in value if hasattr(ProxyProtocol, p.upper())]
                    setattr(obj, key, protocols)
                else:
                    setattr(obj, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        def convert_dataclass(obj):
            result = asdict(obj)
            # 處理枚舉類型
            for key, value in result.items():
                if hasattr(value, 'name'):
                    result[key] = value.name.lower()
                elif isinstance(value, list) and value and hasattr(value[0], 'name'):
                    result[key] = [v.name.lower() for v in value]
            return result
        
        return {
            'api': convert_dataclass(self.api),
            'scanner': convert_dataclass(self.scanner),
            'validation': convert_dataclass(self.validation),
            'fetcher': convert_dataclass(self.fetcher),
            'storage': convert_dataclass(self.storage),
            'logging': convert_dataclass(self.logging),
            'performance': convert_dataclass(self.performance)
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """獲取 API 配置字典"""
        return {
            'shodan_api_key': self.api.shodan_api_key,
            'censys_api_id': self.api.censys_api_id,
            'censys_api_secret': self.api.censys_api_secret,
            'proxyscrape_api_key': self.api.proxyscrape_api_key,
            'github_token': self.api.github_token,
            'ipapi_key': self.api.ipapi_key
        }
    
    def validate_config(self) -> List[str]:
        """驗證配置有效性"""
        errors = []
        
        # 檢查必要目錄
        try:
            Path(self.storage.data_directory).mkdir(parents=True, exist_ok=True)
            Path(self.storage.backup_directory).mkdir(parents=True, exist_ok=True)
            if self.logging.file_path:
                Path(self.logging.file_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(f"目錄創建失敗: {e}")
        
        # 檢查數值範圍
        if self.scanner.max_concurrent <= 0:
            errors.append("scanner.max_concurrent 必須大於 0")
        
        if self.scanner.timeout <= 0:
            errors.append("scanner.timeout 必須大於 0")
        
        if self.performance.cache_size <= 0:
            errors.append("performance.cache_size 必須大於 0")
        
        # 檢查 API 金鑰（如果啟用相應功能）
        if self.fetcher.enable_shodan and not self.api.shodan_api_key:
            errors.append("啟用 Shodan 但未配置 API 金鑰")
        
        if self.fetcher.enable_censys and (not self.api.censys_api_id or not self.api.censys_api_secret):
            errors.append("啟用 Censys 但未配置 API 金鑰")
        
        return errors
    
    def get_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        return {
            "config_file": self.config_file,
            "api_keys_configured": {
                "shodan": bool(self.api.shodan_api_key),
                "censys": bool(self.api.censys_api_id and self.api.censys_api_secret),
                "proxyscrape": bool(self.api.proxyscrape_api_key),
                "github": bool(self.api.github_token),
                "ipapi": bool(self.api.ipapi_key)
            },
            "enabled_fetchers": {
                "proxyscrape": self.fetcher.enable_proxyscrape,
                "github": self.fetcher.enable_github,
                "shodan": self.fetcher.enable_shodan,
                "censys": self.fetcher.enable_censys,
                "web_scraping": self.fetcher.enable_web_scraping
            },
            "scanner_settings": {
                "max_concurrent": self.scanner.max_concurrent,
                "timeout": self.scanner.timeout,
                "fast_scan_enabled": self.scanner.enable_fast_scan
            },
            "validation_settings": {
                "min_speed": self.validation.min_speed.name,
                "required_anonymity": self.validation.required_anonymity.name,
                "geolocation_check": self.validation.enable_geolocation_check,
                "anonymity_check": self.validation.enable_anonymity_check
            }
        }


# 全局配置實例
_global_config: Optional[ProxyManagerConfig] = None


def get_config() -> ProxyManagerConfig:
    """獲取全局配置實例"""
    global _global_config
    if _global_config is None:
        _global_config = ProxyManagerConfig()
    return _global_config


def set_config(config: ProxyManagerConfig):
    """設置全局配置實例"""
    global _global_config
    _global_config = config


def load_config_from_file(config_file: str) -> ProxyManagerConfig:
    """從文件載入配置"""
    config = ProxyManagerConfig(config_file)
    set_config(config)
    return config