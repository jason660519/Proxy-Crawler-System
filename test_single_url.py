#!/usr/bin/env python3
"""
測試單個URL的URL2Parquet功能
"""

import asyncio
import httpx

async def test_single_url():
    """測試單個URL"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 測試單個URL
        response = await client.post(
            'http://127.0.0.1:8000/api/url2parquet/jobs',
            json={
                'urls': ['https://www.sslproxies.org/'],
                'output_formats': ['md', 'json'],
                'timeout_seconds': 30
            }
        )
        
        print(f'狀態碼: {response.status_code}')
        if response.status_code == 200:
            result = response.json()
            print(f'任務ID: {result["job_id"]}')
            print(f'狀態: {result["status"]}')
            if result.get('result') and result['result'].get('files'):
                print('生成的文件:')
                for file in result['result']['files']:
                    print(f'  - {file["format"]}: {file["path"]}')
        else:
            print(f'錯誤: {response.text}')

if __name__ == "__main__":
    asyncio.run(test_single_url())
