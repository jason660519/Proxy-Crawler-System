#!/usr/bin/env python3
"""
核心功能測試腳本

測試 JasonSpider 代理管理系統的核心功能：
- 配置載入
- 代理獲取
- 基本驗證
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
import logging

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.proxy_manager.manager import ProxyManager
from src.proxy_manager.config import ProxyManagerConfig
from src.proxy_manager.api_config_manager import ApiConfigManager

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_core_functionality():
    """測試核心功能"""
    print("🚀 JasonSpider 核心功能測試")
    print("=" * 50)
    
    try:
        # 1. 測試配置載入
        print("\n1️⃣ 測試配置載入...")
        config = ProxyManagerConfig()
        print(f"   ✅ 配置載入成功")
        print(f"   📁 數據目錄: {config.data_dir}")
        print(f"   🔧 API 配置: {bool(config.api)}")
        
        # 2. 測試 API 配置
        print("\n2️⃣ 測試 API 配置...")
        api_manager = ApiConfigManager()
        github_token = api_manager.get_api_key('github_personal_access_token')
        print(f"   ✅ GitHub Token: {'已配置' if github_token else '未配置'}")
        
        # 3. 測試代理管理器初始化
        print("\n3️⃣ 測試代理管理器初始化...")
        manager = ProxyManager(config)
        print(f"   ✅ 代理管理器創建成功")
        
        # 4. 測試代理獲取
        print("\n4️⃣ 測試代理獲取...")
        print("   🔄 正在獲取代理...")
        start_time = time.time()
        
        proxies = await manager.fetch_proxies()
        fetch_time = time.time() - start_time
        
        print(f"   ✅ 獲取完成: {len(proxies)} 個代理 ({fetch_time:.2f}s)")
        
        if proxies:
            print(f"   📊 代理樣本:")
            for i, proxy in enumerate(proxies[:3]):  # 顯示前3個
                print(f"      {i+1}. {proxy.host}:{proxy.port} ({proxy.protocol.value})")
        
        # 5. 測試統計信息
        print("\n5️⃣ 測試統計信息...")
        stats = manager.get_stats()
        print(f"   ✅ 統計信息獲取成功")
        print(f"   📈 池摘要: {stats.get('pool_summary', {})}")
        
        # 6. 測試代理池管理
        print("\n6️⃣ 測試代理池管理...")
        if proxies:
            single_proxy = await manager.get_proxy()
            print(f"   ✅ 單個代理獲取: {'成功' if single_proxy else '失敗'}")
            
            multiple_proxies = await manager.get_proxies(count=3)
            print(f"   ✅ 多個代理獲取: {len(multiple_proxies)} 個")
        
        print("\n🎉 核心功能測試完成！")
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理資源
        try:
            if 'manager' in locals():
                await manager.stop()
        except:
            pass


async def main():
    """主函數"""
    success = await test_core_functionality()
    
    if success:
        print("\n✅ 所有核心功能測試通過！")
        sys.exit(0)
    else:
        print("\n❌ 核心功能測試失敗！")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        sys.exit(1)

