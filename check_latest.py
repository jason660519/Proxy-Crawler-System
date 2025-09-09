#!/usr/bin/env python3
"""
檢查最新的轉換結果
"""

import json
from pathlib import Path

def check_latest():
    """檢查最新的文件"""
    output_dir = Path('data/url2parquet/outputs')
    json_files = list(output_dir.glob('*.json'))
    latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
    
    print(f'最新的JSON文件: {latest_json.name}')
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f'URL: {data.get("url", "未知")}')
    print(f'標題: {data.get("title", "未知")}')
    
    if 'content' in data:
        content = data['content']
        print(f'內容長度: {len(content)} 字符')
        
        # 查找代理相關內容
        lines = content.split('\n')
        proxy_lines = [line for line in lines if 'proxy' in line.lower() or 'ip' in line.lower()]
        print(f'包含代理相關內容的行數: {len(proxy_lines)}')
        
        if proxy_lines:
            print('前5行代理相關內容:')
            for line in proxy_lines[:5]:
                print(f'  {line[:100]}...')

if __name__ == "__main__":
    check_latest()
