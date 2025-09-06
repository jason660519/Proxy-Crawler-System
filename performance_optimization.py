#!/usr/bin/env python3
"""
性能優化腳本

分析系統性能瓶頸並提供優化建議
"""

import asyncio
import time
import psutil
import sys
from pathlib import Path
from typing import Dict, List, Any
import logging

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.proxy_manager.manager import ProxyManager
from src.proxy_manager.config import ProxyManagerConfig

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.start_time = time.time()
        self.memory_usage = []
        self.cpu_usage = []
        self.measurements = {}
    
    def start_monitoring(self):
        """開始監控"""
        self.start_time = time.time()
        self.memory_usage = []
        self.cpu_usage = []
    
    def record_metrics(self):
        """記錄當前指標"""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        
        self.memory_usage.append(memory_mb)
        self.cpu_usage.append(cpu_percent)
    
    def get_peak_memory(self) -> float:
        """獲取峰值記憶體使用"""
        return max(self.memory_usage) if self.memory_usage else 0
    
    def get_avg_cpu(self) -> float:
        """獲取平均 CPU 使用率"""
        return sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
    
    def get_duration(self) -> float:
        """獲取總耗時"""
        return time.time() - self.start_time


class PerformanceOptimizer:
    """性能優化器"""
    
    def __init__(self):
        self.analyzer = PerformanceAnalyzer()
        self.optimization_suggestions = []
    
    async def analyze_system_performance(self):
        """分析系統性能"""
        print("🔍 系統性能分析")
        print("=" * 50)
        
        # 1. 記憶體使用分析
        await self._analyze_memory_usage()
        
        # 2. CPU 使用分析
        await self._analyze_cpu_usage()
        
        # 3. 網路 I/O 分析
        await self._analyze_network_io()
        
        # 4. 代理獲取性能分析
        await self._analyze_proxy_fetching()
        
        # 5. 代理驗證性能分析
        await self._analyze_proxy_validation()
        
        # 6. 生成優化建議
        self._generate_optimization_suggestions()
    
    async def _analyze_memory_usage(self):
        """分析記憶體使用"""
        print("\n1️⃣ 記憶體使用分析")
        print("-" * 30)
        
        # 獲取系統記憶體信息
        memory = psutil.virtual_memory()
        print(f"總記憶體: {memory.total / 1024 / 1024 / 1024:.2f} GB")
        print(f"可用記憶體: {memory.available / 1024 / 1024 / 1024:.2f} GB")
        print(f"使用率: {memory.percent:.1f}%")
        
        # 分析 Python 進程記憶體
        process = psutil.Process()
        memory_info = process.memory_info()
        print(f"Python 進程記憶體: {memory_info.rss / 1024 / 1024:.2f} MB")
        
        # 檢查記憶體洩漏
        if memory.percent > 80:
            self.optimization_suggestions.append({
                'type': 'memory',
                'priority': 'high',
                'issue': '記憶體使用率過高',
                'suggestion': '考慮減少並發數或增加記憶體'
            })
    
    async def _analyze_cpu_usage(self):
        """分析 CPU 使用"""
        print("\n2️⃣ CPU 使用分析")
        print("-" * 30)
        
        # 獲取 CPU 信息
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        print(f"CPU 核心數: {cpu_count}")
        print(f"CPU 使用率: {cpu_percent:.1f}%")
        
        # 檢查 CPU 使用率
        if cpu_percent > 80:
            self.optimization_suggestions.append({
                'type': 'cpu',
                'priority': 'high',
                'issue': 'CPU 使用率過高',
                'suggestion': '考慮減少並發數或優化算法'
            })
    
    async def _analyze_network_io(self):
        """分析網路 I/O"""
        print("\n3️⃣ 網路 I/O 分析")
        print("-" * 30)
        
        # 獲取網路統計
        net_io = psutil.net_io_counters()
        print(f"發送字節: {net_io.bytes_sent / 1024 / 1024:.2f} MB")
        print(f"接收字節: {net_io.bytes_recv / 1024 / 1024:.2f} MB")
        print(f"發送包數: {net_io.packets_sent}")
        print(f"接收包數: {net_io.packets_recv}")
    
    async def _analyze_proxy_fetching(self):
        """分析代理獲取性能"""
        print("\n4️⃣ 代理獲取性能分析")
        print("-" * 30)
        
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False
            config.auto_cleanup_enabled = False
            config.auto_save_enabled = False
            
            # 創建管理器
            manager = ProxyManager(config)
            
            # 開始監控
            self.analyzer.start_monitoring()
            
            # 測試代理獲取
            print("正在測試代理獲取性能...")
            start_time = time.time()
            
            proxies = await manager.fetch_proxies()
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"獲取代理數: {len(proxies)}")
            print(f"耗時: {duration:.2f} 秒")
            print(f"平均每個代理: {duration/len(proxies)*1000:.2f} ms" if proxies else "N/A")
            
            # 記錄指標
            self.analyzer.record_metrics()
            
            # 檢查性能
            if duration > 60:  # 超過 1 分鐘
                self.optimization_suggestions.append({
                    'type': 'performance',
                    'priority': 'medium',
                    'issue': '代理獲取耗時過長',
                    'suggestion': '考慮優化網路請求或減少獲取源'
                })
            
            await manager.stop()
            
        except Exception as e:
            print(f"❌ 代理獲取性能分析失敗: {e}")
    
    async def _analyze_proxy_validation(self):
        """分析代理驗證性能"""
        print("\n5️⃣ 代理驗證性能分析")
        print("-" * 30)
        
        try:
            # 創建配置
            config = ProxyManagerConfig()
            config.auto_fetch_enabled = False
            config.auto_cleanup_enabled = False
            config.auto_save_enabled = False
            
            # 創建管理器
            manager = ProxyManager(config)
            await manager.start()
            
            # 獲取一些代理進行驗證測試
            proxies = await manager.fetch_proxies()
            
            if proxies:
                # 測試驗證性能
                print(f"正在測試 {len(proxies)} 個代理的驗證性能...")
                start_time = time.time()
                
                await manager.validate_pools()
                
                end_time = time.time()
                duration = end_time - start_time
                
                print(f"驗證耗時: {duration:.2f} 秒")
                print(f"平均每個代理: {duration/len(proxies)*1000:.2f} ms")
                
                # 檢查性能
                if duration > 30:  # 超過 30 秒
                    self.optimization_suggestions.append({
                        'type': 'performance',
                        'priority': 'medium',
                        'issue': '代理驗證耗時過長',
                        'suggestion': '考慮減少並發驗證數或優化驗證邏輯'
                    })
            
            await manager.stop()
            
        except Exception as e:
            print(f"❌ 代理驗證性能分析失敗: {e}")
    
    def _generate_optimization_suggestions(self):
        """生成優化建議"""
        print("\n6️⃣ 優化建議")
        print("-" * 30)
        
        if not self.optimization_suggestions:
            print("✅ 系統性能良好，無需優化")
            return
        
        # 按優先級排序
        high_priority = [s for s in self.optimization_suggestions if s['priority'] == 'high']
        medium_priority = [s for s in self.optimization_suggestions if s['priority'] == 'medium']
        low_priority = [s for s in self.optimization_suggestions if s['priority'] == 'low']
        
        if high_priority:
            print("\n🔴 高優先級問題:")
            for suggestion in high_priority:
                print(f"  • {suggestion['issue']}")
                print(f"    建議: {suggestion['suggestion']}")
        
        if medium_priority:
            print("\n🟡 中優先級問題:")
            for suggestion in medium_priority:
                print(f"  • {suggestion['issue']}")
                print(f"    建議: {suggestion['suggestion']}")
        
        if low_priority:
            print("\n🟢 低優先級問題:")
            for suggestion in low_priority:
                print(f"  • {suggestion['issue']}")
                print(f"    建議: {suggestion['suggestion']}")
    
    def apply_optimizations(self):
        """應用優化建議"""
        print("\n🔧 應用性能優化")
        print("=" * 50)
        
        # 1. 優化配置參數
        self._optimize_config_parameters()
        
        # 2. 優化記憶體使用
        self._optimize_memory_usage()
        
        # 3. 優化並發設置
        self._optimize_concurrency()
        
        # 4. 生成優化後的配置
        self._generate_optimized_config()
    
    def _optimize_config_parameters(self):
        """優化配置參數"""
        print("\n1️⃣ 優化配置參數")
        print("-" * 30)
        
        # 根據系統資源調整參數
        memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024
        cpu_count = psutil.cpu_count()
        
        # 計算最佳並發數
        optimal_concurrent_scans = min(cpu_count * 2, 100)
        optimal_concurrent_validations = min(cpu_count * 4, 200)
        
        print(f"系統記憶體: {memory_gb:.1f} GB")
        print(f"CPU 核心數: {cpu_count}")
        print(f"建議掃描並發數: {optimal_concurrent_scans}")
        print(f"建議驗證並發數: {optimal_concurrent_validations}")
        
        # 根據記憶體調整代理池大小
        if memory_gb < 4:
            max_pool_size = 1000
        elif memory_gb < 8:
            max_pool_size = 5000
        else:
            max_pool_size = 10000
        
        print(f"建議最大代理池大小: {max_pool_size}")
    
    def _optimize_memory_usage(self):
        """優化記憶體使用"""
        print("\n2️⃣ 優化記憶體使用")
        print("-" * 30)
        
        suggestions = [
            "啟用代理池自動清理",
            "設置合理的代理池大小限制",
            "定期清理無效代理",
            "使用生成器而非列表存儲大量代理"
        ]
        
        for suggestion in suggestions:
            print(f"  • {suggestion}")
    
    def _optimize_concurrency(self):
        """優化並發設置"""
        print("\n3️⃣ 優化並發設置")
        print("-" * 30)
        
        suggestions = [
            "根據系統資源調整並發數",
            "使用連接池管理 HTTP 連接",
            "實現請求速率限制",
            "使用異步 I/O 提高效率"
        ]
        
        for suggestion in suggestions:
            print(f"  • {suggestion}")
    
    def _generate_optimized_config(self):
        """生成優化後的配置"""
        print("\n4️⃣ 生成優化配置")
        print("-" * 30)
        
        # 計算優化參數
        memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024
        cpu_count = psutil.cpu_count()
        
        # 生成優化配置
        optimized_config = {
            "scanner": {
                "max_concurrent": min(cpu_count * 2, 100),
                "timeout": 5,
                "retry_count": 2
            },
            "validation": {
                "max_concurrent": min(cpu_count * 4, 200),
                "timeout": 10,
                "retry_count": 2
            },
            "pools": {
                "max_pool_size": min(int(memory_gb * 1000), 10000),
                "auto_cleanup_enabled": True,
                "cleanup_interval_hours": 6
            },
            "fetchers": {
                "max_concurrent": min(cpu_count * 3, 150),
                "timeout": 30,
                "retry_count": 3
            }
        }
        
        # 保存優化配置
        import json
        config_path = Path("config/optimized_config.json")
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(optimized_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 優化配置已保存到: {config_path}")
        print("\n優化配置內容:")
        for section, params in optimized_config.items():
            print(f"\n{section}:")
            for key, value in params.items():
                print(f"  {key}: {value}")


async def main():
    """主函數"""
    print("🚀 JasonSpider 性能優化工具")
    print("=" * 60)
    
    optimizer = PerformanceOptimizer()
    
    try:
        # 分析系統性能
        await optimizer.analyze_system_performance()
        
        # 應用優化建議
        optimizer.apply_optimizations()
        
        print("\n🎉 性能優化完成！")
        print("\n📋 下一步:")
        print("1. 檢查生成的優化配置文件")
        print("2. 根據建議調整系統參數")
        print("3. 重新測試系統性能")
        print("4. 監控優化效果")
        
    except Exception as e:
        print(f"\n❌ 性能優化失敗: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️ 優化被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 優化執行失敗: {e}")
        sys.exit(1)
