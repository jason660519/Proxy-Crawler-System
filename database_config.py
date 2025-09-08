# database_config.py
"""智能資料庫配置管理器

此模組提供統一的資料庫連接配置管理，自動處理 Docker 和本地環境的差異，
支援同步和異步資料庫驅動的自動切換。
"""

import os
from typing import Literal
from src.config.settings import settings


class DatabaseConfig:
    """智能資料庫配置管理器
    
    自動檢測運行環境（Docker 或本地），並根據驅動類型生成對應的資料庫連接 URL。
    支援 PostgreSQL 和 Redis 的配置管理。
    
    Attributes:
        environment: 運行環境 ('docker' 或 'local')
        db_user: 資料庫使用者名稱
        db_password: 資料庫密碼
        db_name: 資料庫名稱
        redis_password: Redis 密碼（可選）
    """
    
    def __init__(self):
        """初始化配置管理器
        
        從環境變數讀取配置，如果未設定則使用預設值。
        """
        self.environment = settings.environment or self._detect_environment()
        self.db_user = settings.db_user
        self.db_password = settings.db_password
        self.db_name = settings.db_name
        self.redis_password = settings.redis_password
        
        # 驗證必要的配置
        if not self.db_password:
            raise ValueError("DB_PASSWORD 環境變數未設定")
    
    def _detect_environment(self) -> str:
        """自動檢測運行環境
        
        Returns:
            str: 'docker' 如果在 Docker 容器中運行，否則 'local'
        """
        # 檢查是否在 Docker 容器中
        if (os.path.exists('/.dockerenv') or 
            os.getenv('DOCKER_ENV') == 'true' or
            os.getenv('HOSTNAME', '').startswith('docker')):
            return 'docker'
        return 'local'
    
    def get_database_url(self, driver: Literal['sync', 'async'] = 'sync') -> str:
        """根據環境和驅動類型自動生成資料庫 URL
        
        Args:
            driver: 驅動類型，'sync' 為同步驅動，'async' 為異步驅動
            
        Returns:
            str: 完整的資料庫連接 URL
            
        Examples:
            >>> config = DatabaseConfig()
            >>> config.get_database_url('sync')
            'postgresql://proxyadmin:password@postgres_db:5432/proxypool'
            >>> config.get_database_url('async')
            'postgresql+asyncpg://proxyadmin:password@postgres_db:5432/proxypool'
        """
        # 根據環境決定主機名
        host = self._get_database_host()
        port = str(settings.db_port)
        
        # 根據驅動類型決定協議
        if driver == 'async':
            protocol = 'postgresql+asyncpg'
        else:
            protocol = 'postgresql'
        
        return f"{protocol}://{self.db_user}:{self.db_password}@{host}:{port}/{self.db_name}"
    
    def get_redis_url(self) -> str:
        """根據環境自動生成 Redis URL
        
        Returns:
            str: 完整的 Redis 連接 URL
            
        Examples:
            >>> config = DatabaseConfig()
            >>> config.get_redis_url()
            'redis://redis_cache:6379/0'
        """
        host = self._get_redis_host()
        port = str(settings.redis_port)
        db_index = str(settings.redis_db)
        
        if self.redis_password:
            return f"redis://:{self.redis_password}@{host}:{port}/{db_index}"
        else:
            return f"redis://{host}:{port}/{db_index}"
    
    def _get_database_host(self) -> str:
        """取得資料庫主機名
        
        Returns:
            str: 根據環境返回對應的主機名
        """
        if self.environment == 'docker':
            return os.getenv('DB_SERVICE', 'postgres_db')
        else:
            return settings.db_host
    
    def _get_redis_host(self) -> str:
        """取得 Redis 主機名
        
        Returns:
            str: 根據環境返回對應的主機名
        """
        if self.environment == 'docker':
            return os.getenv('REDIS_SERVICE', 'redis_cache')
        else:
            return settings.redis_host
    
    def get_connection_info(self) -> dict:
        """取得連接資訊摘要
        
        Returns:
            dict: 包含當前配置的摘要資訊
        """
        return {
            'environment': self.environment,
            'database_host': self._get_database_host(),
            'redis_host': self._get_redis_host(),
            'database_name': self.db_name,
            'database_user': self.db_user,
            'sync_url': self.get_database_url('sync'),
            'async_url': self.get_database_url('async'),
            'redis_url': self.get_redis_url()
        }
    
    def validate_connection(self) -> bool:
        """驗證配置的有效性
        
        Returns:
            bool: 如果配置有效則返回 True
            
        Raises:
            ValueError: 當必要的配置缺失時
        """
        required_fields = ['db_user', 'db_password', 'db_name']
        
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"必要的配置項 {field} 未設定")
        
        return True


# 全局配置實例
db_config = DatabaseConfig()


# 便利函數
def get_sync_database_url() -> str:
    """取得同步資料庫連接 URL
    
    Returns:
        str: 同步資料庫連接 URL
    """
    return db_config.get_database_url('sync')


def get_async_database_url() -> str:
    """取得異步資料庫連接 URL
    
    Returns:
        str: 異步資料庫連接 URL
    """
    return db_config.get_database_url('async')


def get_redis_url() -> str:
    """取得 Redis 連接 URL
    
    Returns:
        str: Redis 連接 URL
    """
    return db_config.get_redis_url()


if __name__ == "__main__":
    # 測試和展示配置
    print("=== 資料庫配置管理器測試 ===")
    print(f"檢測到的環境: {db_config.environment}")
    print(f"同步資料庫 URL: {get_sync_database_url()}")
    print(f"異步資料庫 URL: {get_async_database_url()}")
    print(f"Redis URL: {get_redis_url()}")
    print("\n=== 完整配置資訊 ===")
    
    import json
    config_info = db_config.get_connection_info()
    print(json.dumps(config_info, indent=2, ensure_ascii=False))