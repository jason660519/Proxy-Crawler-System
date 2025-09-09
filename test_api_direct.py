#!/usr/bin/env python3
"""
直接測試API重定向處理
"""

import asyncio
import httpx

async def test_api_redirect():
    """測試API重定向處理"""
    print("🚀 開始測試API重定向處理...")
    
    # 測試重定向URL
    test_url = "https://www.sslproxies.org/"
    
    async with httpx.AsyncClient() as client:
        try:
            # 直接調用API
            response = await client.post(
                "http://127.0.0.1:8000/api/url2parquet/jobs",
                json={
                    "urls": [test_url],
                    "engine": "smart",
                    "output_formats": ["md", "json", "parquet"],
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
                print(f"響應: {data}")
            else:
                print(f"❌ 請求失敗: {response.status_code}")
                print(f"錯誤詳情: {response.text}")
                
        except Exception as e:
            print(f"❌ 請求異常: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_redirect())
