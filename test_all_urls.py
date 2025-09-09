#!/usr/bin/env python3
"""
測試所有URL的URL2Parquet功能
"""

import asyncio
import httpx

async def test_url(url):
    """測試單個URL"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                'http://127.0.0.1:8000/api/url2parquet/jobs',
                json={
                    'urls': [url],
                    'output_formats': ['md', 'json'],
                    'timeout_seconds': 30
                }
            )
            
            print(f'\n🌐 測試 URL: {url}')
            print(f'狀態碼: {response.status_code}')
            
            if response.status_code == 200:
                result = response.json()
                print(f'✅ 任務ID: {result["job_id"]}')
                print(f'📊 狀態: {result["status"]}')
                if result.get('result') and result['result'].get('files'):
                    print('📁 生成的文件:')
                    for file in result['result']['files']:
                        print(f'  - {file["format"]}: {file["path"]} ({file["size"]} bytes)')
                return True
            else:
                print(f'❌ 錯誤: {response.text}')
                return False
                
        except Exception as e:
            print(f'❌ 異常: {e}')
            return False

async def test_all_urls():
    """測試所有URL"""
    urls = [
        "https://free-proxy-list.net/",
        "https://www.sslproxies.org/",
        "https://www.us-proxy.org/",
        "https://www.proxy-list.download/HTTP"
    ]
    
    print("🚀 開始測試所有URL...")
    
    results = []
    for url in urls:
        success = await test_url(url)
        results.append((url, success))
        await asyncio.sleep(1)  # 避免請求過於頻繁
    
    print(f"\n📊 測試結果總結:")
    for url, success in results:
        status = "✅ 成功" if success else "❌ 失敗"
        print(f"  {status}: {url}")

if __name__ == "__main__":
    asyncio.run(test_all_urls())
