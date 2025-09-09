#!/usr/bin/env python3
"""
測試多個URL的重定向處理
"""

import asyncio
import httpx

async def test_multiple_urls():
    """測試多個URL，包括重定向和正常URL"""
    print("🚀 開始測試多個URL重定向處理...")
    
    # 測試多個URL，包括會重定向的和正常的
    test_urls = [
        "https://www.sslproxies.org/",  # 會重定向
        "https://free-proxy-list.net/",  # 正常
        "https://www.us-proxy.org/",  # 可能重定向
        "https://www.proxy-list.download/HTTP"  # 正常
    ]
    
    async with httpx.AsyncClient() as client:
        try:
            # 直接調用API
            response = await client.post(
                "http://127.0.0.1:8000/api/url2parquet/jobs",
                json={
                    "urls": test_urls,
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
                print(f"響應狀態: {data.get('status')}")
                
                if data.get("status") == "redirected":
                    print("🔄 檢測到重定向:")
                    for redirect in data.get("redirects", []):
                        print(f"  - {redirect.get('original_url')} -> {redirect.get('final_url')}")
                elif data.get("status") == "completed":
                    print("✅ 處理完成:")
                    print(f"  - 生成檔案: {len(data.get('result', {}).get('files', []))}")
            else:
                print(f"❌ 請求失敗: {response.status_code}")
                print(f"錯誤詳情: {response.text}")
                
        except Exception as e:
            print(f"❌ 請求異常: {e}")

if __name__ == "__main__":
    asyncio.run(test_multiple_urls())
