#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 連接測試腳本
用於測試與 Docker Redis 容器的連接狀態
"""

import redis
import sys
from typing import Optional

def test_redis_connection(host: str = 'localhost', port: int = 6379, db: int = 0) -> bool:
    """
    測試 Redis 連接
    
    Args:
        host: Redis 主機地址
        port: Redis 端口
        db: Redis 資料庫編號
        
    Returns:
        bool: 連接成功返回 True，失敗返回 False
    """
    try:
        # 創建 Redis 連接
        r = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        
        # 測試連接
        response = r.ping()
        if response:
            print(f"✅ Redis 連接成功！")
            print(f"   主機: {host}:{port}")
            print(f"   資料庫: {db}")
            
            # 獲取 Redis 資訊
            info = r.info('server')
            print(f"   Redis 版本: {info.get('redis_version', 'Unknown')}")
            print(f"   運行時間: {info.get('uptime_in_seconds', 0)} 秒")
            
            # 測試基本操作
            test_key = 'test_connection_key'
            test_value = 'test_connection_value'
            
            r.set(test_key, test_value, ex=10)  # 設置 10 秒過期
            retrieved_value = r.get(test_key)
            
            if retrieved_value == test_value:
                print(f"✅ Redis 讀寫測試成功！")
                r.delete(test_key)  # 清理測試數據
                return True
            else:
                print(f"❌ Redis 讀寫測試失敗！")
                return False
                
        else:
            print(f"❌ Redis ping 失敗！")
            return False
            
    except redis.ConnectionError as e:
        print(f"❌ Redis 連接錯誤: {e}")
        return False
    except redis.TimeoutError as e:
        print(f"❌ Redis 超時錯誤: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知錯誤: {e}")
        return False

def main():
    """
    主函數：測試多個 Redis 連接配置
    """
    print("🔍 開始測試 Redis 連接...\n")
    
    # 測試配置列表
    test_configs = [
        {'host': 'localhost', 'port': 6379, 'db': 0, 'name': 'Docker Redis (localhost:6379)'},
        {'host': '127.0.0.1', 'port': 6379, 'db': 0, 'name': 'Docker Redis (127.0.0.1:6379)'},
    ]
    
    success_count = 0
    
    for config in test_configs:
        print(f"📡 測試 {config['name']}...")
        if test_redis_connection(config['host'], config['port'], config['db']):
            success_count += 1
        print()
    
    print(f"📊 測試結果: {success_count}/{len(test_configs)} 個連接成功")
    
    if success_count > 0:
        print("\n✅ Redis 連接正常，MCP Redis 服務器應該可以正常工作！")
        print("   建議檢查 MCP 配置文件中的連接 URL 格式。")
        return 0
    else:
        print("\n❌ 所有 Redis 連接都失敗，請檢查 Docker 容器狀態。")
        return 1

if __name__ == '__main__':
    sys.exit(main())