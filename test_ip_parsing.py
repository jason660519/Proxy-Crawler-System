#!/usr/bin/env python3
"""
測試 IP 解析功能
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class ProxyInfo:
    ip: str
    port: int
    country_code: str
    country_name: str
    anonymity: str
    google_support: bool
    https_support: bool
    last_checked: str

def parse_proxy_table(markdown_content: str) -> List[ProxyInfo]:
    """解析 Markdown 中的代理表格"""
    lines = markdown_content.split('\n')
    proxy_list = []
    
    # 找到表格開始位置
    table_start = -1
    for i, line in enumerate(lines):
        if '| IP Address | Port | Code | Country |' in line:
            table_start = i + 2  # 跳過標題行和分隔行
            break
    
    if table_start == -1:
        return proxy_list
    
    # 解析表格行
    for i in range(table_start, len(lines)):
        line = lines[i].strip()
        if not line.startswith('|') or line == '':
            break
        
        cells = [cell.strip() for cell in line.split('|') if cell.strip()]
        if len(cells) >= 8:
            try:
                proxy = ProxyInfo(
                    ip=cells[0],
                    port=int(cells[1]),
                    country_code=cells[2],
                    country_name=cells[3],
                    anonymity=cells[4],
                    google_support=cells[5] == 'yes',
                    https_support=cells[6] == 'yes',
                    last_checked=cells[7]
                )
                proxy_list.append(proxy)
            except (ValueError, IndexError) as e:
                print(f"解析代理行失敗: {line} - {e}")
    
    return proxy_list

def main():
    # 讀取生成的 Markdown 文件
    with open('data/url2parquet/outputs/db0c07dc_content.md', 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # 解析代理列表
    proxy_list = parse_proxy_table(markdown_content)
    
    print(f"成功解析 {len(proxy_list)} 個代理")
    print("\n前 10 個代理:")
    print("-" * 80)
    print(f"{'IP':<15} {'Port':<6} {'Country':<15} {'Anonymity':<12} {'HTTPS':<6} {'Google':<6}")
    print("-" * 80)
    
    for i, proxy in enumerate(proxy_list[:10]):
        print(f"{proxy.ip:<15} {proxy.port:<6} {proxy.country_name:<15} {proxy.anonymity:<12} {'Yes' if proxy.https_support else 'No':<6} {'Yes' if proxy.google_support else 'No':<6}")
    
    # 統計資訊
    print(f"\n統計資訊:")
    print(f"總代理數: {len(proxy_list)}")
    print(f"支援 HTTPS: {sum(1 for p in proxy_list if p.https_support)}")
    print(f"支援 Google: {sum(1 for p in proxy_list if p.google_support)}")
    print(f"Elite 代理: {sum(1 for p in proxy_list if 'elite' in p.anonymity)}")
    print(f"匿名代理: {sum(1 for p in proxy_list if 'anonymous' in p.anonymity)}")
    
    # 按國家分組
    country_stats = {}
    for proxy in proxy_list:
        country = proxy.country_name
        country_stats[country] = country_stats.get(country, 0) + 1
    
    print(f"\n按國家分組 (前 10 個):")
    for country, count in sorted(country_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{country}: {count}")

if __name__ == "__main__":
    main()
