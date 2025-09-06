"""SSLProxies.org 代理爬蟲模組

此模組實現了從 sslproxies.org 網站抓取免費代理的功能。
SSLProxies.org 提供多種類型的代理列表，包括 HTTP、HTTPS、SOCKS4 和 SOCKS5。

支援的代理類型：
- HTTP/HTTPS 代理
- SOCKS4 代理  
- SOCKS5 代理
- Elite 代理
- Anonymous 代理
"""

import asyncio
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin

from loguru import logger

from .base_crawler import BaseCrawler, ProxyNode


class SSLProxiesCrawler(BaseCrawler):
    """SSLProxies.org 代理爬蟲
    
    從 sslproxies.org 抓取各種類型的免費代理列表
    """
    
    def __init__(self):
        """初始化 SSLProxies 爬蟲"""
        super().__init__(
            source_name="SSLProxies.org",
            base_url="https://www.sslproxies.org",
            delay_range=(2.0, 4.0),  # 較長的延遲以避免被封
            timeout=30,
            max_retries=3
        )
        
        # 定義要爬取的頁面
        self.proxy_pages = {
            'http': '/',  # HTTP/HTTPS 代理
            'socks4': '/socks-4-proxies',  # SOCKS4 代理
            'socks5': '/socks-5-proxies',  # SOCKS5 代理
            'elite': '/elite-proxies',  # Elite 代理
            'anonymous': '/anonymous-proxies',  # Anonymous 代理
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
            # 查找代理表格
            table = soup.find('table', {'class': 'table table-striped table-bordered'})
            if not table:
                # 嘗試其他可能的表格選擇器
                table = soup.find('table', {'id': 'proxylisttable'})
                if not table:
                    table = soup.find('table')
            
            if not table:
                logger.warning(f"[{self.source_name}] 未找到代理表格")
                return proxies
            
            # 查找表格行
            rows = table.find('tbody')
            if rows:
                rows = rows.find_all('tr')
            else:
                rows = table.find_all('tr')[1:]  # 跳過標題行
            
            for row in rows:
                try:
                    cells = row.find_all('td')
                    if len(cells) >= 7:  # 確保有足夠的列
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
            
            # 提取國家信息
            country = "Unknown"
            if len(cells) > 2:
                country_cell = cells[2]
                country_text = country_cell.get_text(strip=True)
                if country_text:
                    country = country_text
            
            # 提取匿名等級
            anonymity = "Unknown"
            if len(cells) > 4:
                anonymity_text = cells[4].get_text(strip=True)
                if anonymity_text:
                    anonymity = anonymity_text
            
            # 確定協議類型
            protocol = self._determine_protocol(proxy_type, anonymity)
            
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
    
    def _determine_protocol(self, proxy_type: str, anonymity: str) -> str:
        """根據頁面類型和匿名等級確定協議
        
        Args:
            proxy_type: 代理類型
            anonymity: 匿名等級
            
        Returns:
            協議字符串
        """
        proxy_type = proxy_type.lower()
        
        if proxy_type == 'socks4':
            return 'SOCKS4'
        elif proxy_type == 'socks5':
            return 'SOCKS5'
        elif 'https' in anonymity.lower() or proxy_type == 'https':
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
    
    async def get_proxy_count_estimate(self) -> Dict[str, int]:
        """獲取各類型代理的數量估計
        
        Returns:
            各類型代理數量的字典
        """
        counts = {}
        
        for proxy_type, path in self.proxy_pages.items():
            try:
                url = urljoin(self.base_url, path)
                html_content = await self.make_request(url)
                
                if html_content:
                    # 嘗試從頁面中提取代理數量信息
                    soup = self.parse_html(html_content)
                    
                    # 查找表格行數
                    table = soup.find('table', {'class': 'table table-striped table-bordered'})
                    if table:
                        rows = table.find_all('tr')
                        # 減去標題行
                        count = max(0, len(rows) - 1)
                        counts[proxy_type] = count
                    else:
                        counts[proxy_type] = 0
                else:
                    counts[proxy_type] = 0
                
                await self.respect_rate_limit()
                
            except Exception as e:
                logger.error(f"[{self.source_name}] 獲取 {proxy_type} 數量時出錯: {str(e)}")
                counts[proxy_type] = 0
        
        return counts


async def main():
    """測試函數"""
    async with SSLProxiesCrawler() as crawler:
        # 獲取代理數量估計
        logger.info("獲取代理數量估計...")
        counts = await crawler.get_proxy_count_estimate()
        for proxy_type, count in counts.items():
            logger.info(f"{proxy_type.upper()}: {count} 個代理")
        
        # 抓取代理
        logger.info("開始抓取代理...")
        proxies = await crawler.crawl()
        
        # 顯示結果
        logger.info(f"總共抓取到 {len(proxies)} 個代理")
        
        # 顯示統計信息
        stats = crawler.get_stats()
        logger.info(f"統計信息: {stats}")
        
        # 顯示前幾個代理示例
        for i, proxy in enumerate(proxies[:5]):
            logger.info(f"代理 {i+1}: {proxy.ip}:{proxy.port} ({proxy.protocol}) - {proxy.country}")


if __name__ == "__main__":
    asyncio.run(main())