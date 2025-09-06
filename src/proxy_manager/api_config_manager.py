#!/usr/bin/env python3
"""
API 金鑰配置管理工具

提供統一的 API 金鑰配置和管理功能：
- 從環境變量載入 API 金鑰
- 從配置文件載入 API 金鑰
- 驗證 API 金鑰有效性
- 安全存儲 API 金鑰
"""

import os
import json
import base64
from typing import Dict, Optional, Any, List
from pathlib import Path
from dataclasses import dataclass, asdict
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


@dataclass
class ApiKeyInfo:
    """API 金鑰信息"""
    name: str
    key: str
    description: str = ""
    is_encrypted: bool = False
    last_updated: Optional[str] = None
    is_valid: bool = False


class ApiConfigManager:
    """API 配置管理器"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """初始化 API 配置管理器
        
        Args:
            config_dir: 配置目錄路徑
        """
        self.config_dir = config_dir or Path("config")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # API 金鑰配置文件
        self.keys_file = self.config_dir / "api_keys.json"
        self.encrypted_keys_file = self.config_dir / "api_keys.enc"
        
        # 加密相關
        self._encryption_key = None
        self._cipher_suite = None
        
        # 載入現有配置
        self.api_keys: Dict[str, ApiKeyInfo] = {}
        self._load_api_keys()
    
    def _get_encryption_key(self) -> bytes:
        """獲取加密金鑰"""
        if self._encryption_key is None:
            # 從環境變量或生成新的加密金鑰
            key_env = os.getenv("PROXY_MANAGER_ENCRYPTION_KEY")
            if key_env:
                self._encryption_key = key_env.encode()
            else:
                # 生成基於系統信息的加密金鑰
                import platform
                import getpass
                password = f"{platform.node()}-{getpass.getuser()}".encode()
                salt = b"proxy_manager_salt_2024"
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                self._encryption_key = base64.urlsafe_b64encode(kdf.derive(password))
        
        return self._encryption_key
    
    def _get_cipher_suite(self) -> Fernet:
        """獲取加密套件"""
        if self._cipher_suite is None:
            key = self._get_encryption_key()
            self._cipher_suite = Fernet(key)
        return self._cipher_suite
    
    def _load_api_keys(self):
        """載入 API 金鑰"""
        # 優先載入加密文件
        if self.encrypted_keys_file.exists():
            try:
                self._load_encrypted_keys()
                logger.info("✅ 從加密文件載入 API 金鑰")
                return
            except Exception as e:
                logger.warning(f"⚠️ 載入加密文件失敗: {e}")
        
        # 載入普通 JSON 文件
        if self.keys_file.exists():
            try:
                self._load_json_keys()
                logger.info("✅ 從 JSON 文件載入 API 金鑰")
                return
            except Exception as e:
                logger.warning(f"⚠️ 載入 JSON 文件失敗: {e}")
        
        # 從環境變量載入
        self._load_from_environment()
        logger.info("✅ 從環境變量載入 API 金鑰")
    
    def _load_encrypted_keys(self):
        """載入加密的 API 金鑰文件"""
        with open(self.encrypted_keys_file, 'rb') as f:
            encrypted_data = f.read()
        
        cipher_suite = self._get_cipher_suite()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        
        keys_data = json.loads(decrypted_data.decode())
        
        for key_name, key_data in keys_data.items():
            self.api_keys[key_name] = ApiKeyInfo(
                name=key_name,
                key=key_data['key'],
                description=key_data.get('description', ''),
                is_encrypted=True,
                last_updated=key_data.get('last_updated'),
                is_valid=key_data.get('is_valid', False)
            )
    
    def _load_json_keys(self):
        """載入 JSON API 金鑰文件"""
        with open(self.keys_file, 'r', encoding='utf-8') as f:
            keys_data = json.load(f)
        
        for key_name, key_data in keys_data.items():
            self.api_keys[key_name] = ApiKeyInfo(
                name=key_name,
                key=key_data['key'],
                description=key_data.get('description', ''),
                is_encrypted=False,
                last_updated=key_data.get('last_updated'),
                is_valid=key_data.get('is_valid', False)
            )
    
    def _load_from_environment(self):
        """從環境變量載入 API 金鑰"""
        env_mappings = {
            'proxyscrape_api_key': 'PROXYSCRAPE_API_KEY',
            'github_token': 'GITHUB_TOKEN',
            'github_personal_access_token': 'GITHUB_PERSONAL_ACCESS_TOKEN',  # 支援多種命名
            'shodan_api_key': 'SHODAN_API_KEY',
            'censys_api_id': 'CENSYS_API_ID',
            'censys_api_secret': 'CENSYS_API_SECRET'
        }
        
        for key_name, env_var in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                self.api_keys[key_name] = ApiKeyInfo(
                    name=key_name,
                    key=env_value,
                    description=f"從環境變量 {env_var} 載入",
                    is_encrypted=False,
                    is_valid=True
                )
    
    def add_api_key(self, name: str, key: str, description: str = "", encrypt: bool = True):
        """添加 API 金鑰
        
        Args:
            name: API 金鑰名稱
            key: API 金鑰值
            description: 描述
            encrypt: 是否加密存儲
        """
        self.api_keys[name] = ApiKeyInfo(
            name=name,
            key=key,
            description=description,
            is_encrypted=encrypt,
            is_valid=True
        )
        
        logger.info(f"✅ 添加 API 金鑰: {name}")
        self._save_api_keys(encrypt)
    
    def get_api_key(self, name: str) -> Optional[str]:
        """獲取 API 金鑰
        
        Args:
            name: API 金鑰名稱
            
        Returns:
            API 金鑰值，如果不存在則返回 None
        """
        if name in self.api_keys:
            return self.api_keys[name].key
        return None
    
    def remove_api_key(self, name: str):
        """移除 API 金鑰
        
        Args:
            name: API 金鑰名稱
        """
        if name in self.api_keys:
            del self.api_keys[name]
            logger.info(f"✅ 移除 API 金鑰: {name}")
            self._save_api_keys()
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """列出所有 API 金鑰信息
        
        Returns:
            API 金鑰信息列表
        """
        return [
            {
                'name': key_info.name,
                'description': key_info.description,
                'is_encrypted': key_info.is_encrypted,
                'is_valid': key_info.is_valid,
                'last_updated': key_info.last_updated,
                'key_preview': f"{key_info.key[:8]}..." if len(key_info.key) > 8 else key_info.key
            }
            for key_info in self.api_keys.values()
        ]
    
    def validate_api_key(self, name: str) -> bool:
        """驗證 API 金鑰有效性
        
        Args:
            name: API 金鑰名稱
            
        Returns:
            是否有效
        """
        if name not in self.api_keys:
            return False
        
        key_info = self.api_keys[name]
        
        try:
            # 根據不同的 API 進行驗證
            if name == 'proxyscrape_api_key':
                return self._validate_proxyscrape_key(key_info.key)
            elif name == 'github_token':
                return self._validate_github_token(key_info.key)
            elif name == 'shodan_api_key':
                return self._validate_shodan_key(key_info.key)
            elif name in ['censys_api_id', 'censys_api_secret']:
                return self._validate_censys_keys()
            else:
                # 默認驗證：檢查是否為空
                return bool(key_info.key.strip())
                
        except Exception as e:
            logger.error(f"❌ 驗證 API 金鑰 {name} 失敗: {e}")
            return False
    
    def _validate_proxyscrape_key(self, key: str) -> bool:
        """驗證 ProxyScrape API 金鑰"""
        # ProxyScrape API 金鑰通常是 32 位字符
        return len(key) >= 32 and key.isalnum()
    
    def _validate_github_token(self, token: str) -> bool:
        """驗證 GitHub Token"""
        # GitHub Token 格式檢查
        return len(token) >= 40 and token.isalnum()
    
    def _validate_shodan_key(self, key: str) -> bool:
        """驗證 Shodan API 金鑰"""
        # Shodan API 金鑰格式檢查
        return len(key) >= 32 and key.isalnum()
    
    def _validate_censys_keys(self) -> bool:
        """驗證 Censys API 金鑰"""
        api_id = self.get_api_key('censys_api_id')
        api_secret = self.get_api_key('censys_api_secret')
        return bool(api_id and api_secret)
    
    def _save_api_keys(self, encrypt: bool = True):
        """保存 API 金鑰"""
        if encrypt:
            self._save_encrypted_keys()
        else:
            self._save_json_keys()
    
    def _save_encrypted_keys(self):
        """保存加密的 API 金鑰文件"""
        keys_data = {}
        for name, key_info in self.api_keys.items():
            keys_data[name] = {
                'key': key_info.key,
                'description': key_info.description,
                'last_updated': key_info.last_updated,
                'is_valid': key_info.is_valid
            }
        
        json_data = json.dumps(keys_data, ensure_ascii=False, indent=2)
        encrypted_data = self._get_cipher_suite().encrypt(json_data.encode())
        
        with open(self.encrypted_keys_file, 'wb') as f:
            f.write(encrypted_data)
    
    def _save_json_keys(self):
        """保存 JSON API 金鑰文件"""
        keys_data = {}
        for name, key_info in self.api_keys.items():
            keys_data[name] = {
                'key': key_info.key,
                'description': key_info.description,
                'last_updated': key_info.last_updated,
                'is_valid': key_info.is_valid
            }
        
        with open(self.keys_file, 'w', encoding='utf-8') as f:
            json.dump(keys_data, f, ensure_ascii=False, indent=2)
    
    def export_to_config(self, config_file: str):
        """導出 API 金鑰到配置文件
        
        Args:
            config_file: 配置文件路徑
        """
        config_data = {
            'api': {
                'proxyscrape_api_key': self.get_api_key('proxyscrape_api_key'),
                'github_token': self.get_api_key('github_token'),
                'shodan_api_key': self.get_api_key('shodan_api_key'),
                'censys_api_id': self.get_api_key('censys_api_id'),
                'censys_api_secret': self.get_api_key('censys_api_secret')
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ API 金鑰已導出到: {config_file}")
    
    def get_config_dict(self) -> Dict[str, Any]:
        """獲取配置字典
        
        Returns:
            配置字典
        """
        # 優先使用 github_token，如果沒有則使用 github_personal_access_token
        github_token = self.get_api_key('github_token') or self.get_api_key('github_personal_access_token')
        
        return {
            'proxyscrape_api_key': self.get_api_key('proxyscrape_api_key'),
            'github_token': github_token,
            'shodan_api_key': self.get_api_key('shodan_api_key'),
            'censys_api_id': self.get_api_key('censys_api_id'),
            'censys_api_secret': self.get_api_key('censys_api_secret')
        }


def create_api_config_interactive():
    """交互式創建 API 配置"""
    print("🔑 API 金鑰配置工具")
    print("=" * 50)
    
    manager = ApiConfigManager()
    
    # 檢查現有配置
    existing_keys = manager.list_api_keys()
    if existing_keys:
        print("\n📋 現有 API 金鑰:")
        for key_info in existing_keys:
            status = "✅ 有效" if key_info['is_valid'] else "❌ 無效"
            print(f"  - {key_info['name']}: {key_info['key_preview']} ({status})")
    
    print("\n🔧 配置選項:")
    print("1. 添加/更新 API 金鑰")
    print("2. 從環境變量載入")
    print("3. 驗證所有金鑰")
    print("4. 導出到配置文件")
    print("5. 退出")
    
    while True:
        try:
            choice = input("\n請選擇操作 (1-5): ").strip()
            
            if choice == '1':
                _add_api_key_interactive(manager)
            elif choice == '2':
                manager._load_from_environment()
                print("✅ 已從環境變量載入 API 金鑰")
            elif choice == '3':
                _validate_all_keys(manager)
            elif choice == '4':
                config_file = input("配置文件路徑 (默認: config/api_config.json): ").strip()
                if not config_file:
                    config_file = "config/api_config.json"
                manager.export_to_config(config_file)
            elif choice == '5':
                break
            else:
                print("❌ 無效選擇，請重新輸入")
                
        except KeyboardInterrupt:
            print("\n\n👋 再見！")
            break
        except Exception as e:
            print(f"❌ 操作失敗: {e}")


def _add_api_key_interactive(manager: ApiConfigManager):
    """交互式添加 API 金鑰"""
    print("\n🔑 添加 API 金鑰")
    print("-" * 30)
    
    key_name = input("金鑰名稱 (proxyscrape_api_key, github_token, shodan_api_key, censys_api_id, censys_api_secret): ").strip()
    if not key_name:
        print("❌ 金鑰名稱不能為空")
        return
    
    key_value = input("金鑰值: ").strip()
    if not key_value:
        print("❌ 金鑰值不能為空")
        return
    
    description = input("描述 (可選): ").strip()
    encrypt = input("是否加密存儲? (y/N): ").strip().lower() == 'y'
    
    manager.add_api_key(key_name, key_value, description, encrypt)
    print(f"✅ 已添加 API 金鑰: {key_name}")


def _validate_all_keys(manager: ApiConfigManager):
    """驗證所有金鑰"""
    print("\n🔍 驗證 API 金鑰")
    print("-" * 30)
    
    for name in manager.api_keys:
        is_valid = manager.validate_api_key(name)
        status = "✅ 有效" if is_valid else "❌ 無效"
        print(f"  - {name}: {status}")
        
        # 更新驗證狀態
        if name in manager.api_keys:
            manager.api_keys[name].is_valid = is_valid
    
    manager._save_api_keys()


if __name__ == "__main__":
    create_api_config_interactive()
