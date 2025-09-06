#!/usr/bin/env python3
"""
API 配置設置腳本

提供簡單的命令行界面來設置 API 金鑰配置
"""

import sys
import os
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.proxy_manager.api_config_manager import ApiConfigManager, create_api_config_interactive


def main():
    """主函數"""
    print("🚀 JasonSpider API 配置設置工具")
    print("=" * 50)
    
    # 檢查是否在正確的目錄
    if not (project_root / "src" / "proxy_manager").exists():
        print("❌ 錯誤: 請在項目根目錄運行此腳本")
        sys.exit(1)
    
    # 創建配置目錄
    config_dir = project_root / "config"
    config_dir.mkdir(exist_ok=True)
    
    print(f"📁 配置目錄: {config_dir}")
    print()
    
    # 顯示選項
    print("🔧 配置選項:")
    print("1. 交互式配置 API 金鑰")
    print("2. 從環境變量載入配置")
    print("3. 創建配置文件模板")
    print("4. 驗證現有配置")
    print("5. 退出")
    
    while True:
        try:
            choice = input("\n請選擇操作 (1-5): ").strip()
            
            if choice == '1':
                # 交互式配置
                manager = ApiConfigManager(config_dir)
                create_api_config_interactive()
                break
                
            elif choice == '2':
                # 從環境變量載入
                _load_from_environment(config_dir)
                break
                
            elif choice == '3':
                # 創建配置文件模板
                _create_config_template(config_dir)
                break
                
            elif choice == '4':
                # 驗證現有配置
                _validate_existing_config(config_dir)
                break
                
            elif choice == '5':
                print("👋 再見！")
                break
                
            else:
                print("❌ 無效選擇，請重新輸入")
                
        except KeyboardInterrupt:
            print("\n\n👋 再見！")
            break
        except Exception as e:
            print(f"❌ 操作失敗: {e}")


def _load_from_environment(config_dir: Path):
    """從環境變量載入配置"""
    print("\n🌍 從環境變量載入配置")
    print("-" * 30)
    
    manager = ApiConfigManager(config_dir)
    manager._load_from_environment()
    
    # 顯示載入的配置
    keys = manager.list_api_keys()
    if keys:
        print("✅ 載入的 API 金鑰:")
        for key_info in keys:
            print(f"  - {key_info['name']}: {key_info['key_preview']}")
    else:
        print("⚠️ 沒有找到環境變量中的 API 金鑰")
        print("請設置以下環境變量:")
        print("  - PROXYSCRAPE_API_KEY")
        print("  - GITHUB_TOKEN")
        print("  - SHODAN_API_KEY")
        print("  - CENSYS_API_ID")
        print("  - CENSYS_API_SECRET")
    
    # 導出到配置文件
    config_file = config_dir / "api_config.yaml"
    manager.export_to_config(str(config_file))
    print(f"✅ 配置已導出到: {config_file}")


def _create_config_template(config_dir: Path):
    """創建配置文件模板"""
    print("\n📝 創建配置文件模板")
    print("-" * 30)
    
    # 創建 YAML 模板
    yaml_template = config_dir / "api_config.yaml"
    if not yaml_template.exists():
        template_content = """# API 配置
api:
  proxyscrape_api_key: ""
  github_token: ""
  shodan_api_key: ""
  censys_api_id: ""
  censys_api_secret: ""

# 掃描器配置
scanner:
  timeout: 5
  max_concurrent: 100
  enable_fast_scan: true

# 驗證配置
validation:
  timeout: 10
  max_retries: 3
  test_urls:
    - "http://httpbin.org/ip"
    - "https://httpbin.org/ip"

# 自動任務配置
auto_fetch_enabled: false
auto_cleanup_enabled: false
auto_save_enabled: true
auto_fetch_interval_hours: 6
auto_cleanup_interval_hours: 12
auto_save_interval_minutes: 5
"""
        with open(yaml_template, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✅ 已創建 YAML 模板: {yaml_template}")
    else:
        print(f"⚠️ 配置文件已存在: {yaml_template}")
    
    # 創建 JSON 模板
    json_template = config_dir / "api_config.json"
    if not json_template.exists():
        template_content = """{
  "api": {
    "proxyscrape_api_key": "",
    "github_token": "",
    "shodan_api_key": "",
    "censys_api_id": "",
    "censys_api_secret": ""
  },
  "scanner": {
    "timeout": 5,
    "max_concurrent": 100,
    "enable_fast_scan": true
  },
  "validation": {
    "timeout": 10,
    "max_retries": 3,
    "test_urls": [
      "http://httpbin.org/ip",
      "https://httpbin.org/ip"
    ]
  },
  "auto_fetch_enabled": false,
  "auto_cleanup_enabled": false,
  "auto_save_enabled": true,
  "auto_fetch_interval_hours": 6,
  "auto_cleanup_interval_hours": 12,
  "auto_save_interval_minutes": 5
}"""
        with open(json_template, 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f"✅ 已創建 JSON 模板: {json_template}")
    else:
        print(f"⚠️ 配置文件已存在: {json_template}")
    
    print("\n📋 下一步:")
    print("1. 編輯配置文件，填入您的 API 金鑰")
    print("2. 運行 'python setup_api_config.py' 選擇選項 4 驗證配置")


def _validate_existing_config(config_dir: Path):
    """驗證現有配置"""
    print("\n🔍 驗證現有配置")
    print("-" * 30)
    
    manager = ApiConfigManager(config_dir)
    
    # 檢查配置文件
    config_files = [
        config_dir / "api_config.yaml",
        config_dir / "api_config.json",
        config_dir / "api_keys.json",
        config_dir / "api_keys.enc"
    ]
    
    existing_files = [f for f in config_files if f.exists()]
    if existing_files:
        print("📁 找到配置文件:")
        for config_file in existing_files:
            print(f"  - {config_file}")
    else:
        print("⚠️ 沒有找到配置文件")
        return
    
    # 驗證 API 金鑰
    keys = manager.list_api_keys()
    if keys:
        print("\n🔑 API 金鑰狀態:")
        for key_info in keys:
            is_valid = manager.validate_api_key(key_info['name'])
            status = "✅ 有效" if is_valid else "❌ 無效"
            print(f"  - {key_info['name']}: {status}")
    else:
        print("⚠️ 沒有找到 API 金鑰")
    
    # 導出配置到 ProxyManager 格式
    config_dict = manager.get_config_dict()
    if any(config_dict.values()):
        print("\n📤 導出配置到 ProxyManager 格式...")
        from src.proxy_manager.config import ProxyManagerConfig
        
        # 創建 ProxyManager 配置
        pm_config = ProxyManagerConfig()
        pm_config.api.proxyscrape_api_key = config_dict.get('proxyscrape_api_key')
        pm_config.api.github_token = config_dict.get('github_token')
        pm_config.api.shodan_api_key = config_dict.get('shodan_api_key')
        
        # 保存配置
        config_file = config_dir / "proxy_manager_config.yaml"
        pm_config.save_to_file(str(config_file))
        print(f"✅ 已導出 ProxyManager 配置: {config_file}")
    else:
        print("⚠️ 沒有有效的 API 金鑰可以導出")


if __name__ == "__main__":
    main()
