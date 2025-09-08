#!/usr/bin/env python3
"""
主題切換修復測試腳本
測試修復後的主題切換功能是否正常工作
"""

import time
from playwright.sync_api import sync_playwright

def test_theme_switching():
    """測試主題切換功能"""
    print("🎨 開始測試主題切換功能...")
    
    with sync_playwright() as p:
        # 啟動瀏覽器
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            # 訪問頁面
            print("📱 正在載入頁面...")
            page.goto('http://localhost:5173', timeout=10000)
            
            # 等待頁面完全載入
            page.wait_for_load_state('networkidle')
            print("✅ 頁面載入完成")
            
            # 檢查初始主題
            print("\n🔍 檢查初始主題狀態...")
            
            # 檢查 data-theme 屬性
            data_theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
            print(f"📋 data-theme 屬性: {data_theme}")
            
            # 檢查 localStorage
            theme_from_storage = page.evaluate("localStorage.getItem('theme')")
            print(f"💾 localStorage 中的主題: {theme_from_storage}")
            
            # 檢查 CSS 變數
            css_vars = page.evaluate("""
                () => {
                    const root = document.documentElement;
                    const computedStyle = getComputedStyle(root);
                    return {
                        '--color-background-primary': computedStyle.getPropertyValue('--color-background-primary'),
                        '--color-text-primary': computedStyle.getPropertyValue('--color-text-primary'),
                        '--color-primary-500': computedStyle.getPropertyValue('--color-primary-500'),
                        '--color-primary-600': computedStyle.getPropertyValue('--color-primary-600'),
                    };
                }
            """)
            
            print("🎨 CSS 變數值:")
            for var_name, var_value in css_vars.items():
                print(f"  {var_name}: {var_value or '未定義'}")
            
            # 查找主題切換按鈕
            print("\n🔍 尋找主題切換按鈕...")
            theme_button = page.locator('button[title="切換主題"]')
            
            if theme_button.count() > 0:
                print("✅ 找到主題切換按鈕")
                
                # 點擊主題切換按鈕
                print("🔄 點擊主題切換按鈕...")
                theme_button.click()
                
                # 等待主題切換完成
                time.sleep(1)
                
                # 檢查切換後的主題
                print("\n🔍 檢查切換後的主題狀態...")
                
                new_data_theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
                print(f"📋 新的 data-theme 屬性: {new_data_theme}")
                
                new_theme_from_storage = page.evaluate("localStorage.getItem('theme')")
                print(f"💾 新的 localStorage 主題: {new_theme_from_storage}")
                
                # 檢查新的 CSS 變數
                new_css_vars = page.evaluate("""
                    () => {
                        const root = document.documentElement;
                        const computedStyle = getComputedStyle(root);
                        return {
                            '--color-background-primary': computedStyle.getPropertyValue('--color-background-primary'),
                            '--color-text-primary': computedStyle.getPropertyValue('--color-text-primary'),
                            '--color-primary-500': computedStyle.getPropertyValue('--color-primary-500'),
                            '--color-primary-600': computedStyle.getPropertyValue('--color-primary-600'),
                        };
                    }
                """)
                
                print("🎨 新的 CSS 變數值:")
                for var_name, var_value in new_css_vars.items():
                    print(f"  {var_name}: {var_value or '未定義'}")
                
                # 驗證主題是否真的切換了
                if data_theme != new_data_theme:
                    print("✅ 主題切換成功！")
                else:
                    print("❌ 主題切換失敗！")
                
                # 再次點擊切換回來
                print("\n🔄 再次點擊主題切換按鈕...")
                theme_button.click()
                time.sleep(1)
                
                final_data_theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
                print(f"📋 最終 data-theme 屬性: {final_data_theme}")
                
                if final_data_theme == data_theme:
                    print("✅ 主題切換功能正常！")
                else:
                    print("❌ 主題切換功能異常！")
                    
            else:
                print("❌ 未找到主題切換按鈕")
            
            # 檢查調試面板
            print("\n🔍 檢查主題調試面板...")
            debug_panel = page.locator('[data-testid="theme-debugger"], .theme-debugger, [class*="DebugPanel"]')
            if debug_panel.count() > 0:
                print("✅ 找到主題調試面板")
            else:
                print("ℹ️ 未找到主題調試面板（可能只在開發環境顯示）")
            
            print("\n🎉 測試完成！")
            input("按 Enter 關閉瀏覽器...")
            
        except Exception as e:
            print(f"❌ 測試過程中發生錯誤: {e}")
            input("按 Enter 關閉瀏覽器...")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_theme_switching()
