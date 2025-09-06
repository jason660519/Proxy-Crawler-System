"""Geonode.com 代理爬蟲模組

此模組實現了從 geonode.com 網站抓取免費代理的功能。
Geonode 提供高質量的代理列表，支援多種協議和地理位置篩選。

特點：
- 支援分頁瀏覽
- 提供詳細的地理位置信息
- 包含代理速度和穩定性指標
- 支援多種協議類型
"""

import asyncio
import json
import re
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs

from loguru import logger

from .base_crawler import BaseCrawler, ProxyNode


class GeonodeCrawler(BaseCrawler):
    """Geonode.com 代理爬蟲
    
    從 geonode.com 抓取免費代理列表，支援分頁和多種篩選條件
    """
    
    def __init__(self, max_pages: int = 5):
        """初始化 Geonode 爬蟲
        
        Args:
            max_pages: 最大抓取頁數
        """
        super().__init__(
            source_name="Geonode.com",
            base_url="https://geonode.com",
            delay_range=(1.5, 3.0),
            timeout=30,
            max_retries=3
        )
        
        self.max_pages = max_pages
        
        # 定義要抓取的代理類型和對應的 URL 路徑
        self.proxy_endpoints = {
            'free-proxy-list': '/free-proxy-list',
            'premium-proxy-list': '/premium-proxy-list',  # 可能需要註冊
        }
        
        # 支援的協議類型映射
        self.protocol_mapping = {
            'http': 'HTTP',
            'https': 'HTTPS', 
            'socks4': 'SOCKS4',
            'socks5': 'SOCKS5'
        }
    
    async def fetch_proxies(self) -> List[ProxyNode]:
        """抓取所有可用的代理
        
        Returns:
            所有抓取到的代理節點列表
        """
        all_proxies = []
        
        # 主要從免費代理列表抓取
        free_proxy_url = urljoin(self.base_url, self.proxy_endpoints['free-proxy-list'])
        
        logger.info(f"[{self.source_name}] 開始抓取免費代理列表")
        
        # 抓取多頁數據
        for page in range(1, self.max_pages + 1):
            try:
                # 構建分頁 URL
                page_url = f"{free_proxy_url}?page={page}"
                
                logger.info(f"[{self.source_name}] 抓取第 {page} 頁")
                
                # 發送請求
                html_content = await self.make_request(page_url)
                if html_content:
                    # 解析代理
                    proxies = self.parse_proxy_page(html_content)
                    if proxies:
                        all_proxies.extend(proxies)
                        logger.info(f"[{self.source_name}] 第 {page} 頁找到 {len(proxies)} 個代理")
                    else:
                        logger.info(f"[{self.source_name}] 第 {page} 頁沒有找到代理，可能已到最後一頁")
                        break
                else:
                    logger.warning(f"[{self.source_name}] 無法獲取第 {page} 頁內容")
                    break
                
                # 遵守速率限制
                await self.respect_rate_limit()
                
            except Exception as e:
                logger.error(f"[{self.source_name}] 抓取第 {page} 頁時發生錯誤: {str(e)}")
                break
        
        # 嘗試從 API 端點獲取額外數據
        api_proxies = await self._fetch_from_api()
        if api_proxies:
            all_proxies.extend(api_proxies)
            logger.info(f"[{self.source_name}] API 獲取到 {len(api_proxies)} 個額外代理")
        
        # 去重處理
        unique_proxies = self._remove_duplicates(all_proxies)
        logger.info(f"[{self.source_name}] 去重後共有 {len(unique_proxies)} 個唯一代理")
        
        return unique_proxies
    
    def parse_proxy_page(self, html_content: str) -> List[ProxyNode]:
        """解析代理頁面
        
        Args:
            html_content: HTML 內容
            
        Returns:
            解析出的代理節點列表
        """
        soup = self.parse_html(html_content)
        proxies = []
        
        try:
            # 方法1: 查找標準表格
            proxies_from_table = self._parse_table_format(soup)
            if proxies_from_table:
                proxies.extend(proxies_from_table)
            
            # 方法2: 查找 JSON 數據
            proxies_from_json = self._parse_json_data(html_content)
            if proxies_from_json:
                proxies.extend(proxies_from_json)
            
            # 方法3: 查找卡片格式
            proxies_from_cards = self._parse_card_format(soup)
            if proxies_from_cards:
                proxies.extend(proxies_from_cards)
            
            logger.debug(f"[{self.source_name}] 解析出 {len(proxies)} 個代理")
            
        except Exception as e:
            logger.error(f"[{self.source_name}] 解析頁面時發生錯誤: {str(e)}")
        
        return proxies
    
    def _parse_table_format(self, soup) -> List[ProxyNode]:
        """解析表格格式的代理數據"""
        proxies = []
        
        # 查找代理表格
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                rows = table.find_all('tr')
                
                # 跳過標題行
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 4:  # 至少需要 IP, Port, Country, Protocol
                        proxy = self._parse_table_row(cells)
                        if proxy:
                            proxies.append(proxy)
            except Exception as e:
                logger.debug(f"[{self.source_name}] 解析表格時出錯: {str(e)}")
                continue
        
        return proxies
    
    def _parse_table_row(self, cells) -> Optional[ProxyNode]:
        """解析表格行數據"""
        try:
            # 提取基本信息 (根據 Geonode 的表格結構調整)
            ip = cells[0].get_text(strip=True)
            port_text = cells[1].get_text(strip=True)
            
            # 驗證和轉換端口
            try:
                port = int(port_text)
            except ValueError:
                return None
            
            # 提取國家信息
            country = "Unknown"
            if len(cells) > 2:
                country = cells[2].get_text(strip=True)
            
            # 提取協議信息
            protocol = "HTTP"
            if len(cells) > 3:
                protocol_text = cells[3].get_text(strip=True).lower()
                protocol = self.protocol_mapping.get(protocol_text, 'HTTP')
            
            # 提取匿名等級
            anonymity = "Unknown"
            if len(cells) > 4:
                anonymity = cells[4].get_text(strip=True)
            
            # 提取響應時間
            response_time = None
            if len(cells) > 5:
                time_text = cells[5].get_text(strip=True)
                # 嘗試提取數字
                time_match = re.search(r'(\d+(?:\.\d+)?)', time_text)
                if time_match:
                    try:
                        response_time = float(time_match.group(1))
                    except ValueError:
                        pass
            
            return ProxyNode(
                ip=ip,
                port=port,
                protocol=protocol,
                anonymity=anonymity,
                country=country,
                response_time=response_time,
                source=self.source_name
            )
            
        except Exception as e:
            logger.debug(f"[{self.source_name}] 解析行數據時出錯: {str(e)}")
            return None
    
    def _parse_json_data(self, html_content: str) -> List[ProxyNode]:
        """從 HTML 中提取 JSON 格式的代理數據"""
        proxies = []
        
        try:
            # 查找 JavaScript 中的 JSON 數據
            json_patterns = [
                r'var\s+proxies\s*=\s*(\[.*?\]);',
                r'"proxies"\s*:\s*(\[.*?\])',
                r'proxyList\s*=\s*(\[.*?\]);',
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        data = json.loads(match)
                        if isinstance(data, list):
                            for item in data:
                                proxy = self._parse_json_proxy(item)
                                if proxy:
                                    proxies.append(proxy)
                    except json.JSONDecodeError:
                        continue
            
        except Exception as e:
            logger.debug(f"[{self.source_name}] 解析 JSON 數據時出錯: {str(e)}")
        
        return proxies
    
    def _parse_json_proxy(self, data: Dict[str, Any]) -> Optional[ProxyNode]:
        """解析 JSON 格式的代理數據"""
        try:
            ip = data.get('ip') or data.get('host')
            port = data.get('port')
            
            if not ip or not port:
                return None
            
            # 轉換端口為整數
            try:
                port = int(port)
            except (ValueError, TypeError):
                return None
            
            protocol = data.get('protocol', 'HTTP').upper()
            country = data.get('country', 'Unknown')
            anonymity = data.get('anonymity', 'Unknown')
            response_time = data.get('response_time') or data.get('speed')
            
            return ProxyNode(
                ip=ip,
                port=port,
                protocol=protocol,
                anonymity=anonymity,
                country=country,
                response_time=response_time,
                source=self.source_name
            )
            
        except Exception as e:
            logger.debug(f"[{self.source_name}] 解析 JSON 代理時出錯: {str(e)}")
            return None
    
    def _parse_card_format(self, soup) -> List[ProxyNode]:
        """解析卡片格式的代理數據"""
        proxies = []
        
        try:
            # 查找代理卡片
            cards = soup.find_all(['div'], class_=re.compile(r'proxy|card|item'))
            
            for card in cards:
                try:
                    # 提取 IP 和端口
                    ip_port_text = card.get_text()
                    ip_port_match = re.search(r'(\d+\.\d+\.\d+\.\d+):(\d+)', ip_port_text)
                    
                    if ip_port_match:
                        ip = ip_port_match.group(1)
                        port = int(ip_port_match.group(2))
                        
                        # 提取其他信息
                        country_match = re.search(r'Country[:\s]+(\w+)', ip_port_text, re.IGNORECASE)
                        country = country_match.group(1) if country_match else "Unknown"
                        
                        protocol_match = re.search(r'Protocol[:\s]+(\w+)', ip_port_text, re.IGNORECASE)
                        protocol = protocol_match.group(1).upper() if protocol_match else "HTTP"
                        
                        proxy = ProxyNode(
                            ip=ip,
                            port=port,
                            protocol=protocol,
                            country=country,
                            source=self.source_name
                        )
                        proxies.append(proxy)
                        
                except Exception as e:
                    logger.debug(f"[{self.source_name}] 解析卡片時出錯: {str(e)}")
                    continue
            
        except Exception as e:
            logger.debug(f"[{self.source_name}] 解析卡片格式時出錯: {str(e)}")
        
        return proxies
    
    async def _fetch_from_api(self) -> List[ProxyNode]:
        """嘗試從 API 端點獲取代理數據"""
        proxies = []
        
        # 常見的 API 端點
        api_endpoints = [
            '/api/proxy-list',
            '/api/proxies',
            '/proxy-list.json',
            '/free-proxy-list.json'
        ]
        
        for endpoint in api_endpoints:
            try:
                url = urljoin(self.base_url, endpoint)
                
                # 嘗試獲取 JSON 數據
                response = await self.make_request(url)
                if response:
                    try:
                        data = json.loads(response)
                        if isinstance(data, list):
                            for item in data:
                                proxy = self._parse_json_proxy(item)
                                if proxy:
                                    proxies.append(proxy)
                        elif isinstance(data, dict) and 'proxies' in data:
                            for item in data['proxies']:
                                proxy = self._parse_json_proxy(item)
                                if proxy:
                                    proxies.append(proxy)
                        
                        if proxies:
                            logger.info(f"[{self.source_name}] API {endpoint} 獲取到 {len(proxies)} 個代理")
                            break
                            
                    except json.JSONDecodeError:
                        continue
                
                await self.respect_rate_limit()
                
            except Exception as e:
                logger.debug(f"[{self.source_name}] API {endpoint} 請求失敗: {str(e)}")
                continue
        
        return proxies
    
    def _remove_duplicates(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """移除重複的代理"""
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            key = f"{proxy.ip}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies


async def main():
    """測試函數"""
    async with GeonodeCrawler(max_pages=3) as crawler:
        logger.info("開始抓取 Geonode 代理...")
        proxies = await crawler.crawl()
        
        # 顯示結果
        logger.info(f"總共抓取到 {len(proxies)} 個代理")
        
        # 顯示統計信息
        stats = crawler.get_stats()
        logger.info(f"統計信息: {stats}")
        
        # 按協議分組顯示
        protocol_counts = {}
        for proxy in proxies:
            protocol_counts[proxy.protocol] = protocol_counts.get(proxy.protocol, 0) + 1
        
        logger.info("按協議分組:")
        for protocol, count in protocol_counts.items():
            logger.info(f"  {protocol}: {count} 個")
        
        # 顯示前幾個代理示例
        logger.info("代理示例:")
        for i, proxy in enumerate(proxies[:5]):
            logger.info(f"  {i+1}. {proxy.ip}:{proxy.port} ({proxy.protocol}) - {proxy.country}")


if __name__ == "__main__":
    asyncio.run(main())