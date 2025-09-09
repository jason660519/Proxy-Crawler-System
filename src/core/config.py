#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核心配置模組

此模組提供系統的核心配置功能，包括：
- 配置載入和管理
- 環境變數處理
- 配置驗證
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class Config(BaseModel):
    """系統配置類
    
    管理系統的所有配置項目。
    """
    
    # 應用基本配置
    app_name: str = Field(default="Proxy Crawler System", description="應用名稱")
    version: str = Field(default="1.0.0", description="版本號")
    debug: bool = Field(default=False, description="調試模式")
    
    # API 配置
    api_host: str = Field(default="localhost", description="API 主機")
    api_port: int = Field(default=8000, description="API 端口")
    
    # Redis 配置
    redis_host: str = Field(default="localhost", description="Redis 主機")
    redis_port: int = Field(default=6379, description="Redis 端口")
    redis_db: int = Field(default=0, description="Redis 資料庫")
    
    # 資料庫配置
    db_host: str = Field(default="localhost", description="資料庫主機")
    db_port: int = Field(default=5432, description="資料庫端口")
    db_name: str = Field(default="proxy_crawler", description="資料庫名稱")
    db_user: str = Field(default="postgres", description="資料庫用戶")
    db_password: str = Field(default="", description="資料庫密碼")
    
    # 日誌配置
    log_level: str = Field(default="INFO", description="日誌級別")
    log_file: Optional[str] = Field(default=None, description="日誌文件路徑")
    
    # 代理配置
    proxy_timeout: float = Field(default=10.0, description="代理超時時間")
    proxy_max_retries: int = Field(default=3, description="代理最大重試次數")
    
    class Config:
        """Pydantic 配置"""
        env_prefix = "PROXY_CRAWLER_"
        case_sensitive = False


# 全局配置實例
_config_instance: Optional[Config] = None


def load_config(config_path: Optional[str] = None) -> Config:
    """載入配置
    
    Args:
        config_path: 配置文件路徑，如果為 None 則使用默認路徑
    
    Returns:
        Config: 配置實例
    """
    global _config_instance
    
    if config_path is None:
        # 使用默認配置路徑
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "config" / "config.yaml"
    
    config_data = {}
    
    # 如果配置文件存在，則載入
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"載入配置文件失敗: {e}")
    
    # 創建配置實例
    _config_instance = Config(**config_data)
    return _config_instance


def get_config() -> Config:
    """獲取配置實例
    
    Returns:
        Config: 配置實例
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = load_config()
    
    return _config_instance


def reload_config(config_path: Optional[str] = None) -> Config:
    """重新載入配置
    
    Args:
        config_path: 配置文件路徑
    
    Returns:
        Config: 新的配置實例
    """
    global _config_instance
    _config_instance = None
    return load_config(config_path)