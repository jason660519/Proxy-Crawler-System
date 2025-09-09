#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
URL2Parquet 整合測試腳本

測試前端與後端 API 的整合功能：
- 任務創建
- 重定向處理
- 文件生成和下載
- 本地文件管理
"""

import asyncio
import httpx
import json
import time
from pathlib import Path

# 測試配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/url2parquet"

# 測試 URL
TEST_URLS = [
    "https://free-proxy-list.net/",
    "https://httpbin.org/redirect/1",  # 測試重定向
    "https://httpbin.org/html"  # 測試正常處理
]

async def test_create_job():
    """測試創建任務"""
    print("🧪 測試創建任務...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(f"{API_BASE}/jobs", json={
                "urls": TEST_URLS,
                "output_formats": ["md", "json", "parquet", "csv"],
                "timeout_seconds": 30,
                "engine": "smart"
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 任務創建成功: {data['job_id']}")
                print(f"   狀態: {data['status']}")
                
                if data.get('status') == 'redirected':
                    print(f"   重定向數量: {len(data.get('redirects', []))}")
                    return data['job_id'], data.get('redirects', [])
                elif data.get('status') == 'completed':
                    print(f"   生成文件數量: {len(data.get('result', {}).get('files', []))}")
                    return data['job_id'], []
                else:
                    return data['job_id'], []
            else:
                print(f"❌ 任務創建失敗: {response.status_code} - {response.text}")
                return None, []
                
        except Exception as e:
            print(f"❌ 請求失敗: {e}")
            return None, []

async def test_get_job(job_id: str):
    """測試獲取任務狀態"""
    print(f"🧪 測試獲取任務狀態: {job_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{API_BASE}/jobs/{job_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 任務狀態: {data['status']}")
                if data.get('result') and data['result'].get('files'):
                    print(f"   文件數量: {len(data['result']['files'])}")
                    for file in data['result']['files']:
                        print(f"   - {file['format']}: {file['path']} ({file['size']} bytes)")
                return data
            else:
                print(f"❌ 獲取任務狀態失敗: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 請求失敗: {e}")
            return None

async def test_confirm_redirect(job_id: str, redirects: list):
    """測試確認重定向"""
    if not redirects:
        print("⏭️ 跳過重定向測試（無重定向）")
        return job_id
        
    print(f"🧪 測試確認重定向: {len(redirects)} 個重定向")
    
    redirect_urls = [r['final_url'] for r in redirects]
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{API_BASE}/jobs/{job_id}/confirm-redirect", json=redirect_urls)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 重定向確認成功: {data['status']}")
                if data.get('result') and data['result'].get('files'):
                    print(f"   生成文件數量: {len(data['result']['files'])}")
                return data['job_id']
            else:
                print(f"❌ 重定向確認失敗: {response.status_code} - {response.text}")
                return job_id
                
        except Exception as e:
            print(f"❌ 請求失敗: {e}")
            return job_id

async def test_download_files(job_id: str):
    """測試下載文件"""
    print(f"🧪 測試下載文件: {job_id}")
    
    # 先獲取文件列表
    job_data = await test_get_job(job_id)
    if not job_data or not job_data.get('result') or not job_data['result'].get('files'):
        print("❌ 無文件可下載")
        return
        
    files = job_data['result']['files']
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for file in files:
            try:
                print(f"   下載 {file['format']} 文件...")
                response = await client.get(f"{API_BASE}/jobs/{job_id}/files/{file['format']}/download")
                
                if response.status_code == 200:
                    # 保存文件到測試目錄
                    test_dir = Path("test_output")
                    test_dir.mkdir(exist_ok=True)
                    
                    filename = f"test_{job_id}_{file['format']}.{file['format']}"
                    file_path = test_dir / filename
                    file_path.write_bytes(response.content)
                    
                    print(f"   ✅ {file['format']} 文件下載成功: {file_path} ({len(response.content)} bytes)")
                else:
                    print(f"   ❌ {file['format']} 文件下載失敗: {response.status_code}")
                    
            except Exception as e:
                print(f"   ❌ 下載 {file['format']} 文件失敗: {e}")

async def test_local_markdown():
    """測試本地 Markdown 文件管理"""
    print("🧪 測試本地 Markdown 文件管理...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # 列出本地文件
            response = await client.get(f"{API_BASE}/local-md?work_dir=data/url2parquet")
            
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                print(f"✅ 本地文件列表: {len(files)} 個文件")
                
                for file in files[:3]:  # 只顯示前3個
                    print(f"   - {file['filename']} ({file['size']} bytes)")
                
                # 測試讀取文件內容
                if files:
                    first_file = files[0]
                    print(f"   讀取文件內容: {first_file['filename']}")
                    
                    content_response = await client.get(f"{API_BASE}/local-md/content?filename={first_file['filename']}&work_dir=data/url2parquet")
                    
                    if content_response.status_code == 200:
                        content_data = content_response.json()
                        print(f"   ✅ 文件內容讀取成功: {len(content_data['content'])} 字符")
                    else:
                        print(f"   ❌ 文件內容讀取失敗: {content_response.status_code}")
                        
            else:
                print(f"❌ 獲取本地文件列表失敗: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 請求失敗: {e}")

async def test_health_check():
    """測試健康檢查"""
    print("🧪 測試健康檢查...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                print("✅ 後端服務健康")
                return True
            else:
                print(f"❌ 後端服務不健康: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 健康檢查失敗: {e}")
            return False

async def main():
    """主測試函數"""
    print("🚀 開始 URL2Parquet 整合測試")
    print("=" * 50)
    
    # 健康檢查
    if not await test_health_check():
        print("❌ 後端服務不可用，測試終止")
        return
    
    print()
    
    # 創建任務
    job_id, redirects = await test_create_job()
    if not job_id:
        print("❌ 無法創建任務，測試終止")
        return
    
    print()
    
    # 處理重定向
    if redirects:
        job_id = await test_confirm_redirect(job_id, redirects)
        print()
    
    # 等待任務完成
    print("⏳ 等待任務完成...")
    max_wait = 60  # 最多等待60秒
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        job_data = await test_get_job(job_id)
        if job_data and job_data.get('status') in ['completed', 'failed']:
            break
        await asyncio.sleep(2)
    
    print()
    
    # 下載文件
    await test_download_files(job_id)
    print()
    
    # 測試本地文件管理
    await test_local_markdown()
    print()
    
    print("🎉 測試完成！")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
