#!/usr/bin/env python3
"""
測試正常URL的處理
"""

import asyncio
import httpx

async def test_normal_urls():
    """測試正常URL"""
    print("🚀 開始測試正常URL處理...")
    
    # 測試正常URL
    test_urls = [
        "https://free-proxy-list.net/",
        "https://www.proxy-list.download/HTTP"
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            # 直接調用API
            response = await client.post(
                "http://127.0.0.1:8000/api/url2parquet/jobs",
                json={
                    "urls": test_urls,
                    "engine": "smart",
                    "output_formats": ["md", "json"],
                    "obey_robots_txt": True,
                    "timeout_seconds": 30,
                    "max_concurrency": 4,
                    "work_dir": "data/url2parquet"
                }
            )
            
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 請求成功!")
                print(f"響應狀態: {data.get('status')}")
                
                if data.get("status") == "completed":
                    print("✅ 處理完成:")
                    files = data.get('result', {}).get('files', [])
                    print(f"  - 生成檔案: {len(files)}")
                    for file in files:
                        print(f"    - {file.get('format')}: {file.get('path')}")
                else:
                    print(f"狀態: {data.get('status')}")
            else:
                print(f"❌ 請求失敗: {response.status_code}")
                print(f"錯誤詳情: {response.text}")
                
        except Exception as e:
            print(f"❌ 請求異常: {e}")

if __name__ == "__main__":
    asyncio.run(test_normal_urls())
