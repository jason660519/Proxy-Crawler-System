#!/usr/bin/env python3
"""
檢查URL2Parquet轉換結果
"""

import json
from pathlib import Path

def check_results():
    """檢查所有轉換結果"""
    output_dir = Path('data/url2parquet/outputs')
    json_files = list(output_dir.glob('*.json'))
    
    print(f'找到 {len(json_files)} 個JSON文件:')
    
    for json_file in sorted(json_files, key=lambda x: x.stat().st_mtime):
        print(f'\n📄 {json_file.name}:')
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                if 'url' in data:
                    print(f'  URL: {data["url"]}')
                if 'title' in data:
                    print(f'  標題: {data["title"]}')
                if 'content' in data:
                    content = data['content']
                    if isinstance(content, str):
                        print(f'  內容長度: {len(content)} 字符')
                        # 查找代理相關內容
                        if 'proxy' in content.lower() or 'ip' in content.lower():
                            print('  ✅ 包含代理相關內容')
                        else:
                            print('  ❌ 不包含代理相關內容')
            else:
                print(f'  數據類型: {type(data)}')
                
        except Exception as e:
            print(f'  ❌ 讀取失敗: {e}')

if __name__ == "__main__":
    check_results()
