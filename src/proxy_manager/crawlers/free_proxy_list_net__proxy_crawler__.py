"""Free-Proxy-List.net 代理爬蟲模組

此模組實現了從 free-proxy-list.net 網站抓取免費代理的功能。
Free-Proxy-List.net 是一個知名的免費代理提供網站，提供多種類型的代理列表。

支援的代理類型：
- HTTP/HTTPS 代理
- SOCKS4 代理
- SOCKS5 代理
- 匿名代理
- 透明代理

特點：
- 實時更新的代理列表
- 詳細的代理信息（國家、匿名等級、HTTPS支援等）
- 多個專門的代理列表頁面
"""

import asyncio
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin

from loguru import logger

from .base_crawler import BaseCrawler, ProxyNode


class FreeProxyListCrawler(BaseCrawler):
    """Free-Proxy-List.net 代理爬蟲
    
    從 free-proxy-list.net 抓取各種類型的免費代理列表
    """
    
    def __init__(self):
        """初始化 Free-Proxy-List 爬蟲"""
        super().__init__(
            source_name="Free-Proxy-List.net",
            base_url="https://free-proxy-list.net",
            delay_range=(1.0, 2.5),
            timeout=30,
            max_retries=3
        )
        
        # 定義要爬取的頁面
        self.proxy_pages = {
            'http': '/',  # 主要的 HTTP/HTTPS 代理列表
            'anonymous': '/anonymous-proxy.html',  # 匿名代理
            'uk': '/uk-proxy.html',  # 英國代理
            'us': '/us-proxy.html',  # 美國代理
            'socks': '/socks-proxy.html',  # SOCKS 代理
        }
        
        # 匿名等級映射
        self.anonymity_mapping = {
            'elite proxy': 'Elite',
            'anonymous': 'Anonymous', 
            'transparent': 'Transparent',
            'high anonymity': 'Elite',
            'no': 'Transparent',
            'yes': 'Anonymous'
        }
    
    async def fetch_proxies(self) -> List[ProxyNode]:
        """抓取所有類型的代理
        
        Returns:
            所有抓取到的代理節點列表
        """
        all_proxies = []
        
        for proxy_type, path in self.proxy_pages.items():
            logger.info(f"[{self.source_name}] 開始抓取 {proxy_type.upper()} 代理")
            
            try:
                # 構建完整 URL
                url = urljoin(self.base_url, path)
                
                # 發送請求
                html_content = await self.make_request(url)
                if html_content:
                    # 解析代理
                    proxies = self.parse_proxy_page(html_content, proxy_type)
                    all_proxies.extend(proxies)
                    logger.info(f"[{self.source_name}] {proxy_type.upper()} 頁面找到 {len(proxies)} 個代理")
                else:
                    logger.warning(f"[{self.source_name}] 無法獲取 {proxy_type.upper()} 頁面內容")
                
                # 遵守速率限制
                await self.respect_rate_limit()
                
            except Exception as e:
                logger.error(f"[{self.source_name}] 抓取 {proxy_type.upper()} 代理時發生錯誤: {str(e)}")
        
        # 去重處理
        unique_proxies = self._remove_duplicates(all_proxies)
        logger.info(f"[{self.source_name}] 去重後共有 {len(unique_proxies)} 個唯一代理")
        
        return unique_proxies
    
    def parse_proxy_page(self, html_content: str, proxy_type: str = 'http') -> List[ProxyNode]:
        """解析代理頁面
        
        Args:
            html_content: HTML 內容
            proxy_type: 代理類型
            
        Returns:
            解析出的代理節點列表
        """
        soup = self.parse_html(html_content)
        proxies = []
        
        try:
            # 查找代理表格 - Free-Proxy-List 使用特定的表格 ID
            table = soup.find('table', {'id': 'proxylisttable'})
            if not table:
                # 備用選擇器
                table = soup.find('table', {'class': 'table table-striped table-bordered'})
                if not table:
                    table = soup.find('table')
            
            if not table:
                logger.warning(f"[{self.source_name}] 未找到代理表格")
                return proxies
            
            # 查找表格體
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
            else:
                # 如果沒有 tbody，直接查找所有行並跳過標題
                all_rows = table.find_all('tr')
                rows = all_rows[1:] if len(all_rows) > 1 else []
            
            logger.debug(f"[{self.source_name}] 找到 {len(rows)} 行數據")
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 7:  # Free-Proxy-List 通常有8列
                        proxy = self._parse_table_row(cells, proxy_type)
                        if proxy:
                            proxies.append(proxy)
                except Exception as e:
                    logger.debug(f"[{self.source_name}] 解析行時出錯: {str(e)}")
                    continue
            
            logger.debug(f"[{self.source_name}] 從 {proxy_type} 頁面解析出 {len(proxies)} 個代理")
            
        except Exception as e:
            logger.error(f"[{self.source_name}] 解析 {proxy_type} 頁面時發生錯誤: {str(e)}")
        
        return proxies
    
    def _parse_table_row(self, cells: List, proxy_type: str) -> Optional[ProxyNode]:
        """解析表格行數據
        
        Free-Proxy-List.net 的表格結構通常是：
        IP Address | Port | Code | Country | Anonymity | Google | Https | Last Checked
        
        Args:
            cells: 表格單元格列表
            proxy_type: 代理類型
            
        Returns:
            代理節點對象或 None
        """
        try:
            # 提取基本信息
            ip = cells[0].get_text(strip=True)
            port_text = cells[1].get_text(strip=True)
            
            # 驗證和轉換端口
            try:
                port = int(port_text)
            except ValueError:
                logger.debug(f"[{self.source_name}] 無效端口: {port_text}")
                return None
            
            # 提取國家代碼和國家名稱
            country_code = "Unknown"
            country_name = "Unknown"
            if len(cells) > 2:
                country_code = cells[2].get_text(strip=True)
            if len(cells) > 3:
                country_name = cells[3].get_text(strip=True)
                if country_name:
                    country = country_name
                elif country_code:
                    country = country_code
                else:
                    country = "Unknown"
            else:
                country = country_code if country_code else "Unknown"
            
            # 提取匿名等級
            anonymity = "Unknown"
            if len(cells) > 4:
                anonymity_text = cells[4].get_text(strip=True).lower()
                anonymity = self.anonymity_mapping.get(anonymity_text, anonymity_text.title())
            
            # 檢查是否支援 HTTPS
            supports_https = False
            if len(cells) > 6:
                https_text = cells[6].get_text(strip=True).lower()
                supports_https = https_text in ['yes', 'true', '1']
            
            # 確定協議類型
            protocol = self._determine_protocol(proxy_type, supports_https, anonymity)
            
            # 提取最後檢查時間
            last_checked_text = ""
            if len(cells) > 7:
                last_checked_text = cells[7].get_text(strip=True)
            
            # 創建代理節點
            proxy = ProxyNode(
                ip=ip,
                port=port,
                protocol=protocol,
                anonymity=anonymity,
                country=country,
                source=self.source_name
            )
            
            return proxy
            
        except Exception as e:
            logger.debug(f"[{self.source_name}] 解析行數據時出錯: {str(e)}")
            return None
    
    def _determine_protocol(self, proxy_type: str, supports_https: bool, anonymity: str) -> str:
        """根據頁面類型和特性確定協議
        
        Args:
            proxy_type: 代理類型
            supports_https: 是否支援 HTTPS
            anonymity: 匿名等級
            
        Returns:
            協議字符串
        """
        proxy_type = proxy_type.lower()
        
        if proxy_type == 'socks' or 'socks' in proxy_type:
            # 對於 SOCKS 頁面，需要進一步判斷是 SOCKS4 還是 SOCKS5
            # 通常 SOCKS5 支援更多功能，這裡默認為 SOCKS5
            return 'SOCKS5'
        elif supports_https:
            return 'HTTPS'
        else:
            return 'HTTP'
    
    def _remove_duplicates(self, proxies: List[ProxyNode]) -> List[ProxyNode]:
        """移除重複的代理
        
        Args:
            proxies: 代理列表
            
        Returns:
            去重後的代理列表
        """
        seen = set()
        unique_proxies = []
        
        for proxy in proxies:
            # 使用 IP:Port 作為唯一標識
            key = f"{proxy.ip}:{proxy.port}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)
        
        return unique_proxies
    
    async def get_proxy_statistics(self) -> Dict[str, any]:
        """獲取代理統計信息
        
        Returns:
            包含各種統計信息的字典
        """
        stats = {
            'total_proxies': 0,
            'by_type': {},
            'by_country': {},
            'by_anonymity': {},
            'by_protocol': {}
        }
        
        try:
            # 抓取主頁面獲取統計信息
            html_content = await self.make_request(self.base_url)
            if html_content:
                soup = self.parse_html(html_content)
                
                # 嘗試從頁面中提取統計信息
                # 查找可能包含統計信息的元素
                stat_elements = soup.find_all(['div', 'span', 'p'], 
                                            text=re.compile(r'\d+\s*(proxy|proxies)', re.IGNORECASE))
                
                for element in stat_elements:
                    text = element.get_text()
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        stats['total_proxies'] = max(stats['total_proxies'], int(numbers[0]))
        
        except Exception as e:
            logger.error(f"[{self.source_name}] 獲取統計信息時出錯: {str(e)}")
        
        return stats
    
    async def check_website_status(self) -> Dict[str, bool]:
        """檢查各個頁面的可用性
        
        Returns:
            各頁面的可用性狀態
        """
        status = {}
        
        for page_name, path in self.proxy_pages.items():
            try:
                url = urljoin(self.base_url, path)
                html_content = await self.make_request(url)
                status[page_name] = html_content is not None
                
                if status[page_name]:
                    logger.info(f"[{self.source_name}] {page_name} 頁面可用")
                else:
                    logger.warning(f"[{self.source_name}] {page_name} 頁面不可用")
                
                await self.respect_rate_limit()
                
            except Exception as e:
                logger.error(f"[{self.source_name}] 檢查 {page_name} 頁面時出錯: {str(e)}")
                status[page_name] = False
        
        return status


async def main():
    """測試函數"""
    async with FreeProxyListCrawler() as crawler:
        # 檢查網站狀態
        logger.info("檢查網站頁面狀態...")
        status = await crawler.check_website_status()
        for page, available in status.items():
            logger.info(f"{page}: {'可用' if available else '不可用'}")
        
        # 獲取統計信息
        logger.info("獲取統計信息...")
        stats = await crawler.get_proxy_statistics()
        logger.info(f"網站統計: {stats}")
        
        # 抓取代理
        logger.info("開始抓取代理...")
        proxies = await crawler.crawl()
        
        # 顯示結果
        logger.info(f"總共抓取到 {len(proxies)} 個代理")
        
        # 按協議分組統計
        protocol_counts = {}
        country_counts = {}
        anonymity_counts = {}
        
        for proxy in proxies:
            # 協議統計
            protocol_counts[proxy.protocol] = protocol_counts.get(proxy.protocol, 0) + 1
            # 國家統計
            country_counts[proxy.country] = country_counts.get(proxy.country, 0) + 1
            # 匿名等級統計
            anonymity_counts[proxy.anonymity] = anonymity_counts.get(proxy.anonymity, 0) + 1
        
        logger.info("按協議分組:")
        for protocol, count in sorted(protocol_counts.items()):
            logger.info(f"  {protocol}: {count} 個")
        
        logger.info("按國家分組 (前5名):")
        for country, count in sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            logger.info(f"  {country}: {count} 個")
        
        logger.info("按匿名等級分組:")
        for anonymity, count in sorted(anonymity_counts.items()):
            logger.info(f"  {anonymity}: {count} 個")
        
        # 顯示爬蟲統計信息
        crawler_stats = crawler.get_stats()
        logger.info(f"爬蟲統計: {crawler_stats}")
        
        # 顯示前幾個代理示例
        logger.info("代理示例:")
        for i, proxy in enumerate(proxies[:5]):
            logger.info(f"  {i+1}. {proxy.ip}:{proxy.port} ({proxy.protocol}) - {proxy.country} [{proxy.anonymity}]")


if __name__ == "__main__":
    asyncio.run(main())