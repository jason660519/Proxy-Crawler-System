"""代理掃描與驗證模組

實施高級代理掃描技術：
- 高速端口掃描（ZMap/Masscan 風格）
- 多層代理驗證
- 匿名度檢測
- 地理位置驗證
- 性能基準測試
"""

import asyncio
import aiohttp
import socket
import struct
import time
import random
from typing import List, Optional, Dict, Any, Tuple, Set
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
import ipaddress
from urllib.parse import urlparse
import json

from .models import ProxyNode, ProxyProtocol, ProxyAnonymity, ProxyStatus, ProxySpeed
from .intelligent_detection import IntelligentProxyDetector, DetectionResult, BenchmarkResult
from .geolocation_enhanced import EnhancedGeolocationDetector, GeolocationInfo
from .quality_assessment import ProxyQualityAssessor, QualityMetrics, QualityGrade
from .zmap_integration import ZMapIntegration, IntelligentTargetDiscovery

logger = logging.getLogger(__name__)


class ProxyScanner:
    """高級代理掃描器
    
    提供多種掃描和驗證方法
    """
    
    def __init__(self, max_concurrent: int = 100, timeout: float = 10.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.executor = ThreadPoolExecutor(max_workers=50)
        
        # 測試 URL 配置
        self.test_urls = [
            "http://httpbin.org/ip",
            "https://api.ipify.org?format=json",
            "http://icanhazip.com",
            "https://checkip.amazonaws.com",
            "http://ip-api.com/json"
        ]
        
        # 匿名度檢測 URL
        self.anonymity_test_urls = [
            "http://httpbin.org/headers",
            "https://httpbin.org/headers"
        ]
        
        # 統計信息
        self.scan_stats = {
            "total_scanned": 0,
            "successful_connections": 0,
            "failed_connections": 0,
            "timeout_errors": 0,
            "connection_errors": 0
        }
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建 HTTP 會話"""
        if not self.session:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=self.timeout / 2,
                sock_read=self.timeout / 2
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
        
        return self.session
    
    async def scan_proxy_batch(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """批量掃描代理"""
        logger.info(f"🔍 開始掃描 {len(proxies)} 個代理...")
        
        # 創建掃描任務
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = [self._scan_single_proxy(proxy, semaphore) for proxy in proxies]
        
        # 執行掃描
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        scanned_proxies = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.debug(f"代理掃描異常 {proxies[i].host}:{proxies[i].port}: {result}")
                proxies[i].status = ProxyStatus.FAILED
                self.scan_stats["failed_connections"] += 1
            else:
                scanned_proxies.append(result)
        
        # 統計
        active_count = len([p for p in scanned_proxies if p.status == ProxyStatus.ACTIVE])
        logger.info(f"✅ 掃描完成：{active_count}/{len(proxies)} 個代理可用")
        
        return scanned_proxies
    
    async def _scan_single_proxy(self, proxy: ProxyNode, semaphore: asyncio.Semaphore) -> ProxyNode:
        """掃描單個代理"""
        async with semaphore:
            self.scan_stats["total_scanned"] += 1
            
            # 1. 基本連接測試
            if not await self._test_basic_connection(proxy):
                proxy.status = ProxyStatus.FAILED
                return proxy
            
            # 2. HTTP 功能測試
            if not await self._test_http_functionality(proxy):
                proxy.status = ProxyStatus.FAILED
                return proxy
            
            # 3. 匿名度檢測
            anonymity = await self._detect_anonymity(proxy)
            proxy.anonymity = anonymity
            
            # 4. 速度測試
            speed = await self._measure_speed(proxy)
            proxy.speed = speed
            
            # 5. 地理位置檢測
            await self._detect_geolocation(proxy)
            
            # 更新狀態
            proxy.status = ProxyStatus.ACTIVE
            proxy.last_checked = datetime.now()
            self.scan_stats["successful_connections"] += 1
            
            return proxy
    
    async def _test_basic_connection(self, proxy: ProxyNode) -> bool:
        """基本連接測試"""
        try:
            # TCP 連接測試
            if proxy.protocol in [ProxyProtocol.SOCKS4, ProxyProtocol.SOCKS5]:
                return await self._test_socks_connection(proxy)
            else:
                return await self._test_http_connection(proxy)
        
        except Exception as e:
            logger.debug(f"基本連接測試失敗 {proxy.host}:{proxy.port}: {e}")
            self.scan_stats["connection_errors"] += 1
            return False
    
    async def _test_socks_connection(self, proxy: ProxyNode) -> bool:
        """SOCKS 代理連接測試"""
        try:
            # 使用 asyncio 進行 SOCKS 握手測試
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(proxy.host, proxy.port),
                timeout=self.timeout / 2
            )
            
            if proxy.protocol == ProxyProtocol.SOCKS4:
                # SOCKS4 握手
                request = struct.pack(">BBH4s", 4, 1, 80, socket.inet_aton("8.8.8.8")) + b"\x00"
            else:
                # SOCKS5 握手
                request = b"\x05\x01\x00"  # 版本5，1個方法，無認證
            
            writer.write(request)
            await writer.drain()
            
            response = await asyncio.wait_for(reader.read(1024), timeout=2)
            writer.close()
            await writer.wait_closed()
            
            return len(response) > 0
        
        except Exception as e:
            logger.debug(f"SOCKS 連接測試失敗 {proxy.host}:{proxy.port}: {e}")
            return False
    
    async def _test_http_connection(self, proxy: ProxyNode) -> bool:
        """HTTP 代理連接測試"""
        try:
            session = await self._get_session()
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            
            async with session.get(
                "http://httpbin.org/ip",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout / 2)
            ) as response:
                return response.status == 200
        
        except asyncio.TimeoutError:
            self.scan_stats["timeout_errors"] += 1
            return False
        except Exception as e:
            logger.debug(f"HTTP 連接測試失敗 {proxy.host}:{proxy.port}: {e}")
            return False
    
    async def _test_http_functionality(self, proxy: ProxyNode) -> bool:
        """HTTP 功能完整性測試"""
        try:
            session = await self._get_session()
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            
            # 測試多個 URL
            for test_url in self.test_urls[:2]:  # 只測試前兩個以節省時間
                try:
                    async with session.get(
                        test_url,
                        proxy=proxy_url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            return True
                except:
                    continue
            
            return False
        
        except Exception as e:
            logger.debug(f"HTTP 功能測試失敗 {proxy.host}:{proxy.port}: {e}")
            return False
    
    async def _detect_anonymity(self, proxy: ProxyNode) -> ProxyAnonymity:
        """檢測代理匿名度"""
        try:
            session = await self._get_session()
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            
            # 獲取原始 IP（不使用代理）
            try:
                async with session.get("http://httpbin.org/ip", timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        original_data = await response.json()
                        original_ip = original_data.get("origin", "").split(",")[0].strip()
                    else:
                        original_ip = None
            except:
                original_ip = None
            
            # 通過代理獲取 headers
            async with session.get(
                "http://httpbin.org/headers",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    return ProxyAnonymity.UNKNOWN
                
                data = await response.json()
                headers = data.get("headers", {})
                
                # 檢查是否洩露原始 IP
                forwarded_headers = [
                    "X-Forwarded-For", "X-Real-Ip", "X-Originating-Ip",
                    "Client-Ip", "Via", "Forwarded"
                ]
                
                has_forwarded = any(header in headers for header in forwarded_headers)
                
                # 檢查 User-Agent 是否被修改
                user_agent = headers.get("User-Agent", "")
                is_ua_modified = "proxy" in user_agent.lower() or "squid" in user_agent.lower()
                
                # 判斷匿名度
                if has_forwarded or is_ua_modified:
                    if original_ip and any(original_ip in str(headers.get(h, "")) for h in forwarded_headers):
                        return ProxyAnonymity.TRANSPARENT
                    else:
                        return ProxyAnonymity.ANONYMOUS
                else:
                    return ProxyAnonymity.ELITE
        
        except Exception as e:
            logger.debug(f"匿名度檢測失敗 {proxy.host}:{proxy.port}: {e}")
            return ProxyAnonymity.UNKNOWN
    
    async def _measure_speed(self, proxy: ProxyNode) -> ProxySpeed:
        """測量代理速度"""
        try:
            session = await self._get_session()
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            
            # 測試小文件下載速度
            start_time = time.time()
            
            async with session.get(
                "http://httpbin.org/bytes/1024",  # 下載 1KB 數據
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    await response.read()
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    
                    # 根據響應時間分類速度
                    if response_time < 1.0:
                        return ProxySpeed.FAST
                    elif response_time < 3.0:
                        return ProxySpeed.MEDIUM
                    else:
                        return ProxySpeed.SLOW
                else:
                    return ProxySpeed.UNKNOWN
        
        except Exception as e:
            logger.debug(f"速度測試失敗 {proxy.host}:{proxy.port}: {e}")
            return ProxySpeed.UNKNOWN
    
    async def _detect_geolocation(self, proxy: ProxyNode):
        """檢測代理地理位置"""
        try:
            session = await self._get_session()
            proxy_url = f"http://{proxy.host}:{proxy.port}"
            
            # 使用 ip-api.com 獲取地理位置信息
            async with session.get(
                "http://ip-api.com/json",
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("status") == "success":
                        proxy.country = data.get("country")
                        proxy.region = data.get("regionName")
                        proxy.city = data.get("city")
                        proxy.isp = data.get("isp")
                        
                        # 更新元數據
                        if not proxy.metadata:
                            proxy.metadata = {}
                        
                        proxy.metadata.update({
                            "geolocation": {
                                "lat": data.get("lat"),
                                "lon": data.get("lon"),
                                "timezone": data.get("timezone"),
                                "as": data.get("as"),
                                "query": data.get("query")  # 實際 IP
                            }
                        })
        
        except Exception as e:
            logger.debug(f"地理位置檢測失敗 {proxy.host}:{proxy.port}: {e}")
    
    def get_scan_stats(self) -> Dict[str, Any]:
        """獲取掃描統計信息"""
        total = self.scan_stats["total_scanned"]
        if total == 0:
            return self.scan_stats
        
        return {
            **self.scan_stats,
            "success_rate": (self.scan_stats["successful_connections"] / total) * 100,
            "failure_rate": (self.scan_stats["failed_connections"] / total) * 100,
            "timeout_rate": (self.scan_stats["timeout_errors"] / total) * 100
        }
    
    async def close(self):
        """關閉掃描器"""
        if self.session:
            await self.session.close()
            self.session = None
        
        self.executor.shutdown(wait=True)
        logger.info("✅ 代理掃描器已關閉")


class FastPortScanner:
    """高速端口掃描器
    
    模擬 ZMap/Masscan 的高速掃描技術
    """
    
    def __init__(self, max_concurrent: int = 1000, timeout: float = 3.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.common_proxy_ports = [
            80, 8080, 3128, 8000, 8888, 9999, 8118, 8123, 8181,
            1080, 1081, 1085, 4145, 5678,  # SOCKS
            443, 8443, 8843,  # HTTPS
            3129, 8081, 8082, 8083, 8084, 8085, 8086, 8087, 8089,
            9000, 9001, 9002, 9003, 9080, 9090, 9091, 9092, 9093
        ]
    
    async def scan_ip_range(self, ip_range: str, ports: Optional[List[int]] = None) -> List[Tuple[str, int]]:
        """掃描 IP 範圍的開放端口"""
        if ports is None:
            ports = self.common_proxy_ports
        
        # 解析 IP 範圍
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
            ips = [str(ip) for ip in network.hosts()]
        except ValueError:
            # 單個 IP
            ips = [ip_range]
        
        logger.info(f"🔍 開始掃描 {len(ips)} 個 IP 的 {len(ports)} 個端口...")
        
        # 創建掃描任務
        semaphore = asyncio.Semaphore(self.max_concurrent)
        tasks = []
        
        for ip in ips:
            for port in ports:
                tasks.append(self._scan_port(ip, port, semaphore))
        
        # 執行掃描
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 收集開放的端口
        open_ports = []
        for result in results:
            if isinstance(result, tuple) and result[2]:  # (ip, port, is_open)
                open_ports.append((result[0], result[1]))
        
        logger.info(f"✅ 發現 {len(open_ports)} 個開放端口")
        return open_ports
    
    async def _scan_port(self, ip: str, port: int, semaphore: asyncio.Semaphore) -> Tuple[str, int, bool]:
        """掃描單個端口"""
        async with semaphore:
            try:
                # TCP 連接測試
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port),
                    timeout=self.timeout
                )
                
                writer.close()
                await writer.wait_closed()
                
                return (ip, port, True)
            
            except Exception:
                return (ip, port, False)
    
    async def discover_proxies_in_range(self, ip_range: str) -> List[ProxyNode]:
        """在 IP 範圍內發現潛在代理"""
        open_ports = await self.scan_ip_range(ip_range)
        
        proxies = []
        for ip, port in open_ports:
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
                source="fast-scanner",
                tags=["discovered", "port-scan"]
            )
            
            proxies.append(proxy)
        
        logger.info(f"🎯 在範圍 {ip_range} 發現 {len(proxies)} 個潛在代理")
        return proxies


class ProxyValidator:
    """代理驗證器
    
    提供全面的代理驗證功能
    """
    
    def __init__(self, scanner: ProxyScanner):
        self.scanner = scanner
        self.validation_rules = {
            "min_speed": ProxySpeed.SLOW,
            "required_anonymity": ProxyAnonymity.TRANSPARENT,
            "max_response_time": 10.0,
            "required_countries": None,  # None = 所有國家
            "blocked_countries": ["CN", "RU"],  # 示例：阻止某些國家
            "required_protocols": None  # None = 所有協議
        }
    
    def set_validation_rules(self, rules: Dict[str, Any]):
        """設置驗證規則"""
        self.validation_rules.update(rules)
    
    async def validate_proxies(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """驗證代理列表"""
        logger.info(f"🔍 開始驗證 {len(proxies)} 個代理...")
        
        # 首先進行掃描
        scanned_proxies = await self.scanner.scan_proxy_batch(proxies)
        
        # 然後應用驗證規則
        validated_proxies = []
        for proxy in scanned_proxies:
            if self._meets_validation_criteria(proxy):
                validated_proxies.append(proxy)
        
        logger.info(f"✅ {len(validated_proxies)}/{len(proxies)} 個代理通過驗證")
        return validated_proxies
    
    def _meets_validation_criteria(self, proxy: ProxyNode) -> bool:
        """檢查代理是否符合驗證標準"""
        # 必須是活躍狀態
        if proxy.status != ProxyStatus.ACTIVE:
            return False
        
        # 速度檢查
        if proxy.speed and proxy.speed.value < self.validation_rules["min_speed"].value:
            return False
        
        # 匿名度檢查
        if proxy.anonymity and proxy.anonymity.value < self.validation_rules["required_anonymity"].value:
            return False
        
        # 國家檢查
        if self.validation_rules["required_countries"]:
            if proxy.country not in self.validation_rules["required_countries"]:
                return False
        
        if self.validation_rules["blocked_countries"]:
            if proxy.country in self.validation_rules["blocked_countries"]:
                return False
        
        # 協議檢查
        if self.validation_rules["required_protocols"]:
            if proxy.protocol not in self.validation_rules["required_protocols"]:
                return False
        
        return True
    
    def get_validation_report(self, original_proxies: List[ProxyNode], validated_proxies: List[ProxyNode]) -> Dict[str, Any]:
        """生成驗證報告"""
        total_original = len(original_proxies)
        total_validated = len(validated_proxies)
        
        # 按狀態統計
        status_counts = {}
        for proxy in original_proxies:
            status = proxy.status.name
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # 按協議統計
        protocol_counts = {}
        for proxy in validated_proxies:
            protocol = proxy.protocol.name
            protocol_counts[protocol] = protocol_counts.get(protocol, 0) + 1
        
        # 按國家統計
        country_counts = {}
        for proxy in validated_proxies:
            country = proxy.country or "Unknown"
            country_counts[country] = country_counts.get(country, 0) + 1
        
        return {
            "total_original": total_original,
            "total_validated": total_validated,
            "validation_rate": (total_validated / total_original * 100) if total_original > 0 else 0,
            "status_distribution": status_counts,
            "protocol_distribution": protocol_counts,
            "country_distribution": country_counts,
            "validation_rules": self.validation_rules,
            "scanner_stats": self.scanner.get_scan_stats()
        }


class EnhancedProxyScanner:
    """增強代理掃描器
    
    整合所有第二階段功能：
    - ZMap 整合
    - 智能代理探測
    - 地理位置增強檢測
    - 質量評估
    """
    
    def __init__(self, max_concurrent: int = 100, timeout: float = 10.0):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        
        # 初始化各個組件
        self.basic_scanner = ProxyScanner(max_concurrent, timeout)
        self.port_scanner = FastPortScanner(max_concurrent, timeout)
        self.intelligent_detector = IntelligentProxyDetector()
        self.geolocation_detector = EnhancedGeolocationDetector()
        self.quality_assessor = ProxyQualityAssessor()
        self.zmap_integration = ZMapIntegration()
        self.target_discovery = IntelligentTargetDiscovery(self.zmap_integration)
        
        # 統計信息
        self.enhanced_stats = {
            "total_discovered": 0,
            "total_analyzed": 0,
            "high_quality_count": 0,
            "geographic_coverage": {},
            "anonymity_distribution": {},
            "performance_metrics": {}
        }
    
    async def comprehensive_scan(self, 
                               targets: Optional[List[str]] = None,
                               ip_ranges: Optional[List[str]] = None,
                               existing_proxies: Optional[List[ProxyNode]] = None,
                               enable_zmap: bool = False,
                               enable_intelligence: bool = True,
                               enable_quality_assessment: bool = True) -> Dict[str, Any]:
        """全面掃描
        
        Args:
            targets: 目標主機列表
            ip_ranges: IP 範圍列表
            existing_proxies: 現有代理列表
            enable_zmap: 是否啟用 ZMap 掃描
            enable_intelligence: 是否啟用智能檢測
            enable_quality_assessment: 是否啟用質量評估
            
        Returns:
            掃描結果字典
        """
        logger.info("🚀 開始增強代理掃描...")
        
        all_proxies = []
        scan_results = {
            "discovered_proxies": [],
            "analyzed_proxies": [],
            "quality_metrics": [],
            "geographic_info": [],
            "detection_results": [],
            "benchmark_results": [],
            "statistics": {}
        }
        
        try:
            # 1. 目標發現階段
            if targets or ip_ranges:
                discovered_proxies = await self._discover_targets(targets, ip_ranges, enable_zmap)
                all_proxies.extend(discovered_proxies)
                scan_results["discovered_proxies"] = discovered_proxies
                self.enhanced_stats["total_discovered"] += len(discovered_proxies)
            
            # 2. 添加現有代理
            if existing_proxies:
                all_proxies.extend(existing_proxies)
            
            if not all_proxies:
                logger.warning("⚠️ 沒有找到任何代理進行掃描")
                return scan_results
            
            # 3. 基礎掃描
            logger.info(f"🔍 開始基礎掃描 {len(all_proxies)} 個代理...")
            scanned_proxies = await self.basic_scanner.scan_proxy_batch(all_proxies)
            active_proxies = [p for p in scanned_proxies if p.status == ProxyStatus.ACTIVE]
            
            logger.info(f"✅ 基礎掃描完成：{len(active_proxies)} 個活躍代理")
            
            if not active_proxies:
                logger.warning("⚠️ 沒有發現活躍的代理")
                scan_results["analyzed_proxies"] = scanned_proxies
                return scan_results
            
            # 4. 智能檢測階段
            if enable_intelligence:
                logger.info("🧠 開始智能檢測階段...")
                detection_results, benchmark_results = await self._intelligent_analysis(active_proxies)
                scan_results["detection_results"] = detection_results
                scan_results["benchmark_results"] = benchmark_results
            else:
                detection_results = [None] * len(active_proxies)
                benchmark_results = [None] * len(active_proxies)
            
            # 5. 地理位置增強檢測
            logger.info("🌍 開始地理位置增強檢測...")
            geographic_info = await self._enhanced_geolocation_analysis(active_proxies)
            scan_results["geographic_info"] = geographic_info
            
            # 6. 質量評估階段
            if enable_quality_assessment:
                logger.info("📊 開始質量評估階段...")
                quality_metrics = await self._quality_assessment_analysis(
                    active_proxies, detection_results, benchmark_results
                )
                scan_results["quality_metrics"] = quality_metrics
                
                # 統計高質量代理
                high_quality_count = len([
                    m for m in quality_metrics 
                    if m.quality_grade in [QualityGrade.EXCELLENT, QualityGrade.GOOD]
                ])
                self.enhanced_stats["high_quality_count"] = high_quality_count
            
            # 7. 更新統計信息
            self.enhanced_stats["total_analyzed"] = len(active_proxies)
            self._update_enhanced_statistics(active_proxies, scan_results)
            
            scan_results["analyzed_proxies"] = active_proxies
            scan_results["statistics"] = self.get_enhanced_statistics()
            
            logger.info(f"🎉 增強掃描完成！分析了 {len(active_proxies)} 個代理")
            
        except Exception as e:
            logger.error(f"❌ 增強掃描過程中發生錯誤: {e}")
            scan_results["error"] = str(e)
        
        return scan_results
    
    async def _discover_targets(self, 
                              targets: Optional[List[str]], 
                              ip_ranges: Optional[List[str]], 
                              enable_zmap: bool) -> List[ProxyNode]:
        """目標發現"""
        discovered_proxies = []
        
        # 智能目標發現
        if targets:
            logger.info(f"🎯 使用智能目標發現分析 {len(targets)} 個目標...")
            intelligent_targets = await self.target_discovery.generate_smart_targets(
                targets, intelligence_sources=['shodan', 'censys']
            )
            # 將目標字符串轉換為代理節點（這裡需要進一步掃描）
            for target in intelligent_targets:
                # 這裡應該調用掃描方法來發現實際的代理
                pass
        
        # IP 範圍掃描
        if ip_ranges:
            for ip_range in ip_ranges:
                logger.info(f"🔍 掃描 IP 範圍: {ip_range}")
                
                if enable_zmap:
                    # 使用 ZMap 進行高速掃描
                    zmap_results = await self.zmap_integration.scan_range(
                        ip_range, ports=[80, 8080, 3128, 1080]
                    )
                    discovered_proxies.extend(zmap_results)
                else:
                    # 使用內建快速掃描器
                    range_proxies = await self.port_scanner.discover_proxies_in_range(ip_range)
                    discovered_proxies.extend(range_proxies)
        
        return discovered_proxies
    
    async def _intelligent_analysis(self, proxies: List[ProxyNode]) -> Tuple[List[DetectionResult], List[BenchmarkResult]]:
        """智能分析"""
        detection_results = []
        benchmark_results = []
        
        # 批量智能檢測
        semaphore = asyncio.Semaphore(self.max_concurrent // 2)  # 減少並發以避免過載
        
        async def analyze_proxy(proxy: ProxyNode) -> Tuple[Optional[DetectionResult], Optional[BenchmarkResult]]:
            async with semaphore:
                try:
                    # 智能檢測
                    detection_result = await self.intelligent_detector.detect_proxy(proxy, comprehensive=True)
                    
                    # 性能基準測試（僅對高質量代理進行）
                    benchmark_result = None
                    if detection_result and detection_result.is_working and detection_result.success_rate > 0.7:
                        benchmark_result = await self.intelligent_detector.benchmark_proxy(proxy)
                    
                    return detection_result, benchmark_result
                    
                except Exception as e:
                    logger.debug(f"智能分析失敗 {proxy.host}:{proxy.port}: {e}")
                    return None, None
        
        # 執行分析
        tasks = [analyze_proxy(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, tuple):
                detection_result, benchmark_result = result
                detection_results.append(detection_result)
                benchmark_results.append(benchmark_result)
            else:
                detection_results.append(None)
                benchmark_results.append(None)
        
        return detection_results, benchmark_results
    
    async def _enhanced_geolocation_analysis(self, proxies: List[ProxyNode]) -> List[GeolocationInfo]:
        """增強地理位置分析"""
        geographic_info = []
        
        # 批量地理位置檢測
        proxy_ips = [proxy.host for proxy in proxies]
        geo_results = await self.geolocation_detector.batch_detect_locations(proxy_ips)
        
        for proxy in proxies:
            if proxy.host in geo_results:
                geo_info = geo_results[proxy.host]
                
                # 更新代理的地理信息
                proxy.country = geo_info.country_code
                proxy.region = geo_info.region
                proxy.city = geo_info.city
                proxy.isp = geo_info.isp
                
                # 更新元數據
                if not proxy.metadata:
                    proxy.metadata = {}
                
                proxy.metadata["enhanced_geolocation"] = {
                    "latitude": geo_info.latitude,
                    "longitude": geo_info.longitude,
                    "timezone": geo_info.timezone,
                    "asn": geo_info.asn,
                    "organization": geo_info.organization,
                    "accuracy_radius": geo_info.accuracy_radius,
                    "is_vpn": geo_info.is_vpn,
                    "is_tor": geo_info.is_tor,
                    "threat_level": geo_info.threat_level
                }
                
                geographic_info.append(geo_info)
            else:
                geographic_info.append(None)
        
        return geographic_info
    
    async def _quality_assessment_analysis(self, 
                                         proxies: List[ProxyNode],
                                         detection_results: List[Optional[DetectionResult]],
                                         benchmark_results: List[Optional[BenchmarkResult]]) -> List[QualityMetrics]:
        """質量評估分析"""
        # 準備評估數據
        assessment_data = []
        for i, proxy in enumerate(proxies):
            detection_result = detection_results[i] if i < len(detection_results) else None
            benchmark_result = benchmark_results[i] if i < len(benchmark_results) else None
            assessment_data.append((proxy, detection_result, benchmark_result))
        
        # 批量質量評估
        quality_metrics = self.quality_assessor.batch_assess_quality(assessment_data)
        
        return quality_metrics
    
    def _update_enhanced_statistics(self, proxies: List[ProxyNode], scan_results: Dict[str, Any]):
        """更新增強統計信息"""
        # 地理覆蓋統計
        country_counts = {}
        for proxy in proxies:
            country = proxy.country or "Unknown"
            country_counts[country] = country_counts.get(country, 0) + 1
        self.enhanced_stats["geographic_coverage"] = country_counts
        
        # 匿名性分佈統計
        anonymity_counts = {}
        for proxy in proxies:
            anonymity = proxy.anonymity.name if proxy.anonymity else "Unknown"
            anonymity_counts[anonymity] = anonymity_counts.get(anonymity, 0) + 1
        self.enhanced_stats["anonymity_distribution"] = anonymity_counts
        
        # 性能指標統計
        if "benchmark_results" in scan_results:
            benchmark_results = [r for r in scan_results["benchmark_results"] if r is not None]
            if benchmark_results:
                avg_latency = sum(r.latency for r in benchmark_results) / len(benchmark_results)
                avg_download_speed = sum(r.download_speed for r in benchmark_results) / len(benchmark_results)
                
                self.enhanced_stats["performance_metrics"] = {
                    "average_latency": avg_latency,
                    "average_download_speed": avg_download_speed,
                    "total_benchmarked": len(benchmark_results)
                }
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """獲取增強統計信息"""
        stats = self.enhanced_stats.copy()
        
        # 添加基礎掃描器統計
        stats["basic_scanner_stats"] = self.basic_scanner.get_scan_stats()
        
        # 添加質量評估統計
        stats["quality_assessment_stats"] = self.quality_assessor.get_assessment_statistics()
        
        # 計算成功率
        if stats["total_discovered"] > 0:
            stats["discovery_to_analysis_rate"] = (stats["total_analyzed"] / stats["total_discovered"]) * 100
        
        if stats["total_analyzed"] > 0:
            stats["high_quality_rate"] = (stats["high_quality_count"] / stats["total_analyzed"]) * 100
        
        return stats
    
    async def export_comprehensive_report(self, scan_results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """導出綜合報告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_proxy_scan_report_{timestamp}.json"
        
        # 準備報告數據
        report_data = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "scanner_version": "2.0-enhanced",
                "scan_type": "comprehensive"
            },
            "scan_summary": {
                "total_discovered": len(scan_results.get("discovered_proxies", [])),
                "total_analyzed": len(scan_results.get("analyzed_proxies", [])),
                "total_quality_assessed": len(scan_results.get("quality_metrics", [])),
                "geographic_locations": len(set(
                    p.country for p in scan_results.get("analyzed_proxies", []) 
                    if p.country
                ))
            },
            "detailed_results": scan_results,
            "statistics": self.get_enhanced_statistics()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"📄 綜合報告已導出: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ 導出綜合報告失敗: {e}")
            raise
    
    async def close(self):
        """關閉增強掃描器"""
        await self.basic_scanner.close()
        await self.intelligent_detector.close()
        await self.geolocation_detector.close()
        
        logger.info("✅ 增強代理掃描器已關閉")