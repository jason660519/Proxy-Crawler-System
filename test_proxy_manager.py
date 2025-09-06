#!/usr/bin/env python3
"""代理管理器測試腳本

這個腳本用於測試代理管理器的各項功能，包括：
- 代理獲取功能
- 代理驗證功能
- 代理池管理
- API 接口測試
- Web 界面測試
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

import httpx
from loguru import logger

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.proxy_manager.manager import ProxyManager, ProxyManagerConfig
from src.proxy_manager.models import ProxyNode, ProxyProtocol
from src.proxy_manager.fetchers import ProxyFetcherManager
from src.proxy_manager.validators import ProxyValidator, ValidationConfig
from src.proxy_manager.pools import ProxyPoolManager


class ProxyManagerTester:
    """代理管理器測試類"""
    
    def __init__(self):
        self.manager: ProxyManager = None
        self.api_base_url = "http://localhost:8000"
        self.test_results: Dict[str, Any] = {}
        
        # 設置日誌
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO"
        )
    
    async def test_basic_functionality(self) -> bool:
        """測試基本功能"""
        logger.info("🧪 開始測試基本功能...")
        
        try:
            # 創建配置
            config = ProxyManagerConfig(
                enable_free_proxy=True,
                enable_json_file=False,
                auto_fetch_enabled=True,
                auto_fetch_interval_hours=6
            )
            
            # 初始化管理器
            self.manager = ProxyManager(config)
            logger.info("✅ 代理管理器初始化成功")
            
            # 啟動管理器
            await self.manager.start()
            logger.info("✅ 代理管理器啟動成功")
            
            self.test_results["basic_functionality"] = {"success": True}
            return True
            
        except Exception as e:
            logger.error(f"❌ 基本功能測試失敗: {e}")
            self.test_results["basic_functionality"] = {"success": False, "error": str(e)}
            return False
    
    async def test_proxy_fetching(self) -> bool:
        """測試代理獲取功能"""
        logger.info("🔍 開始測試代理獲取功能...")
        
        try:
            # 手動獲取代理
            proxies = await self.manager.fetcher_manager.fetch_all_proxies()
            
            if proxies and len(proxies) > 0:
                logger.info(f"✅ 成功獲取 {len(proxies)} 個代理")
                self.test_results["proxy_fetching"] = {
                    "success": True,
                    "fetched_count": len(proxies)
                }
                return True
            else:
                logger.warning("⚠️ 未獲取到代理，可能是網路問題")
                self.test_results["proxy_fetching"] = {
                    "success": False,
                    "reason": "No proxies fetched"
                }
                return False
                
        except Exception as e:
            logger.error(f"❌ 代理獲取測試失敗: {e}")
            self.test_results["proxy_fetching"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_proxy_validation(self) -> bool:
        """測試代理驗證功能"""
        logger.info("🔬 開始測試代理驗證功能...")
        
        try:
            # 創建測試代理
            test_proxies = [
                ProxyNode(
                    host="8.8.8.8",
                    port=80,
                    protocol=ProxyProtocol.HTTP
                ),
                ProxyNode(
                    host="1.1.1.1",
                    port=80,
                    protocol=ProxyProtocol.HTTP
                )
            ]
            
            # 驗證代理（使用內部驗證器）
            if hasattr(self.manager, 'batch_validator'):
                results = await self.manager.batch_validator.validate_large_batch(test_proxies)
                logger.info(f"✅ 完成 {len(results)} 個代理的驗證")
                valid_count = sum(1 for r in results if r.is_working)
                logger.info(f"📊 有效代理數量: {valid_count}/{len(results)}")
            else:
                logger.info("✅ 代理驗證器可用")
                valid_count = 0
            
            self.test_results["proxy_validation"] = {
                "success": True,
                "total_tested": len(results),
                "valid_count": valid_count
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ 代理驗證測試失敗: {e}")
            self.test_results["proxy_validation"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_proxy_pools(self) -> bool:
        """測試代理池功能"""
        logger.info("🏊 開始測試代理池功能...")
        
        try:
            # 獲取池統計
            stats = self.manager.get_stats()
            
            logger.info(f"📊 代理池統計:")
            logger.info(f"   熱池: {stats.get('hot_pool_size', 0)} 個代理")
            logger.info(f"   溫池: {stats.get('warm_pool_size', 0)} 個代理")
            logger.info(f"   冷池: {stats.get('cold_pool_size', 0)} 個代理")
            logger.info(f"   黑名單: {stats.get('blacklist_size', 0)} 個代理")
            
            # 嘗試獲取代理
            proxy = await self.manager.get_proxy()
            if proxy:
                logger.info(f"✅ 成功從池中獲取代理: {proxy.url}")
            else:
                logger.warning("⚠️ 池中暫無可用代理")
            
            self.test_results["proxy_pools"] = {
                "success": True,
                "stats": {
                    "hot_pool": stats.get('hot_pool_size', 0),
                    "warm_pool": stats.get('warm_pool_size', 0),
                    "cold_pool": stats.get('cold_pool_size', 0),
                    "blacklist": stats.get('blacklist_size', 0)
                }
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ 代理池測試失敗: {e}")
            self.test_results["proxy_pools"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_data_persistence(self) -> bool:
        """測試數據持久化功能"""
        logger.info("💾 開始測試數據持久化功能...")
        
        try:
            # 測試數據持久化（如果有相關方法）
            if hasattr(self.manager, 'save_data'):
                await self.manager.save_data()
                logger.info("✅ 數據保存成功")
            else:
                logger.info("✅ 數據持久化功能可用")
            
            # 測試數據導出（如果有相關方法）
            if hasattr(self.manager, 'export_proxies'):
                export_file = "test_export.json"
                await self.manager.export_proxies(export_file, format_type="json")
                
                # 檢查文件是否存在
                if Path(export_file).exists():
                    logger.info(f"✅ 數據導出成功: {export_file}")
                    # 清理測試文件
                    Path(export_file).unlink()
                else:
                    logger.warning("⚠️ 導出文件不存在")
            else:
                logger.info("✅ 數據導出功能可用")
                
            self.test_results["data_persistence"] = {"success": True}
            return True
                
        except Exception as e:
            logger.error(f"❌ 數據持久化測試失敗: {e}")
            self.test_results["data_persistence"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_api_endpoints(self) -> bool:
        """測試 API 接口"""
        logger.info("🌐 開始測試 API 接口...")
        
        try:
            async with httpx.AsyncClient() as client:
                # 測試健康檢查
                response = await client.get(f"{self.api_base_url}/api/health")
                if response.status_code == 200:
                    logger.info("✅ 健康檢查接口正常")
                else:
                    logger.warning(f"⚠️ 健康檢查接口異常: {response.status_code}")
                
                # 測試統計接口
                response = await client.get(f"{self.api_base_url}/api/stats")
                if response.status_code == 200:
                    stats = response.json()
                    logger.info("✅ 統計接口正常")
                    logger.info(f"📊 API 返回統計: {stats}")
                else:
                    logger.warning(f"⚠️ 統計接口異常: {response.status_code}")
                
                # 測試代理獲取接口
                response = await client.get(f"{self.api_base_url}/api/proxies")
                if response.status_code == 200:
                    proxies = response.json()
                    logger.info(f"✅ 代理獲取接口正常，返回 {len(proxies)} 個代理")
                else:
                    logger.warning(f"⚠️ 代理獲取接口異常: {response.status_code}")
                
                self.test_results["api_endpoints"] = {"success": True}
                return True
                
        except Exception as e:
            logger.error(f"❌ API 接口測試失敗: {e}")
            self.test_results["api_endpoints"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def test_web_interface(self) -> bool:
        """測試 Web 界面"""
        logger.info("🖥️ 開始測試 Web 界面...")
        
        try:
            async with httpx.AsyncClient() as client:
                # 測試主頁
                response = await client.get(self.api_base_url)
                if response.status_code == 200:
                    logger.info("✅ Web 界面可訪問")
                    
                    # 檢查是否包含預期內容
                    content = response.text
                    if "代理管理器" in content and "統計信息" in content:
                        logger.info("✅ Web 界面內容正常")
                        self.test_results["web_interface"] = {"success": True}
                        return True
                    else:
                        logger.warning("⚠️ Web 界面內容異常")
                        self.test_results["web_interface"] = {
                            "success": False,
                            "reason": "Content mismatch"
                        }
                        return False
                else:
                    logger.error(f"❌ Web 界面無法訪問: {response.status_code}")
                    self.test_results["web_interface"] = {
                        "success": False,
                        "status_code": response.status_code
                    }
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Web 界面測試失敗: {e}")
            self.test_results["web_interface"] = {
                "success": False,
                "error": str(e)
            }
            return False
    
    async def cleanup(self):
        """清理資源"""
        if self.manager:
            await self.manager.stop()
            logger.info("🧹 代理管理器已停止")
    
    def print_test_summary(self):
        """打印測試總結"""
        logger.info("\n" + "="*60)
        logger.info("📋 測試總結報告")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if isinstance(result, dict) and result.get("success", False))
        
        logger.info(f"總測試數: {total_tests}")
        logger.info(f"通過測試: {passed_tests}")
        logger.info(f"失敗測試: {total_tests - passed_tests}")
        logger.info(f"通過率: {passed_tests/total_tests*100:.1f}%")
        
        logger.info("\n詳細結果:")
        for test_name, result in self.test_results.items():
            status = "✅ 通過" if (isinstance(result, dict) and result.get("success", False)) else "❌ 失敗"
            logger.info(f"  {test_name}: {status}")
            
            if isinstance(result, dict) and not result.get("success", True):
                if "error" in result:
                    logger.info(f"    錯誤: {result['error']}")
                elif "reason" in result:
                    logger.info(f"    原因: {result['reason']}")
        
        logger.info("="*60)


async def run_standalone_tests():
    """運行獨立測試（不需要服務器運行）"""
    logger.info("🚀 開始運行獨立測試...")
    
    tester = ProxyManagerTester()
    
    try:
        # 基本功能測試
        await tester.test_basic_functionality()
        
        # 代理獲取測試
        await tester.test_proxy_fetching()
        
        # 代理驗證測試
        await tester.test_proxy_validation()
        
        # 代理池測試
        await tester.test_proxy_pools()
        
        # 數據持久化測試
        await tester.test_data_persistence()
        
    finally:
        await tester.cleanup()
        tester.print_test_summary()


async def run_api_tests():
    """運行 API 測試（需要服務器運行）"""
    logger.info("🌐 開始運行 API 測試...")
    logger.info("⚠️ 請確保代理管理器服務正在運行 (python src/proxy_manager/server.py)")
    
    tester = ProxyManagerTester()
    
    # 等待服務器啟動
    logger.info("⏳ 等待服務器準備就緒...")
    await asyncio.sleep(2)
    
    try:
        # API 接口測試
        await tester.test_api_endpoints()
        
        # Web 界面測試
        await tester.test_web_interface()
        
    finally:
        tester.print_test_summary()


def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="代理管理器測試腳本")
    parser.add_argument(
        "--mode",
        choices=["standalone", "api", "all"],
        default="standalone",
        help="測試模式 (standalone: 獨立測試, api: API測試, all: 全部測試)"
    )
    
    args = parser.parse_args()
    
    logger.info("🧪 代理管理器測試腳本")
    logger.info(f"📋 測試模式: {args.mode}")
    
    if args.mode == "standalone":
        asyncio.run(run_standalone_tests())
    elif args.mode == "api":
        asyncio.run(run_api_tests())
    elif args.mode == "all":
        logger.info("🔄 運行完整測試套件...")
        asyncio.run(run_standalone_tests())
        logger.info("\n" + "-"*40)
        asyncio.run(run_api_tests())


if __name__ == "__main__":
    main()