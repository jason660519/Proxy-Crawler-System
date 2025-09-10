#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP 伺服器測試腳本
用於驗證已安裝的 MCP 伺服器是否正常運作
"""

import subprocess
import sys
import json
import os
from typing import Dict, List, Tuple

def test_mcp_server(name: str, command: str, args: List[str], env: Dict[str, str] = None) -> Tuple[bool, str]:
    """
    測試 MCP 伺服器
    
    Args:
        name: 伺服器名稱
        command: 命令
        args: 參數列表
        env: 環境變數
        
    Returns:
        Tuple[bool, str]: (是否成功, 錯誤訊息)
    """
    try:
        # 準備環境變數
        full_env = dict(env) if env else {}
        
        # 執行命令
        result = subprocess.run(
            [command] + args,
            capture_output=True,
            text=True,
            timeout=10,
            env=full_env
        )
        
        if result.returncode == 0:
            return True, "成功"
        else:
            return False, f"錯誤碼: {result.returncode}, 錯誤: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return False, "超時"
    except FileNotFoundError:
        return False, f"命令未找到: {command}"
    except Exception as e:
        return False, f"未知錯誤: {str(e)}"

def main():
    """主函數"""
    print("🔍 開始測試 MCP 伺服器...\n")
    
    # 測試配置
    test_configs = [
        {
            "name": "Playwright MCP",
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--help"],
            "env": None
        },
        {
            "name": "Context7 MCP",
            "command": "npx",
            "args": ["@upstash/context7-mcp@latest", "--help"],
            "env": None
        },
        {
            "name": "Sequential Thinking MCP",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-sequential-thinking", "--help"],
            "env": None
        },
        {
            "name": "Figma MCP",
            "command": "npx",
            "args": ["figma-developer-mcp", "--help"],
            "env": None
        },
        {
            "name": "Brave Search MCP",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-brave-search", "--help"],
            # 使用環境變數，避免硬編碼金鑰
            "env": {"BRAVE_API_KEY": os.getenv("BRAVE_API_KEY", "DUMMY_KEY_PLACEHOLDER")}
        },
        {
            "name": "PostgreSQL MCP",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-postgres", "postgresql://postgres:password@localhost:5432/proxy_manager"],
            "env": None
        },
        {
            "name": "Redis MCP",
            "command": "npx",
            "args": ["@modelcontextprotocol/server-redis", "redis://localhost:6379"],
            "env": None
        },
        {
            "name": "Fetch MCP",
            "command": "uvx",
            "args": ["mcp-server-fetch", "--help"],
            "env": None
        }
    ]
    
    success_count = 0
    total_count = len(test_configs)
    
    for config in test_configs:
        print(f"📡 測試 {config['name']}...")
        success, message = test_mcp_server(
            config["name"],
            config["command"],
            config["args"],
            config["env"]
        )
        
        if success:
            print(f"   ✅ {message}")
            success_count += 1
        else:
            print(f"   ❌ {message}")
        print()
    
    print(f"📊 測試結果: {success_count}/{total_count} 個 MCP 伺服器可用")
    
    if success_count > 0:
        print("\n✅ 部分 MCP 伺服器已成功安裝並可用！")
        print("   建議重新啟動 Cursor 以載入新的 MCP 配置。")
        return 0
    else:
        print("\n❌ 所有 MCP 伺服器測試都失敗，請檢查安裝狀態。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
