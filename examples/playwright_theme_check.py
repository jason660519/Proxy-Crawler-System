from playwright.sync_api import sync_playwright
from time import sleep

URL = "http://localhost:5174"

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(URL, wait_until="load")

        # 等待應用初始化（loading spinner 約 1.5s）
        page.wait_for_timeout(2000)

        def read_state():
            data_theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
            bg_primary = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--color-background-primary')")
            return data_theme, bg_primary

        print("開啟:", URL)
        before_theme, before_bg = read_state()
        print("當前 data-theme:", before_theme)
        print("當前 --color-background-primary:", before_bg)

        # 等待主題切換按鈕出現
        try:
            page.wait_for_selector('button[title="切換主題"]', timeout=5000)
        except Exception:
            print("未找到切換主題按鈕（超時）")
            input("按 Enter 關閉... ")
            browser.close()
            raise SystemExit(0)

        btn = page.locator('button[title="切換主題"]')
        print("找到切換按鈕數量:", btn.count())
        btn.first.click()
        page.wait_for_timeout(800)

        after_theme, after_bg = read_state()
        print("切換後 data-theme:", after_theme)
        print("切換後 --color-background-primary:", after_bg)

        input("按 Enter 關閉... ")
        browser.close()
