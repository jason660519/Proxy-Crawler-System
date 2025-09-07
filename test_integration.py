#!/usr/bin/env python3
"""
整合測試腳本

測試 JasonSpider-Dev 中完成的功能是否成功整合到主系統中：
- 增強代理掃描器
- 更新的數據模型
- 代理管理器整合
"""

import asyncio
import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.proxy_manager.manager import ProxyManager, EnhancedProxyManager
from src.proxy_manager.enhanced_scanner import EnhancedProxyScanner
from src.proxy_manager.models import ScanTarget, ScanProtocol, ScanStatus
from src.proxy_manager.config import ProxyManagerConfig

async def test_enhanced_scanner():
    """測試增強掃描器"""
    print("🔍 測試增強代理掃描器...")
    
    try:
        scanner = EnhancedProxyScanner()
        
        # 測試掃描本地回環地址
        target = ScanTarget(host="127.0.0.1", port=8080, protocols=[ScanProtocol.HTTP])
        result = await scanner._scan_single_target(target)
        results = [result]
        
        print(f"   ✅ 掃描器初始化成功")
        print(f"   📊 掃描結果: {len(results)} 個")
        
        for result in results:
            print(f"   🎯 {result.target.host}:{result.target.port} - {result.result.value}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 掃描器測試失敗: {e}")
        return False

async def test_proxy_manager_integration():
    """測試代理管理器整合"""
    print("🔧 測試代理管理器整合...")
    
    try:
        config = ProxyManagerConfig()
        manager = EnhancedProxyManager(config)
        
        # 測試初始化
        print(f"   ✅ 代理管理器初始化成功")
        print(f"   📊 增強掃描器: {hasattr(manager, 'enhanced_scanner')}")
        
        # 測試掃描功能
        results = await manager.scan_single_target("127.0.0.1", 8080, ["http"])
        print(f"   🎯 單目標掃描: {len(results)} 個結果")
        
        # 測試統計功能
        stats = await manager.get_scan_statistics()
        print(f"   📈 掃描統計: {len(stats)} 個指標")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 代理管理器測試失敗: {e}")
        return False

async def test_models_integration():
    """測試數據模型整合"""
    print("📋 測試數據模型整合...")
    
    try:
        from src.proxy_manager.models import ScanTarget, ScanResult, ScanConfig, ScanProtocol, ScanStatus
        
        # 測試掃描目標
        target = ScanTarget(host="192.168.1.1", port=8080, protocols=[ScanProtocol.HTTP])
        print(f"   ✅ ScanTarget 創建成功: {target.host}:{target.port}")
        
        # 測試掃描結果
        result = ScanResult(
            target=target,
            protocol=ScanProtocol.HTTP,
            result=ScanStatus.SUCCESS,
            response_time=100.0
        )
        print(f"   ✅ ScanResult 創建成功: {result.result.value}")
        
        # 測試掃描配置
        config = ScanConfig(max_concurrent_scans=50)
        print(f"   ✅ ScanConfig 創建成功: {config.max_concurrent_scans} 並發")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 數據模型測試失敗: {e}")
        return False

async def main():
    """主測試函數"""
    print("🚀 JasonSpider 整合測試開始")
    print("=" * 50)
    
    tests = [
        ("數據模型整合", test_models_integration),
        ("增強掃描器", test_enhanced_scanner),
        ("代理管理器整合", test_proxy_manager_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📝 執行測試: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ 測試異常: {e}")
            results.append((test_name, False))
    
    # 輸出測試結果
    print("\n" + "=" * 50)
    print("📊 測試結果總結")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 總體結果: {passed}/{total} 個測試通過")
    
    if passed == total:
        print("🎉 所有測試通過！整合成功！")
        return True
    else:
        print("⚠️ 部分測試失敗，需要檢查整合問題")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
