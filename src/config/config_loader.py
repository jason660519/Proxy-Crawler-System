#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加載器模組

此模組負責加載和管理系統配置，支援：
- YAML 配置文件加載
- 環境變數覆蓋
- 配置驗證
- 動態配置更新

作者: Assistant
創建時間: 2024
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from loguru import logger
from pydantic import BaseModel, Field, validator

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class ServerConfig(BaseModel):
    """服務器配置模型"""
    host: str = Field(default="0.0.0.0", description="服務器主機地址")
    environment: str = Field(default="development", description="運行環境")
    debug: bool = Field(default=True, description="調試模式")
    
    @validator('environment')
    def validate_environment(cls, v):
        """驗證環境配置"""
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f"環境必須是 {allowed_envs} 之一")
        return v


class APIConfig(BaseModel):
    """API 配置模型"""
    port: int = Field(description="服務端口")
    workers: int = Field(default=1, description="工作進程數")
    reload: bool = Field(default=True, description="自動重載")
    log_level: str = Field(default="info", description="日誌級別")
    access_log: bool = Field(default=True, description="訪問日誌")
    
    @validator('port')
    def validate_port(cls, v):
        """驗證端口號"""
        if not 1 <= v <= 65535:
            raise ValueError("端口號必須在 1-65535 之間")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """驗證日誌級別"""
        allowed_levels = ['debug', 'info', 'warning', 'error', 'critical']
        if v.lower() not in allowed_levels:
            raise ValueError(f"日誌級別必須是 {allowed_levels} 之一")
        return v.lower()


class DatabaseConfig(BaseModel):
    """數據庫配置模型"""
    
    class PostgreSQLConfig(BaseModel):
        """PostgreSQL 配置"""
        host: str = Field(default="localhost")
        port: int = Field(default=5432)
        database: str = Field(description="數據庫名稱")
        username: str = Field(description="用戶名")
        password: str = Field(description="密碼")
        pool_size: int = Field(default=10)
        max_overflow: int = Field(default=20)
        pool_timeout: int = Field(default=30)
        pool_recycle: int = Field(default=3600)
    
    class RedisConfig(BaseModel):
        """Redis 配置"""
        host: str = Field(default="localhost")
        port: int = Field(default=6379)
        database: int = Field(default=0)
        password: Optional[str] = Field(default=None)
        max_connections: int = Field(default=10)
        socket_timeout: int = Field(default=5)
        socket_connect_timeout: int = Field(default=5)
    
    postgresql: PostgreSQLConfig
    redis: RedisConfig


class ETLConfig(BaseModel):
    """ETL 配置模型"""
    batch_size: int = Field(default=1000, description="批次大小")
    max_workers: int = Field(default=4, description="最大工作線程數")
    timeout: int = Field(default=300, description="超時時間")
    retry_attempts: int = Field(default=3, description="重試次數")
    retry_delay: int = Field(default=5, description="重試延遲")
    
    class ValidationConfig(BaseModel):
        """驗證配置"""
        strict_mode: bool = Field(default=True)
        max_errors: int = Field(default=100)
        error_threshold: float = Field(default=0.05)
    
    class SchedulerConfig(BaseModel):
        """調度器配置"""
        enabled: bool = Field(default=True)
        interval: int = Field(default=3600)
        max_concurrent_jobs: int = Field(default=2)
    
    validation: ValidationConfig
    scheduler: SchedulerConfig


class ProxyConfig(BaseModel):
    """代理配置模型"""
    
    class ValidationConfig(BaseModel):
        """驗證配置"""
        timeout: int = Field(default=10)
        test_urls: list = Field(default_factory=lambda: [
            "http://httpbin.org/ip",
            "https://httpbin.org/ip",
            "http://icanhazip.com"
        ])
        max_concurrent: int = Field(default=50)
    
    class ScoringConfig(BaseModel):
        """評分配置"""
        speed_weight: float = Field(default=0.4)
        reliability_weight: float = Field(default=0.3)
        anonymity_weight: float = Field(default=0.2)
        location_weight: float = Field(default=0.1)
    
    class FilteringConfig(BaseModel):
        """過濾配置"""
        min_speed: float = Field(default=1.0)
        min_reliability: float = Field(default=0.8)
        required_anonymity: str = Field(default="anonymous")
    
    validation: ValidationConfig
    scoring: ScoringConfig
    filtering: FilteringConfig


class AlertRule(BaseModel):
    """警報規則"""
    name: str
    condition: str
    severity: str
    cooldown: int


class MonitoringConfig(BaseModel):
    """監控配置模型"""
    
    class MetricsConfig(BaseModel):
        """指標配置"""
        enabled: bool = Field(default=True)
        collection_interval: int = Field(default=60)
        retention_days: int = Field(default=30)
    
    class AlertsConfig(BaseModel):
        """警報配置"""
        enabled: bool = Field(default=True)
        email_notifications: bool = Field(default=False)
        webhook_url: Optional[str] = Field(default=None)
        rules: list[AlertRule] = Field(default_factory=list)
    
    port: int = Field(default=8002)
    metrics: MetricsConfig
    alerts: AlertsConfig


class LoggingConfig(BaseModel):
    """日誌配置模型"""
    level: str = Field(default="INFO")
    format: str = Field(default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    class FileConfig(BaseModel):
        """文件日誌配置"""
        enabled: bool = Field(default=True)
        path: str = Field(default="logs")
        rotation: str = Field(default="1 day")
        retention: str = Field(default="7 days")
        compression: str = Field(default="gz")
    
    class ConsoleConfig(BaseModel):
        """控制台日誌配置"""
        enabled: bool = Field(default=True)
        colorize: bool = Field(default=True)
    
    file: FileConfig
    console: ConsoleConfig


class SecurityConfig(BaseModel):
    """安全配置模型"""
    
    class CORSConfig(BaseModel):
        """CORS 配置"""
        allow_origins: list = Field(default_factory=list)
        allow_methods: list = Field(default_factory=list)
        allow_headers: list = Field(default_factory=list)
        allow_credentials: bool = Field(default=True)
    
    class APIKeysConfig(BaseModel):
        """API 金鑰配置"""
        enabled: bool = Field(default=False)
        header_name: str = Field(default="X-API-Key")
        keys: list = Field(default_factory=list)
    
    class RateLimitingConfig(BaseModel):
        """速率限制配置"""
        enabled: bool = Field(default=True)
        requests_per_minute: int = Field(default=100)
        burst_size: int = Field(default=10)
    
    cors: CORSConfig
    api_keys: APIKeysConfig
    rate_limiting: RateLimitingConfig


class AppConfig(BaseModel):
    """應用程式完整配置模型"""
    server: ServerConfig
    main_api: APIConfig
    etl_api: APIConfig
    monitoring: APIConfig
    database: DatabaseConfig
    etl: ETLConfig
    proxy: ProxyConfig
    monitoring_config: MonitoringConfig = Field(alias="monitoring")
    logging: LoggingConfig
    security: SecurityConfig
    feature_flags: Dict[str, bool] = Field(default_factory=dict)


class ConfigLoader:
    """配置加載器"""
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """初始化配置加載器
        
        Args:
            config_path: 配置文件路徑，如果為 None 則使用默認路徑
        """
        self.config_path = self._resolve_config_path(config_path)
        self._config: Optional[AppConfig] = None
        
        # 配置日誌
        logger.remove()
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO"
        )
    
    def _resolve_config_path(self, config_path: Optional[Union[str, Path]]) -> Path:
        """解析配置文件路徑"""
        if config_path:
            return Path(config_path)
        
        # 嘗試多個可能的配置文件位置
        possible_paths = [
            Path("config/server_config.yaml"),
            Path("../config/server_config.yaml"),
            Path("../../config/server_config.yaml"),
            project_root / "config" / "server_config.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.resolve()
        
        # 如果都找不到，返回默認路徑
        return project_root / "config" / "server_config.yaml"
    
    def load_config(self, reload: bool = False) -> AppConfig:
        """加載配置
        
        Args:
            reload: 是否強制重新加載配置
            
        Returns:
            應用程式配置對象
        """
        if self._config is not None and not reload:
            return self._config
        
        try:
            logger.info(f"📖 正在加載配置文件: {self.config_path}")
            
            if not self.config_path.exists():
                logger.warning(f"⚠️ 配置文件不存在: {self.config_path}")
                logger.info("🔧 使用默認配置")
                return self._create_default_config()
            
            # 讀取 YAML 配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # 應用環境變數覆蓋
            config_data = self._apply_env_overrides(config_data)
            
            # 驗證並創建配置對象
            self._config = AppConfig(**config_data)
            
            logger.info("✅ 配置加載成功")
            return self._config
            
        except Exception as e:
            logger.error(f"❌ 配置加載失敗: {e}")
            logger.info("🔧 使用默認配置")
            return self._create_default_config()
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """應用環境變數覆蓋"""
        # 定義環境變數映射
        env_mappings = {
            'SERVER_HOST': ['server', 'host'],
            'SERVER_ENVIRONMENT': ['server', 'environment'],
            'SERVER_DEBUG': ['server', 'debug'],
            'MAIN_API_PORT': ['main_api', 'port'],
            'ETL_API_PORT': ['etl_api', 'port'],
            'MONITORING_PORT': ['monitoring', 'port'],
            'DB_HOST': ['database', 'postgresql', 'host'],
            'DB_PORT': ['database', 'postgresql', 'port'],
            'DB_NAME': ['database', 'postgresql', 'database'],
            'DB_USER': ['database', 'postgresql', 'username'],
            'DB_PASSWORD': ['database', 'postgresql', 'password'],
            'REDIS_HOST': ['database', 'redis', 'host'],
            'REDIS_PORT': ['database', 'redis', 'port'],
            'REDIS_PASSWORD': ['database', 'redis', 'password'],
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # 設置嵌套配置值
                current = config_data
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # 類型轉換
                final_key = config_path[-1]
                if env_var.endswith('_PORT'):
                    current[final_key] = int(env_value)
                elif env_var.endswith('_DEBUG'):
                    current[final_key] = env_value.lower() in ('true', '1', 'yes')
                else:
                    current[final_key] = env_value
                
                logger.info(f"🔄 環境變數覆蓋: {env_var} -> {'.'.join(config_path)}")
        
        return config_data
    
    def _create_default_config(self) -> AppConfig:
        """創建默認配置"""
        default_config = {
            'server': {
                'host': '0.0.0.0',
                'environment': 'development',
                'debug': True
            },
            'main_api': {
                'port': 8000,
                'workers': 1,
                'reload': True,
                'log_level': 'info',
                'access_log': True
            },
            'etl_api': {
                'port': 8001,
                'workers': 1,
                'reload': True,
                'log_level': 'info',
                'access_log': True
            },
            'monitoring': {
                'port': 8002,
                'workers': 1,
                'reload': True,
                'log_level': 'info',
                'access_log': True
            },
            'database': {
                'postgresql': {
                    'host': 'localhost',
                    'port': 5432,
                    'database': 'proxy_manager',
                    'username': 'postgres',
                    'password': 'password',
                    'pool_size': 10,
                    'max_overflow': 20,
                    'pool_timeout': 30,
                    'pool_recycle': 3600
                },
                'redis': {
                    'host': 'localhost',
                    'port': 6379,
                    'database': 0,
                    'password': None,
                    'max_connections': 10,
                    'socket_timeout': 5,
                    'socket_connect_timeout': 5
                }
            },
            'etl': {
                'batch_size': 1000,
                'max_workers': 4,
                'timeout': 300,
                'retry_attempts': 3,
                'retry_delay': 5,
                'validation': {
                    'strict_mode': True,
                    'max_errors': 100,
                    'error_threshold': 0.05
                },
                'scheduler': {
                    'enabled': True,
                    'interval': 3600,
                    'max_concurrent_jobs': 2
                }
            },
            'proxy': {
                'validation': {
                    'timeout': 10,
                    'test_urls': [
                        'http://httpbin.org/ip',
                        'https://httpbin.org/ip',
                        'http://icanhazip.com'
                    ],
                    'max_concurrent': 50
                },
                'scoring': {
                    'speed_weight': 0.4,
                    'reliability_weight': 0.3,
                    'anonymity_weight': 0.2,
                    'location_weight': 0.1
                },
                'filtering': {
                    'min_speed': 1.0,
                    'min_reliability': 0.8,
                    'required_anonymity': 'anonymous'
                }
            },
            'monitoring': {
                'port': 8002,
                'metrics': {
                    'enabled': True,
                    'collection_interval': 60,
                    'retention_days': 30
                },
                'alerts': {
                    'enabled': True,
                    'email_notifications': False,
                    'webhook_url': None,
                    'rules': []
                }
            },
            'logging': {
                'level': 'INFO',
                'format': '<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>',
                'file': {
                    'enabled': True,
                    'path': 'logs',
                    'rotation': '1 day',
                    'retention': '7 days',
                    'compression': 'gz'
                },
                'console': {
                    'enabled': True,
                    'colorize': True
                }
            },
            'security': {
                'cors': {
                    'allow_origins': [
                        'http://localhost:3000',
                        'http://localhost:8080',
                        'http://127.0.0.1:3000',
                        'http://127.0.0.1:8080'
                    ],
                    'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                    'allow_headers': ['*'],
                    'allow_credentials': True
                },
                'api_keys': {
                    'enabled': False,
                    'header_name': 'X-API-Key',
                    'keys': []
                },
                'rate_limiting': {
                    'enabled': True,
                    'requests_per_minute': 100,
                    'burst_size': 10
                }
            },
            'feature_flags': {
                'etl_pipeline': True,
                'monitoring_dashboard': True,
                'api_documentation': True,
                'metrics_export': True,
                'data_validation': True,
                'proxy_rotation': True,
                'geo_filtering': True,
                'speed_testing': True
            }
        }
        
        self._config = AppConfig(**default_config)
        return self._config
    
    def get_config(self) -> AppConfig:
        """獲取當前配置"""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def reload_config(self) -> AppConfig:
        """重新加載配置"""
        return self.load_config(reload=True)
    
    def save_config(self, config: AppConfig, backup: bool = True) -> bool:
        """保存配置到文件
        
        Args:
            config: 要保存的配置對象
            backup: 是否創建備份
            
        Returns:
            是否保存成功
        """
        try:
            # 創建備份
            if backup and self.config_path.exists():
                backup_path = self.config_path.with_suffix('.yaml.bak')
                backup_path.write_text(self.config_path.read_text(encoding='utf-8'), encoding='utf-8')
                logger.info(f"📋 配置備份已創建: {backup_path}")
            
            # 確保目錄存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 轉換為字典並保存
            config_dict = config.dict(by_alias=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
            
            logger.info(f"💾 配置已保存: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置保存失敗: {e}")
            return False
    
    @staticmethod
    def create_default_config(config_path: str) -> bool:
        """創建默認配置文件
        
        Args:
            config_path: 配置文件路徑
            
        Returns:
            是否創建成功
        """
        try:
            # 創建配置加載器實例
            loader = ConfigLoader(config_path)
            
            # 生成默認配置
            default_config = loader._create_default_config()
            
            # 保存配置
            return loader.save_config(default_config, backup=False)
            
        except Exception as e:
            logger.error(f"❌ 創建默認配置失敗: {e}")
            return False


# 全局配置加載器實例
config_loader = ConfigLoader()


def get_config() -> AppConfig:
    """獲取應用程式配置"""
    return config_loader.get_config()


def reload_config() -> AppConfig:
    """重新加載配置"""
    return config_loader.reload_config()


if __name__ == "__main__":
    # 測試配置加載
    config = get_config()
    print(f"✅ 配置加載測試成功")
    print(f"📡 主 API 端口: {config.main_api.port}")
    print(f"🔧 ETL API 端口: {config.etl_api.port}")
    print(f"📈 監控端口: {config.monitoring.port}")
    print(f"🗄️ 數據庫主機: {config.database.postgresql.host}")
    print(f"🔴 Redis 主機: {config.database.redis.host}")