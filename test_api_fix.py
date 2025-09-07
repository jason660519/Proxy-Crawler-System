#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 修復測試腳本

測試修復後的 API 端點是否正常工作
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_api_endpoints():
    """測試 API 端點"""
    base_url = "http://localhost:8000"
    
    print("🔍 開始測試 API 端點...")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # 測試基本端點
        endpoints = [
            ("/", "根路徑"),
            ("/health", "健康檢查"),
            ("/status", "系統狀態"),
            ("/docs", "API 文檔"),
        ]
        
        for endpoint, description in endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    status = response.status
                    if status == 200:
                        print(f"✅ {description}: {endpoint} - 狀態碼 {status}")
                    else:
                        print(f"⚠️ {description}: {endpoint} - 狀態碼 {status}")
            except Exception as e:
                print(f"❌ {description}: {endpoint} - 錯誤: {e}")
        
        print("\n" + "=" * 50)
        print("🔍 測試代理管理功能...")
        
        # 測試代理管理相關功能
        try:
            # 測試代理獲取
            async with session.get(f"{base_url}/api/proxies?limit=5") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 代理列表 API: 成功獲取 {len(data)} 個代理")
                else:
                    print(f"⚠️ 代理列表 API: 狀態碼 {response.status}")
        except Exception as e:
            print(f"❌ 代理列表 API: 錯誤 - {e}")
        
        try:
            # 測試代理統計
            async with session.get(f"{base_url}/api/stats") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ 代理統計 API: 成功獲取統計數據")
                else:
                    print(f"⚠️ 代理統計 API: 狀態碼 {response.status}")
        except Exception as e:
            print(f"❌ 代理統計 API: 錯誤 - {e}")
        
        print("\n" + "=" * 50)
        print("🔍 測試 ETL 功能...")
        
        try:
            # 測試 ETL 狀態
            async with session.get(f"{base_url}/etl/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ ETL 狀態 API: 成功獲取 ETL 狀態")
                else:
                    print(f"⚠️ ETL 狀態 API: 狀態碼 {response.status}")
        except Exception as e:
            print(f"❌ ETL 狀態 API: 錯誤 - {e}")

async def test_html_to_markdown_service():
    """測試 HTML to Markdown 服務"""
    print("\n" + "=" * 50)
    print("🔍 測試 HTML to Markdown 服務...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 測試健康檢查
            async with session.get("http://localhost:8001/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ HTML to Markdown 健康檢查: 正常")
                else:
                    print(f"⚠️ HTML to Markdown 健康檢查: 狀態碼 {response.status}")
        except Exception as e:
            print(f"❌ HTML to Markdown 健康檢查: 錯誤 - {e}")
        
        try:
            # 測試轉換功能
            test_html = "<h1>測試標題</h1><p>這是一個測試段落。</p>"
            payload = {
                "html_content": test_html,
                "engine": "markdownify"
            }
            
            async with session.post("http://localhost:8001/convert", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("success"):
                        print(f"✅ HTML to Markdown 轉換: 成功")
                        print(f"   轉換結果: {data.get('markdown_content', '')[:50]}...")
                    else:
                        print(f"⚠️ HTML to Markdown 轉換: 失敗 - {data.get('error_message')}")
                else:
                    print(f"⚠️ HTML to Markdown 轉換: 狀態碼 {response.status}")
        except Exception as e:
            print(f"❌ HTML to Markdown 轉換: 錯誤 - {e}")

async def test_frontend():
    """測試前端服務"""
    print("\n" + "=" * 50)
    print("🔍 測試前端服務...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("http://localhost:3000") as response:
                if response.status == 200:
                    content = await response.text()
                    if "html" in content.lower():
                        print(f"✅ 前端服務: 正常運行")
                    else:
                        print(f"⚠️ 前端服務: 響應內容異常")
                else:
                    print(f"⚠️ 前端服務: 狀態碼 {response.status}")
        except Exception as e:
            print(f"❌ 前端服務: 錯誤 - {e}")

async def main():
    """主測試函數"""
    print("🚀 開始 API 修復測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 測試主 API 服務
    await test_api_endpoints()
    
    # 測試 HTML to Markdown 服務
    await test_html_to_markdown_service()
    
    # 測試前端服務
    await test_frontend()
    
    print("\n" + "=" * 50)
    print("✅ 測試完成！")

if __name__ == "__main__":
    asyncio.run(main())
