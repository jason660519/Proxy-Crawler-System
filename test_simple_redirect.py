#!/usr/bin/env python3
"""
簡單測試重定向處理
"""

import asyncio
import httpx

async def test_simple_redirect():
    """簡單測試重定向"""
    
    url = "https://www.sslproxies.org/"
    
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=False,
            max_redirects=0
        ) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            
            print(f"狀態碼: {resp.status_code}")
            print(f"響應頭: {dict(resp.headers)}")
            
            if resp.status_code in [301, 302, 303, 307, 308]:
                redirect_url = resp.headers.get("location")
                print(f"重定向URL: {redirect_url}")
                
                if redirect_url:
                    # 確保重定向URL是完整的
                    if redirect_url.startswith('/'):
                        from urllib.parse import urljoin
                        redirect_url = urljoin(url, redirect_url)
                    
                    print(f"完整重定向URL: {redirect_url}")
                    
                    return {
                        "status": "redirected",
                        "original_url": url,
                        "final_url": redirect_url,
                        "message": f"URL已跳轉至 {redirect_url}，是否繼續測試新的URL？"
                    }
            else:
                print("沒有重定向")
                
    except httpx.HTTPStatusError as e:
        print(f"HTTP狀態錯誤: {e}")
        print(f"狀態碼: {e.response.status_code}")
        print(f"響應頭: {dict(e.response.headers)}")
        
        if e.response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = e.response.headers.get("location")
            if redirect_url:
                if redirect_url.startswith('/'):
                    from urllib.parse import urljoin
                    redirect_url = urljoin(url, redirect_url)
                
                return {
                    "status": "redirected",
                    "original_url": url,
                    "final_url": redirect_url,
                    "message": f"URL已跳轉至 {redirect_url}，是否繼續測試新的URL？"
                }
    except Exception as e:
        print(f"其他錯誤: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_redirect())
