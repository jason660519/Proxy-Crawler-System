#!/usr/bin/env python3
"""
系統整合測試腳本

測試 JasonSpider 代理管理系統的各個模組協同工作：
- 代理獲取模組
- 代理驗證模組  
- 代理池管理模組
- 高級獲取器模組
- 掃描器模組
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


class SystemIntegrationTester:
    """系統整合測試器"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
    async def run_all_tests(self):
        """運行所有測試"""
        print("🚀 JasonSpider 系統整合測試")
        print("=" * 60)
        
        tests = [
            ("配置載入測試", self.test_config_loading),
            ("API 配置測試", self.test_api_config),
            ("代理管理器初始化", self.test_proxy_manager_init),
            ("代理獲取測試", self.test_proxy_fetching),
            ("代理驗證測試", self.test_proxy_validation),
            ("代理池管理測試", self.test_proxy_pool_management),
            ("統計信息測試", self.test_statistics),
            ("數據持久化測試", self.test_data_persistence)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 執行: {test_name}")
            print("-" * 40)
            
            try:
                start_time = time.time()
                result = await test_func()
                duration = time.time() - start_time
                
                if result.get('success', False):
                    print(f"✅ {test_name} - 通過 ({duration:.2f}s)")
                    self.test_results[test_name] = {
                        'status': 'PASS',
                        'duration': duration,
                        'details': result.get('details', {})
                    }
                else:
                    print(f"❌ {test_name} - 失敗 ({duration:.2f}s)")
                    print(f"   錯誤: {result.get('error', '未知錯誤')}")
                    self.test_results[test_name] = {
                        'status': 'FAIL',
                        'duration': duration,
                        'error': result.get('error', '未知錯誤')
                    }
                    
            except Exception as e:
                duration = time.time() - start_time
                print(f"💥 {test_name} - 異常 ({duration:.2f}s)")
                print(f"   異常: {str(e)}")
                self.test_results[test_name] = {
                    'status': 'ERROR',
                    'duration': duration,
                    'error': str(e)
                }
        
        # 生成測試報告
        self.generate_test_report()
    
    async def test_config_loading(self) -> Dict[str, Any]:
        """測試配置載入"""
        try:
            # 測試基本配置載入
            config = ProxyManagerConfig()
            
            # 檢查基本配置屬性
            assert hasattr(config, 'data_dir'), "缺少 data_dir 配置"
            assert hasattr(config, 'api'), "缺少 api 配置"
            assert hasattr(config, 'scanner'), "缺少 scanner 配置"
            assert hasattr(config, 'validation'), "缺少 validation 配置"
            
            return {
                'success': True,
                'details': {
                    'data_dir': str(config.data_dir),
                    'api_config_loaded': True,
                    'scanner_config_loaded': True,
                    'validation_config_loaded': True
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_api_config(self) -> Dict[str, Any]:
        """測試 API 配置"""
        try:
            # 測試 API 配置管理器
            api_manager = ApiConfigManager()
            
            # 檢查是否載入了 GitHub Token
            github_token = api_manager.get_api_key('github_personal_access_token')
            has_github_token = bool(github_token)
            
            # 獲取配置字典
            config_dict = api_manager.get_config_dict()
            
            return {
                'success': True,
                'details': {
                    'github_token_loaded': has_github_token,
                    'config_keys': list(config_dict.keys()),
                    'total_api_keys': len(api_manager.api_keys)
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_proxy_manager_init(self) -> Dict[str, Any]:
        """測試代理管理器初始化"""
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False  # 禁用自動獲取
            config.auto_cleanup_enabled = False  # 禁用自動清理
            config.auto_save_enabled = False  # 禁用自動保存
            
            # 初始化代理管理器
            manager = ProxyManager(config)
            
            # 檢查組件初始化
            assert hasattr(manager, 'fetcher_manager'), "缺少 fetcher_manager"
            assert hasattr(manager, 'advanced_fetcher_manager'), "缺少 advanced_fetcher_manager"
            assert hasattr(manager, 'scanner'), "缺少 scanner"
            assert hasattr(manager, 'pool_manager'), "缺少 pool_manager"
            
            # 啟動管理器
            await manager.start()
            
            # 檢查啟動狀態
            assert manager._running, "管理器未正確啟動"
            
            # 停止管理器
            await manager.stop()
            
            return {
                'success': True,
                'details': {
                    'components_initialized': True,
                    'manager_started': True,
                    'manager_stopped': True
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_proxy_fetching(self) -> Dict[str, Any]:
        """測試代理獲取"""
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False
            config.auto_cleanup_enabled = False
            config.auto_save_enabled = False
            
            # 初始化管理器
            manager = ProxyManager(config)
            await manager.start()
            
            # 測試代理獲取
            print("   正在獲取代理...")
            proxies = await manager.fetch_proxies()
            
            # 檢查結果
            proxy_count = len(proxies)
            has_proxies = proxy_count > 0
            
            await manager.stop()
            
            return {
                'success': True,
                'details': {
                    'proxies_fetched': proxy_count,
                    'has_proxies': has_proxies,
                    'fetch_successful': True
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_proxy_validation(self) -> Dict[str, Any]:
        """測試代理驗證"""
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False
            config.auto_cleanup_enabled = False
            config.auto_save_enabled = False
            
            # 初始化管理器
            manager = ProxyManager(config)
            await manager.start()
            
            # 獲取一些代理進行驗證測試
            proxies = await manager.fetch_proxies()
            
            if proxies:
                # 測試驗證功能
                print(f"   正在驗證 {len(proxies)} 個代理...")
                await manager.validate_pools()
                
                # 獲取驗證後的統計
                stats = manager.get_stats()
                pool_summary = stats.get('pool_summary', {})
                
                await manager.stop()
                
                return {
                    'success': True,
                    'details': {
                        'proxies_validated': len(proxies),
                        'validation_completed': True,
                        'pool_summary': pool_summary
                    }
                }
            else:
                await manager.stop()
                return {
                    'success': True,
                    'details': {
                        'proxies_validated': 0,
                        'validation_completed': True,
                        'note': '沒有代理需要驗證'
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_proxy_pool_management(self) -> Dict[str, Any]:
        """測試代理池管理"""
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False
            config.auto_cleanup_enabled = False
            config.auto_save_enabled = False
            
            # 初始化管理器
            manager = ProxyManager(config)
            await manager.start()
            
            # 獲取代理
            proxies = await manager.fetch_proxies()
            
            if proxies:
                # 測試代理池操作
                print(f"   測試代理池管理...")
                
                # 獲取單個代理
                proxy = await manager.get_proxy()
                single_proxy_available = proxy is not None
                
                # 獲取多個代理
                multiple_proxies = await manager.get_proxies(count=5)
                multiple_proxies_available = len(multiple_proxies) > 0
                
                # 獲取統計信息
                stats = manager.get_stats()
                pool_stats = stats.get('pool_details', {})
                
                await manager.stop()
                
                return {
                    'success': True,
                    'details': {
                        'single_proxy_available': single_proxy_available,
                        'multiple_proxies_available': multiple_proxies_available,
                        'pool_stats_available': bool(pool_stats),
                        'total_pools': len(pool_stats)
                    }
                }
            else:
                await manager.stop()
                return {
                    'success': True,
                    'details': {
                        'single_proxy_available': False,
                        'multiple_proxies_available': False,
                        'note': '沒有代理可供測試'
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_statistics(self) -> Dict[str, Any]:
        """測試統計信息"""
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False
            config.auto_cleanup_enabled = False
            config.auto_save_enabled = False
            
            # 初始化管理器
            manager = ProxyManager(config)
            await manager.start()
            
            # 獲取統計信息
            stats = manager.get_stats()
            
            # 檢查統計信息結構
            required_keys = ['manager_stats', 'pool_summary', 'fetcher_stats', 'config', 'status']
            stats_keys = list(stats.keys())
            missing_keys = [key for key in required_keys if key not in stats_keys]
            
            await manager.stop()
            
            return {
                'success': len(missing_keys) == 0,
                'details': {
                    'stats_available': True,
                    'required_keys_present': len(missing_keys) == 0,
                    'missing_keys': missing_keys,
                    'total_stats_keys': len(stats_keys)
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def test_data_persistence(self) -> Dict[str, Any]:
        """測試數據持久化"""
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False
            config.auto_cleanup_enabled = False
            config.auto_save_enabled = False
            
            # 初始化管理器
            manager = ProxyManager(config)
            await manager.start()
            
            # 獲取代理
            proxies = await manager.fetch_proxies()
            
            if proxies:
                # 測試導出功能
                print("   測試數據導出...")
                export_file = Path("test_export.json")
                
                try:
                    exported_count = await manager.export_proxies(export_file, "json")
                    
                    # 檢查導出文件
                    file_exists = export_file.exists()
                    file_size = export_file.stat().st_size if file_exists else 0
                    
                    # 清理測試文件
                    if export_file.exists():
                        export_file.unlink()
                    
                    await manager.stop()
                    
                    return {
                        'success': file_exists and file_size > 0,
                        'details': {
                            'export_successful': file_exists,
                            'exported_count': exported_count,
                            'file_size': file_size
                        }
                    }
                except Exception as export_error:
                    await manager.stop()
                    return {
                        'success': False,
                        'error': f"導出失敗: {str(export_error)}"
                    }
            else:
                await manager.stop()
                return {
                    'success': True,
                    'details': {
                        'export_skipped': True,
                        'note': '沒有代理可供導出'
                    }
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_test_report(self):
        """生成測試報告"""
        total_time = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 測試報告")
        print("=" * 60)
        
        # 統計結果
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results.values() if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results.values() if r['status'] == 'FAIL'])
        error_tests = len([r for r in self.test_results.values() if r['status'] == 'ERROR'])
        
        print(f"總測試數: {total_tests}")
        print(f"通過: {passed_tests} ✅")
        print(f"失敗: {failed_tests} ❌")
        print(f"錯誤: {error_tests} 💥")
        print(f"總耗時: {total_time:.2f} 秒")
        print(f"成功率: {(passed_tests/total_tests)*100:.1f}%")
        
        # 詳細結果
        print("\n📋 詳細結果:")
        print("-" * 40)
        
        for test_name, result in self.test_results.items():
            status_icon = {
                'PASS': '✅',
                'FAIL': '❌', 
                'ERROR': '💥'
            }.get(result['status'], '❓')
            
            print(f"{status_icon} {test_name} ({result['duration']:.2f}s)")
            
            if result['status'] == 'FAIL' and 'error' in result:
                print(f"   錯誤: {result['error']}")
            elif result['status'] == 'ERROR' and 'error' in result:
                print(f"   異常: {result['error']}")
            elif result['status'] == 'PASS' and 'details' in result:
                details = result['details']
                for key, value in details.items():
                    print(f"   {key}: {value}")
        
        # 總結
        print("\n" + "=" * 60)
        if failed_tests == 0 and error_tests == 0:
            print("🎉 所有測試通過！系統整合正常。")
        elif failed_tests > 0 or error_tests > 0:
            print("⚠️ 部分測試失敗，請檢查相關模組。")
        print("=" * 60)


async def main():
    """主函數"""
    tester = SystemIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        sys.exit(1)

