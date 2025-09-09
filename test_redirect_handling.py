#!/usr/bin/env python3
"""
測試重定向處理功能
"""

import asyncio
import httpx

async def test_redirect_handling():
    """測試重定向處理"""
    
    urls = [
        "https://www.sslproxies.org/",
        "https://www.us-proxy.org/",
        "https://free-proxy-list.net/",
        "https://www.proxy-list.download/HTTP"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🚀 開始測試重定向處理...")
        
        # 發送轉換請求
        response = await client.post(
            "http://127.0.0.1:8000/api/url2parquet/jobs",
            json={
                "urls": urls,
                "output_formats": ["md", "json", "parquet"],
                "timeout_seconds": 30
            }
        )
        
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📋 任務ID: {result['job_id']}")
            print(f"📊 狀態: {result['status']}")
            
            if result['status'] == 'redirected':
                print("🔄 檢測到重定向!")
                print(f"重定向數量: {len(result['redirects'])}")
                
                for i, redirect in enumerate(result['redirects']):
                    print(f"\n重定向 {i+1}:")
                    print(f"  原始URL: {redirect['original_url']}")
                    print(f"  重定向至: {redirect['final_url']}")
                    print(f"  訊息: {redirect['message']}")
                
                # 測試確認重定向
                print("\n🔄 測試確認重定向...")
                redirect_urls = [r['final_url'] for r in result['redirects']]
                
                confirm_response = await client.post(
                    f"http://127.0.0.1:8000/api/url2parquet/jobs/{result['job_id']}/confirm-redirect",
                    json=redirect_urls
                )
                
                if confirm_response.status_code == 200:
                    confirm_result = confirm_response.json()
                    print(f"✅ 重定向確認成功!")
                    print(f"📋 新任務ID: {confirm_result['job_id']}")
                    print(f"📊 狀態: {confirm_result['status']}")
                    
                    if confirm_result.get('result') and confirm_result['result'].get('files'):
                        print("📁 生成的文件:")
                        for file in confirm_result['result']['files']:
                            print(f"  - {file['format'].upper()}: {file['path']} ({file['size']} bytes)")
                else:
                    print(f"❌ 重定向確認失敗: {confirm_response.status_code}")
                    print(f"錯誤: {confirm_response.text}")
                    
            elif result['status'] == 'completed':
                print("✅ 轉換成功!")
                if result.get('result') and result['result'].get('files'):
                    print("📁 生成的文件:")
                    for file in result['result']['files']:
                        print(f"  - {file['format'].upper()}: {file['path']} ({file['size']} bytes)")
            else:
                print(f"⚠️ 未知狀態: {result['status']}")
                
        else:
            print(f"❌ 請求失敗: {response.status_code}")
            print(f"錯誤詳情: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_redirect_handling())
