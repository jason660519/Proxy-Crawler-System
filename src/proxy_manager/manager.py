"""代理管理器核心模組

整合所有功能模組，提供統一的代理管理接口：
- 代理獲取與驗證
- 池管理與自動平衡
- 統計與監控
- 持久化存儲
"""

import asyncio
import json
import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
import aiofiles

from .models import ProxyNode, ProxyStatus, ProxyAnonymity, ProxyProtocol, ProxyFilter, ScanTarget, ScanResult, ScanConfig
from .fetchers import ProxyFetcherManager, JsonFileFetcher
from .advanced_fetchers import AdvancedProxyFetcherManager
from .scanner import ProxyScanner
from .enhanced_scanner import EnhancedProxyScanner
from .validators import ProxyValidator, BatchValidator
from .pools import ProxyPoolManager, PoolConfig, PoolType
from .config import ProxyManagerConfig as ConfigClass

logger = logging.getLogger(__name__)


# 使用新的配置類
ProxyManagerConfig = ConfigClass


class ProxyManager:
    """代理管理器主類"""
    
    def __init__(self, config: Optional[ProxyManagerConfig] = None):
        self.config = config or ProxyManagerConfig()
        
        # 核心組件
        self.fetcher_manager = ProxyFetcherManager()
        # 為 AdvancedProxyFetcherManager 準備字典格式的配置
        advanced_config = {
            "proxyscrape_api_key": getattr(self.config.api, 'proxyscrape_api_key', None),
            "github_token": getattr(self.config.api, 'github_token', None),
            "shodan_api_key": getattr(self.config.api, 'shodan_api_key', None)
        }
        self.advanced_fetcher_manager = AdvancedProxyFetcherManager(advanced_config)
        self.scanner = ProxyScanner(self.config.scanner)
        self.enhanced_scanner = EnhancedProxyScanner()
        self.pool_manager = ProxyPoolManager()
        self.validator: Optional[ProxyValidator] = None
        self.batch_validator: Optional[BatchValidator] = None
        
        # 狀態
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # 統計
        self.stats = {
            'total_fetched': 0,
            'total_validated': 0,
            'total_active': 0,
            'last_fetch_time': None,
            'last_validation_time': None,
            'start_time': None
        }
    
    async def start(self):
        """啟動代理管理器"""
        if self._running:
            logger.warning("⚠️ 代理管理器已經在運行中")
            return
        
        logger.info("🚀 啟動代理管理器...")
        
        try:
            # 初始化組件
            await self._initialize_components()
            
            # 載入現有數據
            await self._load_existing_data()
            
            # 啟動自動任務
            await self._start_auto_tasks()
            
            self._running = True
            self.stats['start_time'] = datetime.now()
            
            logger.info("✅ 代理管理器啟動成功")
            
        except Exception as e:
            logger.error(f"❌ 代理管理器啟動失敗: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """停止代理管理器"""
        if not self._running:
            return
        
        logger.info("🛑 停止代理管理器...")
        
        self._running = False
        
        # 取消所有任務
        for task in self._tasks:
            task.cancel()
        
        # 等待任務完成
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        self._tasks.clear()
        
        # 保存數據
        await self._save_data()
        
        # 停止組件
        await self.pool_manager.stop()
        
        if self.validator and hasattr(self.validator, 'close'):
            await self.validator.close()
        
        await self.advanced_fetcher_manager.close()
        await self.scanner.close()
        
        logger.info("✅ 代理管理器已停止")
    
    async def _initialize_components(self):
        """初始化組件"""
        # 初始化獲取器
        # FreeProxyFetcher 已移除，改用其他代理來源
        # if self.config.enable_free_proxy:
        #     self.fetcher_manager.add_fetcher(FreeProxyFetcher())
        
        if self.config.enable_json_file and self.config.json_file_path.exists():
            self.fetcher_manager.add_fetcher(
                JsonFileFetcher(str(self.config.json_file_path))
            )
        
        # 初始化驗證器
        self.validator = ProxyValidator(self.config.validation)
        
        self.batch_validator = BatchValidator(
            self.config.validation,
            self.config.batch_validation_size
        )
        
        # 啟動池管理器
        await self.pool_manager.start()
    
    async def _load_existing_data(self):
        """載入現有數據"""
        data_file = self.config.data_dir / "proxy_pools.json"
        if data_file.exists():
            try:
                await self.pool_manager.load_from_file(data_file)
                logger.info("📂 已載入現有代理數據")
            except Exception as e:
                logger.error(f"❌ 載入數據失敗: {e}")
    
    async def _start_auto_tasks(self):
        """啟動自動任務"""
        if self.config.auto_fetch_enabled:
            task = asyncio.create_task(self._auto_fetch_loop())
            self._tasks.append(task)
        
        if self.config.auto_cleanup_enabled:
            task = asyncio.create_task(self._auto_cleanup_loop())
            self._tasks.append(task)
        
        if self.config.auto_save_enabled:
            task = asyncio.create_task(self._auto_save_loop())
            self._tasks.append(task)
    
    async def fetch_proxies(self, sources: Optional[List[str]] = None) -> List[ProxyNode]:
        """獲取代理"""
        logger.info("🔍 開始獲取代理...")
        
        try:
            # 獲取原始代理（傳統來源）
            raw_proxies = await self.fetcher_manager.fetch_all_proxies()
            
            # 獲取高級來源代理
            advanced_proxies = await self.advanced_fetcher_manager.fetch_all_proxies()
            
            # 合併代理列表
            all_proxies = raw_proxies + advanced_proxies
            
            if not all_proxies:
                logger.warning("⚠️ 沒有獲取到任何代理")
                return []
            
            logger.info(f"📥 獲取到 {len(raw_proxies)} 個傳統代理，{len(advanced_proxies)} 個高級代理")
            
            # 使用掃描器進行快速預篩選（可選）
            if hasattr(self.config, 'scanner') and hasattr(self.config.scanner, 'enable_fast_scan') and self.config.scanner.enable_fast_scan:
                logger.info("🔍 執行快速端口掃描預篩選...")
                scanned_proxies = await self.scanner.scan_proxy_list(all_proxies)
                all_proxies = scanned_proxies
                logger.info(f"🎯 掃描後剩餘 {len(all_proxies)} 個代理")
            
            raw_proxies = all_proxies
            
            logger.info(f"📥 總共處理 {len(raw_proxies)} 個代理")
            
            # 批量驗證
            if self.batch_validator:
                validation_results = await self.batch_validator.validate_large_batch(raw_proxies)
                # 提取有效代理
                valid_proxies = [result.proxy for result in validation_results if result.is_working]
            else:
                # 如果沒有批量驗證器，跳過驗證，直接使用所有代理
                logger.warning("⚠️ 批量驗證器未初始化，跳過驗證")
                valid_proxies = raw_proxies
            
            logger.info(f"✅ 驗證完成: {len(valid_proxies)}/{len(raw_proxies)} 個代理可用")
            
            # 添加到池中
            await self.pool_manager.add_proxies(valid_proxies)
            
            # 更新統計
            self.stats['total_fetched'] += len(raw_proxies)
            self.stats['total_validated'] += len(raw_proxies)
            self.stats['total_active'] = len(valid_proxies)
            self.stats['last_fetch_time'] = datetime.now()
            self.stats['last_validation_time'] = datetime.now()
            
            return valid_proxies
            
        except Exception as e:
            logger.error(f"❌ 獲取代理失敗: {e}")
            raise
    
    async def get_proxy(self, 
                       filter_criteria: Optional[ProxyFilter] = None,
                       pool_preference: Optional[List[PoolType]] = None) -> Optional[ProxyNode]:
        """獲取代理"""
        return await self.pool_manager.get_proxy(pool_preference, filter_criteria)
    
    async def get_proxies(self, 
                         count: int = 10,
                         filter_criteria: Optional[ProxyFilter] = None,
                         pool_preference: Optional[List[PoolType]] = None) -> List[ProxyNode]:
        """批量獲取代理"""
        proxies = []
        for _ in range(count):
            proxy = await self.get_proxy(filter_criteria, pool_preference)
            if proxy:
                proxies.append(proxy)
            else:
                break
        return proxies
    
    async def validate_pools(self):
        """驗證和重新平衡代理池"""
        logger.info("🔄 開始驗證代理池...")
        await self.pool_manager.validate_and_rebalance()
        self.stats['last_validation_time'] = datetime.now()
    
    async def cleanup_pools(self):
        """清理代理池"""
        logger.info("🗑️ 開始清理代理池...")
        await self.pool_manager.cleanup_blacklist()
    
    async def _auto_fetch_loop(self):
        """自動獲取循環"""
        while self._running:
            try:
                await asyncio.sleep(self.config.auto_fetch_interval_hours * 3600)
                if self._running:
                    await self.fetch_proxies()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 自動獲取出錯: {e}")
                await asyncio.sleep(300)  # 出錯後等待5分鐘
    
    async def _auto_cleanup_loop(self):
        """自動清理循環"""
        while self._running:
            try:
                await asyncio.sleep(self.config.auto_cleanup_interval_hours * 3600)
                if self._running:
                    await self.cleanup_pools()
                    await self.validate_pools()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 自動清理出錯: {e}")
                await asyncio.sleep(300)
    
    async def _auto_save_loop(self):
        """自動保存循環"""
        while self._running:
            try:
                await asyncio.sleep(self.config.auto_save_interval_minutes * 60)
                if self._running:
                    await self._save_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ 自動保存出錯: {e}")
                await asyncio.sleep(60)
    
    async def _save_data(self):
        """保存數據"""
        try:
            data_file = self.config.data_dir / "proxy_pools.json"
            await self.pool_manager.save_to_file(data_file)
            
            # 創建備份
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.config.backup_dir / f"proxy_pools_{timestamp}.json"
            await self.pool_manager.save_to_file(backup_file)
            
            # 清理舊備份（保留最近10個）
            await self._cleanup_old_backups()
            
        except Exception as e:
            logger.error(f"❌ 保存數據失敗: {e}")
    
    async def _cleanup_old_backups(self):
        """清理舊備份文件"""
        try:
            backup_files = list(self.config.backup_dir.glob("proxy_pools_*.json"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # 保留最近10個備份
            for old_backup in backup_files[10:]:
                old_backup.unlink()
                
        except Exception as e:
            logger.error(f"❌ 清理備份失敗: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        pool_stats = self.pool_manager.get_all_stats()
        pool_summary = self.pool_manager.get_summary()
        
        return {
            'manager_stats': self.stats.copy(),
            'pool_summary': pool_summary,
            'pool_details': {k: v.__dict__ for k, v in pool_stats.items()},
            'fetcher_stats': self.fetcher_manager.get_stats(),
            'advanced_fetcher_stats': self.advanced_fetcher_manager.get_stats(),
            'config': {
                'auto_fetch_enabled': self.config.auto_fetch_enabled,
                'auto_fetch_interval_hours': self.config.auto_fetch_interval_hours,
                'auto_cleanup_enabled': self.config.auto_cleanup_enabled,
                'auto_save_enabled': self.config.auto_save_enabled
            },
            'status': {
                'running': self._running,
                'active_tasks': len(self._tasks)
            }
        }
    
    async def export_proxies(self, 
                           file_path: Path,
                           format_type: str = "json",
                           pool_types: Optional[List[PoolType]] = None) -> int:
        """導出代理到文件"""
        if pool_types is None:
            pool_types = [PoolType.HOT, PoolType.WARM, PoolType.COLD]
        
        all_proxies = []
        for pool_type in pool_types:
            if pool_type in self.pool_manager.pools:
                pool = self.pool_manager.pools[pool_type]
                active_proxies = [
                    proxy for proxy in pool.proxies.values() 
                    if proxy.status == ProxyStatus.ACTIVE
                ]
                all_proxies.extend(active_proxies)
        
        if format_type.lower() == "json":
            data = {
                'timestamp': datetime.now().isoformat(),
                'total_count': len(all_proxies),
                'proxies': [proxy.to_dict() for proxy in all_proxies]
            }
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        
        elif format_type.lower() == "txt":
            lines = []
            for proxy in all_proxies:
                lines.append(f"{proxy.host}:{proxy.port}")
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write('\n'.join(lines))
        
        elif format_type.lower() == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 寫入標題
            writer.writerow(['host', 'port', 'protocol', 'anonymity', 'country', 'score', 'response_time'])
            
            # 寫入數據
            for proxy in all_proxies:
                writer.writerow([
                    proxy.host,
                    proxy.port,
                    proxy.protocol.value,
                    proxy.anonymity.value,
                    proxy.country or '',
                    proxy.score,
                    proxy.metrics.avg_response_time or 0
                ])
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(output.getvalue())
        
        else:
            raise ValueError(f"不支持的格式: {format_type}")
        
        logger.info(f"📤 已導出 {len(all_proxies)} 個代理到: {file_path}")
        return len(all_proxies)
    
    async def import_proxies(self, file_path: Path, validate: bool = True) -> int:
        """從文件導入代理"""
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        proxies = []
        
        if file_path.suffix.lower() == '.json':
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                data = json.loads(content)
                
                if 'proxies' in data:
                    for proxy_dict in data['proxies']:
                        proxy = ProxyNode.from_dict(proxy_dict)
                        proxies.append(proxy)
                else:
                    # 簡單格式
                    for item in data:
                        if isinstance(item, dict) and 'host' in item and 'port' in item:
                            proxy = ProxyNode.from_dict(item)
                            proxies.append(proxy)
        
        elif file_path.suffix.lower() == '.txt':
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                lines = content.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        host, port = line.split(':', 1)
                        proxy = ProxyNode(
                            host=host.strip(),
                            port=int(port.strip()),
                            protocol=ProxyProtocol.HTTP
                        )
                        proxies.append(proxy)
        
        else:
            raise ValueError(f"不支持的文件格式: {file_path.suffix}")
        
        if validate and proxies:
            logger.info(f"🔍 驗證導入的 {len(proxies)} 個代理...")
            validation_results = await self.batch_validator.validate_large_batch(proxies)
            valid_proxies = [result.proxy for result in validation_results if result.is_working]
            await self.pool_manager.add_proxies(valid_proxies)
            logger.info(f"✅ 導入完成: {len(valid_proxies)}/{len(proxies)} 個代理可用")
            return len(valid_proxies)
        else:
            await self.pool_manager.add_proxies(proxies)
            logger.info(f"📥 導入 {len(proxies)} 個代理（未驗證）")
            return len(proxies)


# 使用示例
if __name__ == "__main__":
    async def main():
        # 創建配置
        config = ProxyManagerConfig(
            data_dir=Path("data/proxy_manager"),
            auto_fetch_enabled=True,
            auto_fetch_interval_hours=6
        )
        
        # 創建管理器
        manager = ProxyManager(config)
        
        try:
            # 啟動管理器
            await manager.start()
            
            # 獲取代理
            await manager.fetch_proxies()
            
            # 獲取單個代理
            proxy = await manager.get_proxy()
            if proxy:
                print(f"獲取到代理: {proxy.url}")
            
            # 獲取統計信息
            stats = manager.get_stats()
            print(f"統計信息: {stats['pool_summary']}")
            
            # 導出代理
            await manager.export_proxies(Path("exported_proxies.json"))
            
        finally:
            await manager.stop()


# 增強掃描功能
class EnhancedProxyManager(ProxyManager):
    """增強代理管理器，包含掃描功能"""
    
    async def scan_ip_range(self, ip_range: str, ports: Optional[List[int]] = None) -> List[ScanResult]:
        """掃描 IP 範圍尋找代理
        
        Args:
            ip_range: CIDR 格式的 IP 範圍，如 "192.168.1.0/24"
            ports: 要掃描的端口列表，默認使用配置中的端口
            
        Returns:
            List[ScanResult]: 掃描結果列表
        """
        try:
            logger.info(f"開始掃描 IP 範圍: {ip_range}")
            
            # 使用增強掃描器
            results = await self.enhanced_scanner.scan_ip_range(ip_range, ports)
            
            # 將成功的掃描結果轉換為代理節點
            for result in results:
                if result.result.value == "success" and result.proxy_node:
                    # 添加到代理池
                    await self.pool_manager.add_proxy(result.proxy_node)
            
            logger.info(f"IP 範圍掃描完成，發現 {len([r for r in results if r.result.value == 'success'])} 個代理")
            return results
            
        except Exception as e:
            logger.error(f"IP 範圍掃描失敗: {e}")
            return []
    
    async def scan_single_target(self, host: str, port: int, protocols: Optional[List[str]] = None) -> List[ScanResult]:
        """掃描單個目標
        
        Args:
            host: 目標主機
            port: 目標端口
            protocols: 要測試的協議列表
            
        Returns:
            List[ScanResult]: 掃描結果列表
        """
        try:
            logger.info(f"開始掃描目標: {host}:{port}")
            
            # 創建掃描目標
            target = ScanTarget(host=host, port=port)
            if protocols:
                from .models import ScanProtocol
                target.protocols = [ScanProtocol(p) for p in protocols]
            
            # 使用增強掃描器掃描單個目標
            results = []
            for protocol in target.protocols:
                result = await self.enhanced_scanner._scan_single_target(target)
                results.append(result)
            
            # 將成功的掃描結果轉換為代理節點
            for result in results:
                if result.result.value == "success" and result.proxy_node:
                    # 添加到代理池
                    await self.pool_manager.add_proxy(result.proxy_node)
            
            logger.info(f"目標掃描完成，發現 {len([r for r in results if r.result.value == 'success'])} 個代理")
            return results
            
        except Exception as e:
            logger.error(f"目標掃描失敗: {e}")
            return []
    
    async def get_scan_statistics(self) -> Dict[str, Any]:
        """獲取掃描統計信息
        
        Returns:
            Dict[str, Any]: 掃描統計信息
        """
        try:
            return await self.enhanced_scanner.get_statistics()
        except Exception as e:
            logger.error(f"獲取掃描統計失敗: {e}")
            return {}


if __name__ == "__main__":
    asyncio.run(main())