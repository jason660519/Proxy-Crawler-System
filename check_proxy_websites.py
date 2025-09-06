#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理網站可訪問性檢查工具

檢查PRD文檔中列出的2個代理網站的當前狀態，
識別哪些網站仍然可用，哪些已經無法訪問或重複。
"""

import asyncio
import aiohttp
import time
from typing import Dict, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class WebsiteStatus:
    """網站狀態資料類"""
    url: str
    name: str
    status_code: int = 0
    response_time: float = 0.0
    is_accessible: bool = False
    error_message: str = ""
    content_length: int = 0
    final_url: str = ""  # 重定向後的最終URL


class ProxyWebsiteChecker:
    """代理網站檢查器"""
    
    def __init__(self):
        """初始化檢查器"""
        self.websites = [
            # 當前專案使用的代理來源
            ("https://www.sslproxies.org/", "SSL Proxies"),
            ("https://geonode.com/free-proxy-list/", "Geonode Free Proxy"),
            # GitHub 代理專案
            ("https://github.com/monosans/proxy-scraper-checker", "Proxy Scraper Checker (Rust)"),
            ("https://github.com/roosterkid/openproxylist", "Open Proxy List"),
            ("https://github.com/proxifly/free-proxy-list", "Proxifly Free Proxy List"),
            # ProxyScraper 相關
            ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "ProxyScraper HTTP List"),
            ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt", "ProxyScraper SOCKS4 List"),
            ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt", "ProxyScraper SOCKS5 List")
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def check_website(self, session: aiohttp.ClientSession, url: str, name: str) -> WebsiteStatus:
        """檢查單個網站的可訪問性
        
        Args:
            session: aiohttp會話對象
            url: 網站URL
            name: 網站名稱
            
        Returns:
            WebsiteStatus: 網站狀態信息
        """
        status = WebsiteStatus(url=url, name=name)
        start_time = time.time()
        
        try:
            async with session.get(
                url, 
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=True
            ) as response:
                status.status_code = response.status
                status.response_time = time.time() - start_time
                status.final_url = str(response.url)
                
                # 讀取內容長度
                content = await response.read()
                status.content_length = len(content)
                
                # 判斷是否可訪問（狀態碼200-299為成功）
                status.is_accessible = 200 <= response.status < 300
                
                if not status.is_accessible:
                    status.error_message = f"HTTP {response.status}"
                    
        except asyncio.TimeoutError:
            status.response_time = time.time() - start_time
            status.error_message = "請求超時"
        except aiohttp.ClientError as e:
            status.response_time = time.time() - start_time
            status.error_message = f"連接錯誤: {str(e)}"
        except Exception as e:
            status.response_time = time.time() - start_time
            status.error_message = f"未知錯誤: {str(e)}"
        
        return status
    
    async def check_all_websites(self) -> List[WebsiteStatus]:
        """檢查所有網站的可訪問性
        
        Returns:
            List[WebsiteStatus]: 所有網站的狀態列表
        """
        connector = aiohttp.TCPConnector(
            limit=10,
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [
                self.check_website(session, url, name) 
                for url, name in self.websites
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理異常結果
            statuses = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    url, name = self.websites[i]
                    status = WebsiteStatus(url=url, name=name)
                    status.error_message = f"任務異常: {str(result)}"
                    statuses.append(status)
                else:
                    statuses.append(result)
            
            return statuses
    
    def analyze_results(self, statuses: List[WebsiteStatus]) -> Dict:
        """分析檢查結果
        
        Args:
            statuses: 網站狀態列表
            
        Returns:
            Dict: 分析結果
        """
        accessible = [s for s in statuses if s.is_accessible]
        inaccessible = [s for s in statuses if not s.is_accessible]
        
        # 檢查重複的域名
        domains = {}
        for status in statuses:
            domain = urlparse(status.url).netloc
            if domain in domains:
                domains[domain].append(status)
            else:
                domains[domain] = [status]
        
        duplicates = {domain: sites for domain, sites in domains.items() if len(sites) > 1}
        
        return {
            'total': len(statuses),
            'accessible': len(accessible),
            'inaccessible': len(inaccessible),
            'accessible_sites': accessible,
            'inaccessible_sites': inaccessible,
            'duplicates': duplicates,
            'success_rate': len(accessible) / len(statuses) * 100 if statuses else 0
        }
    
    def print_results(self, analysis: Dict):
        """打印檢查結果
        
        Args:
            analysis: 分析結果字典
        """
        print("\n" + "="*80)
        print("代理網站可訪問性檢查報告")
        print("="*80)
        
        print(f"\n📊 總體統計:")
        print(f"   總網站數: {analysis['total']}")
        print(f"   可訪問: {analysis['accessible']} ({analysis['success_rate']:.1f}%)")
        print(f"   不可訪問: {analysis['inaccessible']}")
        
        print(f"\n✅ 可訪問的網站 ({len(analysis['accessible_sites'])}個):")
        for status in analysis['accessible_sites']:
            print(f"   • {status.name}")
            print(f"     URL: {status.url}")
            print(f"     狀態: HTTP {status.status_code} | 響應時間: {status.response_time:.2f}s | 內容大小: {status.content_length:,} bytes")
            if status.final_url != status.url:
                print(f"     重定向至: {status.final_url}")
            print()
        
        print(f"\n❌ 不可訪問的網站 ({len(analysis['inaccessible_sites'])}個):")
        for status in analysis['inaccessible_sites']:
            print(f"   • {status.name}")
            print(f"     URL: {status.url}")
            print(f"     錯誤: {status.error_message}")
            if status.status_code > 0:
                print(f"     狀態碼: {status.status_code} | 響應時間: {status.response_time:.2f}s")
            print()
        
        if analysis['duplicates']:
            print(f"\n🔄 重複域名檢查:")
            for domain, sites in analysis['duplicates'].items():
                print(f"   域名: {domain}")
                for site in sites:
                    print(f"     - {site.name}: {site.url}")
                print()
        else:
            print(f"\n✨ 沒有發現重複的域名")
        
        print("\n" + "="*80)
        print("檢查完成")
        print("="*80)


async def main():
    """主函數"""
    print("開始檢查代理網站可訪問性...")
    
    checker = ProxyWebsiteChecker()
    statuses = await checker.check_all_websites()
    analysis = checker.analyze_results(statuses)
    checker.print_results(analysis)


if __name__ == "__main__":
    asyncio.run(main())