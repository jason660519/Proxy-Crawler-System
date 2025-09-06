"""ZMap 整合模組

提供高性能網路掃描功能：
- ZMap/Masscan 風格的大規模掃描
- 智能目標發現
- 分散式掃描支援
- 合規性檢查
"""

import asyncio
import subprocess
import json
import ipaddress
import random
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
import tempfile
import shutil

from .models import ProxyNode, ProxyProtocol, ProxyStatus
from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ScanTarget:
    """掃描目標配置"""
    ip_range: str
    ports: List[int]
    protocol: str = "tcp"
    max_rate: int = 1000  # 每秒封包數
    timeout: float = 10.0
    exclude_ranges: List[str] = None
    
    def __post_init__(self):
        if self.exclude_ranges is None:
            # 預設排除私有網段和敏感範圍
            self.exclude_ranges = [
                "10.0.0.0/8",
                "172.16.0.0/12", 
                "192.168.0.0/16",
                "127.0.0.0/8",
                "169.254.0.0/16",
                "224.0.0.0/4",  # 多播
                "240.0.0.0/4"   # 保留
            ]


@dataclass
class ScanResult:
    """掃描結果"""
    target: ScanTarget
    open_ports: List[Tuple[str, int]]
    scan_time: datetime
    duration: float
    total_hosts: int
    responsive_hosts: int
    scan_rate: float
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class ZMapIntegration:
    """ZMap 整合類
    
    提供高性能網路掃描功能，支援多種掃描工具
    """
    
    def __init__(self):
        self.config = get_config()
        self.available_tools = self._detect_available_tools()
        self.scan_history: List[ScanResult] = []
        
        # 常見代理端口
        self.common_proxy_ports = [
            80, 8080, 3128, 8000, 8888, 9999, 8118, 8123, 8181,
            1080, 1081, 1085, 4145, 5678,  # SOCKS
            443, 8443, 8843,  # HTTPS
            3129, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8089,
            9000, 9001, 9002, 9003, 9080, 9090, 9091, 9092, 9093,
            6588, 8090, 8888, 8889, 9000, 9001, 9002, 9003, 9080
        ]
        
        # 合規性檢查
        self.compliance_rules = {
            "max_scan_rate": 10000,  # 每秒最大封包數
            "respect_robots_txt": True,
            "exclude_government_ranges": True,
            "require_explicit_permission": True,
            "log_all_scans": True
        }
    
    def _detect_available_tools(self) -> Dict[str, bool]:
        """檢測可用的掃描工具"""
        tools = {
            "zmap": False,
            "masscan": False,
            "nmap": False,
            "rustscan": False
        }
        
        for tool in tools.keys():
            try:
                result = subprocess.run(
                    [tool, "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=5
                )
                tools[tool] = result.returncode == 0
                if tools[tool]:
                    logger.info(f"✅ 檢測到掃描工具: {tool}")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.debug(f"❌ 掃描工具不可用: {tool}")
        
        return tools
    
    async def scan_for_proxies(self, 
                              ip_ranges: List[str], 
                              ports: Optional[List[int]] = None,
                              max_rate: int = 1000) -> List[ProxyNode]:
        """掃描指定範圍尋找潛在代理
        
        Args:
            ip_ranges: IP 範圍列表 (CIDR 格式)
            ports: 要掃描的端口列表
            max_rate: 最大掃描速率 (每秒封包數)
            
        Returns:
            發現的潛在代理列表
        """
        if ports is None:
            ports = self.common_proxy_ports
        
        # 合規性檢查
        if not await self._compliance_check(ip_ranges, max_rate):
            raise ValueError("掃描請求未通過合規性檢查")
        
        logger.info(f"🔍 開始掃描 {len(ip_ranges)} 個範圍，{len(ports)} 個端口")
        
        all_proxies = []
        
        for ip_range in ip_ranges:
            target = ScanTarget(
                ip_range=ip_range,
                ports=ports,
                max_rate=min(max_rate, self.compliance_rules["max_scan_rate"])
            )
            
            scan_result = await self._execute_scan(target)
            proxies = self._convert_to_proxies(scan_result)
            all_proxies.extend(proxies)
            
            # 記錄掃描歷史
            self.scan_history.append(scan_result)
        
        logger.info(f"✅ 掃描完成，發現 {len(all_proxies)} 個潛在代理")
        return all_proxies
    
    async def _compliance_check(self, ip_ranges: List[str], max_rate: int) -> bool:
        """合規性檢查"""
        # 檢查掃描速率
        if max_rate > self.compliance_rules["max_scan_rate"]:
            logger.error(f"掃描速率 {max_rate} 超過限制 {self.compliance_rules['max_scan_rate']}")
            return False
        
        # 檢查目標範圍
        for ip_range in ip_ranges:
            try:
                network = ipaddress.ip_network(ip_range, strict=False)
                
                # 檢查是否為私有網段
                if network.is_private:
                    logger.warning(f"目標包含私有網段: {ip_range}")
                
                # 檢查是否為保留網段
                if network.is_reserved:
                    logger.error(f"目標包含保留網段: {ip_range}")
                    return False
                
                # 檢查是否為多播網段
                if network.is_multicast:
                    logger.error(f"目標包含多播網段: {ip_range}")
                    return False
                    
            except ValueError as e:
                logger.error(f"無效的 IP 範圍: {ip_range} - {e}")
                return False
        
        # 記錄掃描請求
        if self.compliance_rules["log_all_scans"]:
            logger.info(f"掃描請求記錄: 範圍={ip_ranges}, 速率={max_rate}")
        
        return True
    
    async def _execute_scan(self, target: ScanTarget) -> ScanResult:
        """執行掃描"""
        start_time = datetime.now()
        
        # 選擇最佳掃描工具
        scan_tool = self._select_best_tool(target)
        
        if scan_tool == "zmap":
            open_ports = await self._scan_with_zmap(target)
        elif scan_tool == "masscan":
            open_ports = await self._scan_with_masscan(target)
        elif scan_tool == "nmap":
            open_ports = await self._scan_with_nmap(target)
        elif scan_tool == "rustscan":
            open_ports = await self._scan_with_rustscan(target)
        else:
            # 回退到內建掃描器
            open_ports = await self._scan_with_builtin(target)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 計算統計信息
        network = ipaddress.ip_network(target.ip_range, strict=False)
        total_hosts = network.num_addresses
        responsive_hosts = len(set(ip for ip, port in open_ports))
        scan_rate = len(open_ports) / duration if duration > 0 else 0
        
        return ScanResult(
            target=target,
            open_ports=open_ports,
            scan_time=start_time,
            duration=duration,
            total_hosts=total_hosts,
            responsive_hosts=responsive_hosts,
            scan_rate=scan_rate
        )
    
    def _select_best_tool(self, target: ScanTarget) -> str:
        """選擇最佳掃描工具"""
        # 根據目標大小和可用工具選擇
        network = ipaddress.ip_network(target.ip_range, strict=False)
        host_count = network.num_addresses
        
        if host_count > 10000:
            # 大規模掃描優先使用 ZMap
            if self.available_tools["zmap"]:
                return "zmap"
            elif self.available_tools["masscan"]:
                return "masscan"
        
        if host_count > 1000:
            # 中等規模掃描
            if self.available_tools["masscan"]:
                return "masscan"
            elif self.available_tools["rustscan"]:
                return "rustscan"
        
        # 小規模掃描
        if self.available_tools["nmap"]:
            return "nmap"
        elif self.available_tools["rustscan"]:
            return "rustscan"
        
        # 回退到內建掃描器
        return "builtin"
    
    async def _scan_with_zmap(self, target: ScanTarget) -> List[Tuple[str, int]]:
        """使用 ZMap 進行掃描"""
        open_ports = []
        
        for port in target.ports:
            try:
                # 創建臨時輸出文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    output_file = f.name
                
                # 構建 ZMap 命令
                cmd = [
                    "zmap",
                    "-p", str(port),
                    "-r", str(target.max_rate),
                    "-o", output_file,
                    target.ip_range
                ]
                
                # 添加排除範圍
                if target.exclude_ranges:
                    exclude_file = await self._create_exclude_file(target.exclude_ranges)
                    cmd.extend(["-b", exclude_file])
                
                logger.debug(f"執行 ZMap 命令: {' '.join(cmd)}")
                
                # 執行掃描
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    # 讀取結果
                    with open(output_file, 'r') as f:
                        for line in f:
                            ip = line.strip()
                            if ip:
                                open_ports.append((ip, port))
                else:
                    logger.error(f"ZMap 掃描失敗: {stderr.decode()}")
                
                # 清理臨時文件
                Path(output_file).unlink(missing_ok=True)
                
            except Exception as e:
                logger.error(f"ZMap 掃描異常: {e}")
        
        return open_ports
    
    async def _scan_with_masscan(self, target: ScanTarget) -> List[Tuple[str, int]]:
        """使用 Masscan 進行掃描"""
        open_ports = []
        
        try:
            # 創建臨時輸出文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                output_file = f.name
            
            # 構建端口範圍字符串
            port_ranges = ','.join(map(str, target.ports))
            
            # 構建 Masscan 命令
            cmd = [
                "masscan",
                target.ip_range,
                "-p", port_ranges,
                "--rate", str(target.max_rate),
                "-oJ", output_file
            ]
            
            # 添加排除範圍
            if target.exclude_ranges:
                for exclude_range in target.exclude_ranges:
                    cmd.extend(["--exclude", exclude_range])
            
            logger.debug(f"執行 Masscan 命令: {' '.join(cmd)}")
            
            # 執行掃描
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 解析 JSON 結果
                with open(output_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            try:
                                result = json.loads(line)
                                if 'ip' in result and 'ports' in result:
                                    ip = result['ip']
                                    for port_info in result['ports']:
                                        port = port_info['port']
                                        open_ports.append((ip, port))
                            except json.JSONDecodeError:
                                continue
            else:
                logger.error(f"Masscan 掃描失敗: {stderr.decode()}")
            
            # 清理臨時文件
            Path(output_file).unlink(missing_ok=True)
            
        except Exception as e:
            logger.error(f"Masscan 掃描異常: {e}")
        
        return open_ports
    
    async def _scan_with_nmap(self, target: ScanTarget) -> List[Tuple[str, int]]:
        """使用 Nmap 進行掃描"""
        open_ports = []
        
        try:
            # 構建端口範圍字符串
            port_ranges = ','.join(map(str, target.ports))
            
            # 構建 Nmap 命令
            cmd = [
                "nmap",
                "-sS",  # SYN 掃描
                "-Pn",  # 跳過主機發現
                "-n",   # 不進行 DNS 解析
                "-p", port_ranges,
                "--max-rate", str(target.max_rate),
                "-oX", "-",  # XML 輸出到 stdout
                target.ip_range
            ]
            
            logger.debug(f"執行 Nmap 命令: {' '.join(cmd)}")
            
            # 執行掃描
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 解析 XML 結果 (簡化版)
                import xml.etree.ElementTree as ET
                try:
                    root = ET.fromstring(stdout.decode())
                    for host in root.findall('.//host'):
                        ip_elem = host.find('.//address[@addrtype="ipv4"]')
                        if ip_elem is not None:
                            ip = ip_elem.get('addr')
                            for port in host.findall('.//port'):
                                state = port.find('state')
                                if state is not None and state.get('state') == 'open':
                                    port_num = int(port.get('portid'))
                                    open_ports.append((ip, port_num))
                except ET.ParseError as e:
                    logger.error(f"Nmap XML 解析失敗: {e}")
            else:
                logger.error(f"Nmap 掃描失敗: {stderr.decode()}")
            
        except Exception as e:
            logger.error(f"Nmap 掃描異常: {e}")
        
        return open_ports
    
    async def _scan_with_rustscan(self, target: ScanTarget) -> List[Tuple[str, int]]:
        """使用 RustScan 進行掃描"""
        open_ports = []
        
        try:
            # 構建端口範圍字符串
            port_ranges = ','.join(map(str, target.ports))
            
            # 構建 RustScan 命令
            cmd = [
                "rustscan",
                "-a", target.ip_range,
                "-p", port_ranges,
                "--ulimit", "5000",
                "-g"  # 只輸出開放端口
            ]
            
            logger.debug(f"執行 RustScan 命令: {' '.join(cmd)}")
            
            # 執行掃描
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 解析輸出
                for line in stdout.decode().split('\n'):
                    if '->' in line:
                        # 格式: IP -> Port1,Port2,Port3
                        parts = line.split(' -> ')
                        if len(parts) == 2:
                            ip = parts[0].strip()
                            ports_str = parts[1].strip()
                            for port_str in ports_str.split(','):
                                try:
                                    port = int(port_str.strip())
                                    open_ports.append((ip, port))
                                except ValueError:
                                    continue
            else:
                logger.error(f"RustScan 掃描失敗: {stderr.decode()}")
            
        except Exception as e:
            logger.error(f"RustScan 掃描異常: {e}")
        
        return open_ports
    
    async def _scan_with_builtin(self, target: ScanTarget) -> List[Tuple[str, int]]:
        """使用內建掃描器進行掃描"""
        from .scanner import FastPortScanner
        
        scanner = FastPortScanner(
            max_concurrent=min(1000, target.max_rate),
            timeout=target.timeout
        )
        
        return await scanner.scan_ip_range(target.ip_range, target.ports)
    
    async def _create_exclude_file(self, exclude_ranges: List[str]) -> str:
        """創建排除範圍文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for exclude_range in exclude_ranges:
                f.write(f"{exclude_range}\n")
            return f.name
    
    def _convert_to_proxies(self, scan_result: ScanResult) -> List[ProxyNode]:
        """將掃描結果轉換為代理節點"""
        proxies = []
        
        for ip, port in scan_result.open_ports:
            # 根據端口推測協議
            if port in [1080, 1081, 4145, 5678]:
                protocol = ProxyProtocol.SOCKS5
            elif port in [1085]:
                protocol = ProxyProtocol.SOCKS4
            elif port in [443, 8443, 8843]:
                protocol = ProxyProtocol.HTTPS
            else:
                protocol = ProxyProtocol.HTTP
            
            proxy = ProxyNode(
                host=ip,
                port=port,
                protocol=protocol,
                status=ProxyStatus.INACTIVE,
                source="zmap-scan",
                tags=["discovered", "network-scan", f"tool:{scan_result.target.protocol}"],
                metadata={
                    "scan_time": scan_result.scan_time.isoformat(),
                    "scan_duration": scan_result.duration,
                    "scan_rate": scan_result.scan_rate
                }
            )
            
            proxies.append(proxy)
        
        return proxies
    
    def get_scan_statistics(self) -> Dict[str, Any]:
        """獲取掃描統計信息"""
        if not self.scan_history:
            return {"total_scans": 0}
        
        total_scans = len(self.scan_history)
        total_hosts_scanned = sum(result.total_hosts for result in self.scan_history)
        total_responsive_hosts = sum(result.responsive_hosts for result in self.scan_history)
        total_open_ports = sum(len(result.open_ports) for result in self.scan_history)
        total_duration = sum(result.duration for result in self.scan_history)
        
        avg_scan_rate = sum(result.scan_rate for result in self.scan_history) / total_scans
        
        return {
            "total_scans": total_scans,
            "total_hosts_scanned": total_hosts_scanned,
            "total_responsive_hosts": total_responsive_hosts,
            "total_open_ports": total_open_ports,
            "total_duration": total_duration,
            "average_scan_rate": avg_scan_rate,
            "response_rate": (total_responsive_hosts / total_hosts_scanned * 100) if total_hosts_scanned > 0 else 0,
            "available_tools": self.available_tools,
            "last_scan": self.scan_history[-1].scan_time.isoformat() if self.scan_history else None
        }
    
    async def close(self):
        """關閉 ZMap 整合器"""
        # 清理臨時文件
        logger.info("✅ ZMap 整合器已關閉")


class IntelligentTargetDiscovery:
    """智能目標發現系統
    
    使用多種數據源發現潛在的代理目標
    """
    
    def __init__(self, zmap_integration: ZMapIntegration):
        self.zmap = zmap_integration
        self.config = get_config()
        
        # 已知的代理服務提供商 ASN
        self.proxy_provider_asns = [
            "AS13335",  # Cloudflare
            "AS16509",  # Amazon
            "AS15169",  # Google
            "AS8075",   # Microsoft
            "AS20940",  # Akamai
            "AS32934",  # Facebook
        ]
        
        # 高風險國家/地區 (根據需要調整)
        self.high_risk_countries = ["CN", "RU", "KP", "IR"]
    
    async def discover_targets_from_shodan(self, query: str, limit: int = 1000) -> List[str]:
        """從 Shodan 發現目標"""
        if not self.config.api.shodan_api_key:
            logger.warning("未配置 Shodan API 金鑰")
            return []
        
        try:
            import shodan
            api = shodan.Shodan(self.config.api.shodan_api_key)
            
            # 搜索潛在代理
            results = api.search(query, limit=limit)
            
            targets = []
            for result in results['matches']:
                ip = result['ip_str']
                port = result['port']
                
                # 過濾高風險目標
                if self._is_safe_target(result):
                    targets.append(f"{ip}/32")  # 單個 IP
            
            logger.info(f"從 Shodan 發現 {len(targets)} 個目標")
            return targets
            
        except Exception as e:
            logger.error(f"Shodan 目標發現失敗: {e}")
            return []
    
    async def discover_targets_from_censys(self, query: str, limit: int = 1000) -> List[str]:
        """從 Censys 發現目標"""
        if not (self.config.api.censys_api_id and self.config.api.censys_api_secret):
            logger.warning("未配置 Censys API 金鑰")
            return []
        
        try:
            import censys.search
            
            h = censys.search.CensysHosts(
                api_id=self.config.api.censys_api_id,
                api_secret=self.config.api.censys_api_secret
            )
            
            targets = []
            for result in h.search(query, max_records=limit):
                ip = result['ip']
                
                # 過濾高風險目標
                if self._is_safe_target_ip(ip):
                    targets.append(f"{ip}/32")
            
            logger.info(f"從 Censys 發現 {len(targets)} 個目標")
            return targets
            
        except Exception as e:
            logger.error(f"Censys 目標發現失敗: {e}")
            return []
    
    def _is_safe_target(self, shodan_result: Dict[str, Any]) -> bool:
        """檢查 Shodan 結果是否為安全目標"""
        # 檢查國家
        country = shodan_result.get('location', {}).get('country_code')
        if country in self.high_risk_countries:
            return False
        
        # 檢查組織
        org = shodan_result.get('org', '').lower()
        if any(keyword in org for keyword in ['government', 'military', 'defense', 'police']):
            return False
        
        # 檢查 ISP
        isp = shodan_result.get('isp', '').lower()
        if any(keyword in isp for keyword in ['government', 'military', 'defense']):
            return False
        
        return True
    
    def _is_safe_target_ip(self, ip: str) -> bool:
        """檢查 IP 是否為安全目標"""
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            # 排除私有和保留地址
            if ip_obj.is_private or ip_obj.is_reserved or ip_obj.is_multicast:
                return False
            
            return True
            
        except ValueError:
            return False
    
    async def generate_smart_targets(self, 
                                   base_ranges: List[str],
                                   intelligence_sources: List[str] = None) -> List[str]:
        """生成智能掃描目標
        
        Args:
            base_ranges: 基礎 IP 範圍
            intelligence_sources: 情報來源 ['shodan', 'censys']
            
        Returns:
            優化後的目標列表
        """
        if intelligence_sources is None:
            intelligence_sources = ['shodan', 'censys']
        
        all_targets = list(base_ranges)
        
        # 從 Shodan 獲取目標
        if 'shodan' in intelligence_sources:
            shodan_targets = await self.discover_targets_from_shodan(
                "port:3128 OR port:8080 OR port:1080"
            )
            all_targets.extend(shodan_targets)
        
        # 從 Censys 獲取目標
        if 'censys' in intelligence_sources:
            censys_targets = await self.discover_targets_from_censys(
                "services.port:3128 OR services.port:8080 OR services.port:1080"
            )
            all_targets.extend(censys_targets)
        
        # 去重和優化
        unique_targets = list(set(all_targets))
        
        logger.info(f"生成 {len(unique_targets)} 個智能目標")
        return unique_targets