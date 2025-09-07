#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增強代理探測器 (Enhanced Proxy Scanner)

基於現有的 ProxyScanner 擴展，提供更強大的代理發現功能：
- IP 範圍掃描
- 多協議檢測 (HTTP/SOCKS4/SOCKS5)
- 批量端口掃描
- 智能代理類型識別
- 異步並發處理

作者: AI Assistant (TRAE)
日期: 2025-01-07
版本: 1.0.0
"""

import asyncio
import ipaddress
import socket
import struct
import time
import random
from typing import List, Dict, Optional, Tuple, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import aiofiles

# 導入現有模型
from .models import ProxyNode, ProxyProtocol, ProxyStatus, ProxyAnonymity

logger = logging.getLogger(__name__)


class ScanProtocol(Enum):
    """掃描協議枚舉"""
    HTTP = "http"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"
    HTTPS = "https"


class ScanStatus(Enum):
    """掃描狀態枚舉"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CONNECTION_REFUSED = "connection_refused"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ScanTarget:
    """掃描目標"""
    host: str
    port: int
    protocols: List[ScanProtocol] = field(default_factory=lambda: [ScanProtocol.HTTP])
    priority: int = 1  # 1-10, 10為最高優先級


@dataclass
class ScanResult:
    """掃描結果"""
    target: ScanTarget
    protocol: ScanProtocol
    result: ScanStatus
    response_time: float = 0.0
    error_message: str = ""
    proxy_node: Optional[ProxyNode] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ScanConfig:
    """掃描配置"""
    # 並發控制
    max_concurrent_scans: int = 100
    max_concurrent_connections: int = 50
    
    # 超時設置
    connection_timeout: float = 3.0
    read_timeout: float = 5.0
    
    # 重試設置
    max_retries: int = 2
    retry_delay: float = 0.5
    
    # 掃描範圍
    default_ports: List[int] = field(default_factory=lambda: [80, 8080, 3128, 1080, 1081, 9050, 9051])
    http_ports: List[int] = field(default_factory=lambda: [80, 8080, 3128, 8000, 8888])
    socks_ports: List[int] = field(default_factory=lambda: [1080, 1081, 9050, 9051])
    
    # 輸出設置
    save_results: bool = True
    output_file: str = "scan_results.json"
    
    # 過濾設置
    min_response_time: float = 0.1
    max_response_time: float = 10.0


class EnhancedProxyScanner:
    """增強代理探測器"""
    
    def __init__(self, config: Optional[ScanConfig] = None):
        self.config = config or ScanConfig()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 統計信息
        self.stats = {
            'total_scanned': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'proxies_found': 0,
            'scan_duration': 0.0
        }
        
        # 結果存儲
        self.scan_results: List[ScanResult] = []
        self.found_proxies: List[ProxyNode] = []
        
        # 並發控制
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent_scans)
        self.connection_semaphore = asyncio.Semaphore(self.config.max_concurrent_connections)
    
    async def scan_ip_range(
        self, 
        ip_range: str, 
        ports: Optional[List[int]] = None,
        protocols: Optional[List[ScanProtocol]] = None
    ) -> List[ProxyNode]:
        """
        掃描 IP 範圍尋找代理
        
        Args:
            ip_range: IP 範圍，支持 CIDR 格式 (如: 192.168.1.0/24)
            ports: 要掃描的端口列表，None 使用默認端口
            protocols: 要檢測的協議列表，None 使用默認協議
            
        Returns:
            List[ProxyNode]: 發現的代理列表
        """
        self.logger.info(f"開始掃描 IP 範圍: {ip_range}")
        start_time = time.time()
        
        # 生成掃描目標
        targets = self._generate_scan_targets(ip_range, ports, protocols)
        self.logger.info(f"生成 {len(targets)} 個掃描目標")
        
        # 執行掃描
        await self._scan_targets(targets)
        
        # 更新統計
        self.stats['scan_duration'] = time.time() - start_time
        self.stats['total_scanned'] = len(targets)
        self.stats['successful_scans'] = len([r for r in self.scan_results if r.result == ScanStatus.SUCCESS])
        self.stats['failed_scans'] = len([r for r in self.scan_results if r.result != ScanStatus.SUCCESS])
        self.stats['proxies_found'] = len(self.found_proxies)
        
        # 保存結果
        if self.config.save_results:
            await self._save_results()
        
        self.logger.info(
            f"掃描完成: 掃描 {self.stats['total_scanned']} 個目標, "
            f"發現 {self.stats['proxies_found']} 個代理, "
            f"耗時 {self.stats['scan_duration']:.2f} 秒"
        )
        
        return self.found_proxies
    
    def _generate_scan_targets(
        self, 
        ip_range: str, 
        ports: Optional[List[int]], 
        protocols: Optional[List[ScanProtocol]]
    ) -> List[ScanTarget]:
        """生成掃描目標列表"""
        targets = []
        
        # 解析 IP 範圍
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
        except ValueError as e:
            self.logger.error(f"無效的 IP 範圍: {ip_range}, 錯誤: {e}")
            return targets
        
        # 使用默認端口和協議
        if ports is None:
            ports = self.config.default_ports
        if protocols is None:
            protocols = [ScanProtocol.HTTP, ScanProtocol.SOCKS4, ScanProtocol.SOCKS5]
        
        # 生成目標
        for ip in network.hosts():
            for port in ports:
                for protocol in protocols:
                    target = ScanTarget(
                        host=str(ip),
                        port=port,
                        protocols=[protocol]
                    )
                    targets.append(target)
        
        return targets
    
    async def _scan_targets(self, targets: List[ScanTarget]) -> None:
        """並發掃描目標列表"""
        tasks = []
        
        for target in targets:
            task = asyncio.create_task(self._scan_single_target(target))
            tasks.append(task)
        
        # 等待所有掃描完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"掃描目標 {targets[i]} 時發生錯誤: {result}")
            elif isinstance(result, ScanResult) and result.result == ScanStatus.SUCCESS:
                if result.proxy_node:
                    self.found_proxies.append(result.proxy_node)
    
    async def _scan_single_target(self, target: ScanTarget) -> ScanResult:
        """掃描單個目標"""
        async with self.semaphore:
            for protocol in target.protocols:
                try:
                    result = await self._test_proxy_connection(target, protocol)
                    if result.result == ScanResult.SUCCESS:
                        self.scan_results.append(result)
                        return result
                except Exception as e:
                    self.logger.debug(f"掃描 {target.host}:{target.port} ({protocol.value}) 失敗: {e}")
                    continue
            
            # 所有協議都失敗
            return ScanResult(
                target=target,
                protocol=target.protocols[0],
                result=ScanStatus.FAILED,
                error_message="所有協議測試失敗"
            )
    
    async def _test_proxy_connection(self, target: ScanTarget, protocol: ScanProtocol) -> ScanResult:
        """測試代理連接"""
        start_time = time.time()
        
        try:
            if protocol == ScanProtocol.HTTP:
                return await self._test_http_proxy(target, start_time)
            elif protocol == ScanProtocol.SOCKS4:
                return await self._test_socks4_proxy(target, start_time)
            elif protocol == ScanProtocol.SOCKS5:
                return await self._test_socks5_proxy(target, start_time)
            else:
                return ScanResult(
                    target=target,
                    protocol=protocol,
                    result=ScanStatus.FAILED,
                    error_message=f"不支持的協議: {protocol.value}"
                )
        
        except asyncio.TimeoutError:
            return ScanResult(
                target=target,
                protocol=protocol,
                result=ScanStatus.TIMEOUT,
                response_time=time.time() - start_time,
                error_message="連接超時"
            )
        except Exception as e:
            return ScanResult(
                target=target,
                protocol=protocol,
                result=ScanStatus.UNKNOWN_ERROR,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _test_http_proxy(self, target: ScanTarget, start_time: float) -> ScanResult:
        """測試 HTTP 代理"""
        try:
            # 創建 HTTP 代理測試請求
            test_url = "http://httpbin.org/ip"
            proxy_url = f"http://{target.host}:{target.port}"
            
            # 使用 aiohttp 測試
            import aiohttp
            
            timeout = aiohttp.ClientTimeout(total=self.config.connection_timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(test_url, proxy=proxy_url) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        
                        # 創建代理節點
                        proxy_node = ProxyNode(
                            host=target.host,
                            port=target.port,
                            protocol=ProxyProtocol.HTTP,
                            anonymity=ProxyAnonymity.UNKNOWN,
                            source="enhanced_scanner",
                            status=ProxyStatus.ACTIVE
                        )
                        
                        return ScanResult(
                            target=target,
                            protocol=ScanProtocol.HTTP,
                            result=ScanStatus.SUCCESS,
                            response_time=response_time,
                            proxy_node=proxy_node
                        )
                    else:
                        return ScanResult(
                            target=target,
                            protocol=ScanProtocol.HTTP,
                            result=ScanStatus.FAILED,
                            response_time=time.time() - start_time,
                            error_message=f"HTTP 狀態碼: {response.status}"
                        )
        
        except Exception as e:
            return ScanResult(
                target=target,
                protocol=ScanProtocol.HTTP,
                result=ScanStatus.FAILED,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    async def _test_socks4_proxy(self, target: ScanTarget, start_time: float) -> ScanResult:
        """測試 SOCKS4 代理"""
        try:
            # 在線程池中執行 SOCKS4 測試
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._test_socks4_sync, 
                    target.host, 
                    target.port
                )
            
            if result:
                response_time = time.time() - start_time
                
                proxy_node = ProxyNode(
                    host=target.host,
                    port=target.port,
                    protocol=ProxyProtocol.SOCKS4,
                    anonymity=ProxyAnonymity.UNKNOWN,
                    source="enhanced_scanner",
                    status=ProxyStatus.ACTIVE
                )
                
                return ScanResult(
                    target=target,
                    protocol=ScanProtocol.SOCKS4,
                    result=ScanStatus.SUCCESS,
                    response_time=response_time,
                    proxy_node=proxy_node
                )
            else:
                return ScanResult(
                    target=target,
                    protocol=ScanProtocol.SOCKS4,
                    result=ScanStatus.FAILED,
                    response_time=time.time() - start_time,
                    error_message="SOCKS4 連接失敗"
                )
        
        except Exception as e:
            return ScanResult(
                target=target,
                protocol=ScanProtocol.SOCKS4,
                result=ScanStatus.FAILED,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_socks4_sync(self, host: str, port: int) -> bool:
        """同步測試 SOCKS4 代理"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.connection_timeout)
            
            # 連接到代理
            sock.connect((host, port))
            
            # 發送 SOCKS4 握手請求
            # 格式: [VERSION][COMMAND][PORT][IP][USERID]
            request = struct.pack('!BBH', 4, 1, 80)  # SOCKS4, CONNECT, port 80
            request += socket.inet_aton('127.0.0.1')  # 目標 IP
            request += b'\x00'  # 空用戶名
            
            sock.send(request)
            
            # 接收響應
            response = sock.recv(8)
            sock.close()
            
            if len(response) >= 2:
                version, status = struct.unpack('!BB', response[:2])
                return version == 0 and status == 90  # 成功響應
            
            return False
        
        except Exception:
            return False
    
    async def _test_socks5_proxy(self, target: ScanTarget, start_time: float) -> ScanResult:
        """測試 SOCKS5 代理"""
        try:
            # 在線程池中執行 SOCKS5 測試
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                result = await loop.run_in_executor(
                    executor, 
                    self._test_socks5_sync, 
                    target.host, 
                    target.port
                )
            
            if result:
                response_time = time.time() - start_time
                
                proxy_node = ProxyNode(
                    host=target.host,
                    port=target.port,
                    protocol=ProxyProtocol.SOCKS5,
                    anonymity=ProxyAnonymity.UNKNOWN,
                    source="enhanced_scanner",
                    status=ProxyStatus.ACTIVE
                )
                
                return ScanResult(
                    target=target,
                    protocol=ScanProtocol.SOCKS5,
                    result=ScanStatus.SUCCESS,
                    response_time=response_time,
                    proxy_node=proxy_node
                )
            else:
                return ScanResult(
                    target=target,
                    protocol=ScanProtocol.SOCKS5,
                    result=ScanStatus.FAILED,
                    response_time=time.time() - start_time,
                    error_message="SOCKS5 連接失敗"
                )
        
        except Exception as e:
            return ScanResult(
                target=target,
                protocol=ScanProtocol.SOCKS5,
                result=ScanStatus.FAILED,
                response_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _test_socks5_sync(self, host: str, port: int) -> bool:
        """同步測試 SOCKS5 代理"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.config.connection_timeout)
            
            # 連接到代理
            sock.connect((host, port))
            
            # SOCKS5 握手
            # 1. 發送認證方法
            sock.send(b'\x05\x01\x00')  # SOCKS5, 1 method, no auth
            
            # 2. 接收認證方法響應
            response = sock.recv(2)
            if len(response) != 2 or response[0] != 5:
                sock.close()
                return False
            
            if response[1] != 0:  # 需要認證
                sock.close()
                return False
            
            # 3. 發送連接請求
            request = b'\x05\x01\x00\x01'  # SOCKS5, CONNECT, reserved, IPv4
            request += socket.inet_aton('127.0.0.1')  # 目標 IP
            request += struct.pack('!H', 80)  # 目標端口
            
            sock.send(request)
            
            # 4. 接收連接響應
            response = sock.recv(10)
            sock.close()
            
            if len(response) >= 2:
                version, status = struct.unpack('!BB', response[:2])
                return version == 5 and status == 0  # 成功響應
            
            return False
        
        except Exception:
            return False
    
    async def _save_results(self) -> None:
        """保存掃描結果"""
        try:
            results_data = {
                'scan_config': {
                    'max_concurrent_scans': self.config.max_concurrent_scans,
                    'connection_timeout': self.config.connection_timeout,
                    'default_ports': self.config.default_ports
                },
                'stats': self.stats,
                'scan_results': [
                    {
                        'target': {
                            'host': r.target.host,
                            'port': r.target.port,
                            'protocols': [p.value for p in r.target.protocols]
                        },
                        'protocol': r.protocol.value,
                        'result': r.result.value,
                        'response_time': r.response_time,
                        'error_message': r.error_message,
                        'timestamp': r.timestamp
                    }
                    for r in self.scan_results
                ],
                'found_proxies': [
                    {
                        'host': p.host,
                        'port': p.port,
                        'protocol': p.protocol.value,
                        'anonymity': p.anonymity.value,
                        'source': p.source,
                        'status': p.status.value
                    }
                    for p in self.found_proxies
                ]
            }
            
            async with aiofiles.open(self.config.output_file, 'w', encoding='utf-8') as f:
                import json
                await f.write(json.dumps(results_data, indent=2, ensure_ascii=False))
            
            self.logger.info(f"掃描結果已保存到: {self.config.output_file}")
        
        except Exception as e:
            self.logger.error(f"保存結果失敗: {e}")
    
    def get_stats(self) -> Dict[str, any]:
        """獲取統計信息"""
        return self.stats.copy()
    
    def get_found_proxies(self) -> List[ProxyNode]:
        """獲取發現的代理列表"""
        return self.found_proxies.copy()
    
    def clear_results(self) -> None:
        """清空結果"""
        self.scan_results.clear()
        self.found_proxies.clear()
        self.stats = {
            'total_scanned': 0,
            'successful_scans': 0,
            'failed_scans': 0,
            'proxies_found': 0,
            'scan_duration': 0.0
        }


# 便利函數
async def scan_ip_range_for_proxies(
    ip_range: str,
    ports: Optional[List[int]] = None,
    config: Optional[ScanConfig] = None
) -> List[ProxyNode]:
    """
    掃描 IP 範圍尋找代理的便利函數
    
    Args:
        ip_range: IP 範圍 (CIDR 格式)
        ports: 要掃描的端口列表
        config: 掃描配置
        
    Returns:
        List[ProxyNode]: 發現的代理列表
    """
    scanner = EnhancedProxyScanner(config)
    return await scanner.scan_ip_range(ip_range, ports)


# 使用示例
if __name__ == "__main__":
    async def main():
        # 設置日誌
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 創建掃描配置
        config = ScanConfig(
            max_concurrent_scans=50,
            connection_timeout=2.0,
            default_ports=[80, 8080, 3128, 1080],
            save_results=True,
            output_file="proxy_scan_results.json"
        )
        
        # 創建掃描器
        scanner = EnhancedProxyScanner(config)
        
        # 掃描示例 IP 範圍 (請使用合法的測試範圍)
        print("開始掃描代理...")
        proxies = await scanner.scan_ip_range(
            ip_range="127.0.0.1/32",  # 僅掃描本地
            ports=[8080, 3128],  # 常用代理端口
            protocols=[ScanProtocol.HTTP, ScanProtocol.SOCKS4, ScanProtocol.SOCKS5]
        )
        
        # 顯示結果
        print(f"\n掃描完成！發現 {len(proxies)} 個代理:")
        for proxy in proxies:
            print(f"  {proxy.host}:{proxy.port} ({proxy.protocol.value})")
        
        # 顯示統計
        stats = scanner.get_stats()
        print(f"\n統計信息:")
        print(f"  總掃描數: {stats['total_scanned']}")
        print(f"  成功掃描: {stats['successful_scans']}")
        print(f"  失敗掃描: {stats['failed_scans']}")
        print(f"  發現代理: {stats['proxies_found']}")
        print(f"  掃描耗時: {stats['scan_duration']:.2f} 秒")
    
    # 運行示例
    asyncio.run(main())
