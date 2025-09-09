#!/usr/bin/env python3
"""
測試多個URL的URL2Parquet功能
"""

import asyncio
import httpx
import json
from pathlib import Path

async def test_urls():
    """測試四個代理網站的URL轉換"""
    
    urls = [
        "https://free-proxy-list.net/",
        "https://www.sslproxies.org/",
        "https://www.us-proxy.org/",
        "https://www.proxy-list.download/HTTP"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🚀 開始測試多個URL轉換...")
        
        # 發送轉換請求
        response = await client.post(
            "http://127.0.0.1:8000/api/url2parquet/jobs",
            json={
                "urls": urls,
                "output_formats": ["md", "json", "parquet"],
                "timeout_seconds": 30
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 轉換請求成功!")
            print(f"📋 任務ID: {result['job_id']}")
            print(f"📊 狀態: {result['status']}")
            
            if result.get('result') and result['result'].get('files'):
                print(f"📁 生成的文件:")
                for file_info in result['result']['files']:
                    print(f"  - {file_info['format'].upper()}: {file_info['path']} ({file_info['size']} bytes)")
                
                # 嘗試獲取Markdown內容
                try:
                    md_response = await client.get(
                        f"http://127.0.0.1:8000/api/url2parquet/jobs/{result['job_id']}/files/md"
                    )
                    if md_response.status_code == 200:
                        md_content = md_response.json()
                        print(f"\n📄 Markdown內容預覽 (前500字符):")
                        print("-" * 50)
                        print(md_content['content'][:500])
                        print("-" * 50)
                        
                        # 保存到文件
                        output_dir = Path("data/url2parquet/outputs")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        
                        md_file = output_dir / f"test_multiple_urls_{result['job_id']}.md"
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(md_content['content'])
                        print(f"💾 Markdown文件已保存到: {md_file}")
                        
                    else:
                        print(f"❌ 無法獲取Markdown內容: {md_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ 獲取Markdown內容時出錯: {e}")
            else:
                print("⚠️ 沒有生成文件資訊")
                
        else:
            print(f"❌ 轉換請求失敗: {response.status_code}")
            print(f"錯誤詳情: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_urls())
