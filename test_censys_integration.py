#!/usr/bin/env python3
"""
Censys API 整合測試腳本

測試 Censys API 代理發現功能
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.proxy_manager.advanced_fetchers import CensysProxyFetcher
from src.proxy_manager.api_config_manager import ApiConfigManager

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_censys_integration():
    """測試 Censys API 整合"""
    print("🔍 Censys API 整合測試")
    print("=" * 50)
    
    # 1. 檢查 API 憑證
    print("\n1️⃣ 檢查 Censys API 憑證...")
    api_manager = ApiConfigManager()
    
    censys_api_id = api_manager.get_api_key('censys_api_id')
    censys_api_secret = api_manager.get_api_key('censys_api_secret')
    
    if not censys_api_id or not censys_api_secret:
        print("❌ Censys API 憑證未配置")
        print("請設置以下環境變量:")
        print("  - CENSYS_API_ID")
        print("  - CENSYS_API_SECRET")
        print("\n或者運行配置工具:")
        print("  python setup_api_config.py")
        return False
    
    print(f"✅ Censys API ID: {censys_api_id[:8]}...")
    print(f"✅ Censys API Secret: {'已配置' if censys_api_secret else '未配置'}")
    
    # 2. 測試 Censys 獲取器
    print("\n2️⃣ 測試 Censys 代理獲取器...")
    try:
        fetcher = CensysProxyFetcher(censys_api_id, censys_api_secret)
        print("✅ Censys 獲取器創建成功")
        
        # 3. 測試代理獲取（限制數量以節省 API 額度）
        print("\n3️⃣ 測試代理獲取（限制 5 個）...")
        print("⚠️ 注意: 這會消耗 Censys API 額度")
        
        proxies = await fetcher.fetch_proxies(limit=5)
        
        print(f"✅ 獲取完成: {len(proxies)} 個代理")
        
        if proxies:
            print("\n📊 發現的代理:")
            for i, proxy in enumerate(proxies, 1):
                print(f"  {i}. {proxy.host}:{proxy.port} ({proxy.protocol.value})")
                print(f"     國家: {proxy.country or '未知'}")
                print(f"     來源: {proxy.source}")
                print(f"     標籤: {', '.join(proxy.tags)}")
                print()
        else:
            print("⚠️ 沒有發現代理")
            print("這可能是因為:")
            print("1. 搜尋查詢沒有匹配到結果")
            print("2. API 額度已用完")
            print("3. 網路連接問題")
        
        # 4. 測試統計信息
        print("\n4️⃣ 測試統計信息...")
        stats = fetcher.get_stats()
        print(f"✅ 統計信息: {stats}")
        
        # 5. 清理資源
        print("\n5️⃣ 清理資源...")
        await fetcher.close()
        print("✅ 資源清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_censys_without_credentials():
    """測試沒有憑證時的行為"""
    print("\n🔍 測試沒有憑證時的行為...")
    
    try:
        # 嘗試創建沒有憑證的獲取器
        fetcher = CensysProxyFetcher("", "")
        print("⚠️ 創建了沒有憑證的獲取器")
        
        # 嘗試獲取代理（應該失敗）
        proxies = await fetcher.fetch_proxies(limit=1)
        print(f"獲取結果: {len(proxies)} 個代理")
        
        await fetcher.close()
        
    except Exception as e:
        print(f"✅ 預期錯誤: {e}")


async def main():
    """主函數"""
    print("🚀 Censys API 整合測試")
    print("=" * 60)
    
    # 測試有憑證的情況
    success = await test_censys_integration()
    
    # 測試沒有憑證的情況
    await test_censys_without_credentials()
    
    if success:
        print("\n🎉 Censys API 整合測試完成！")
        print("\n📋 下一步:")
        print("1. 如果測試成功，Censys API 已整合到系統中")
        print("2. 可以在 ProxyManager 中使用 Censys 發現的代理")
        print("3. 注意 API 額度限制（免費版本每月 250 次搜尋）")
    else:
        print("\n❌ Censys API 整合測試失敗！")
        print("請檢查 API 憑證配置")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        sys.exit(1)
