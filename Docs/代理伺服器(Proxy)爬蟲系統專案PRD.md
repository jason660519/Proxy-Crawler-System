## **專案目標**

開發一個代理伺服器(Proxy)爬蟲系統，從指定網址抓取proxy server 代理伺服器資料。

## **資料來源**

1. [https://www.sslproxies.org/](https://www.sslproxies.org/)
2. [https://geonode.com/free-proxy-list/](https://geonode.com/free-proxy-list/)

## **技術要求**

- 使用 Python 3.11+ 作為主要開發語言
- 遵循 Project Rules 中定義的技術棧規範
- 為每個指定網站開發獨立的爬蟲程式，檔名格式: `{source_website}__proxy_crawler__.py`
- 例如：`free_proxy_list_net__proxy_crawler__.py`

## **輸出格式要求**

- 檔案命名：`{source_website}_{timestamp}_proxies.md`
- 使用英文檔案名和資料夾名
- 每筆代理資料包含：IP 地址、端口、協議類型、國家、速度、匿名性等資訊
- raw 檔使用 Markdown 表格格式儲存
- 時間戳格式：YYYYMMDD_HHMMSS

## **功能要求**

- 自動處理分頁和滾動加載
- 支援 JavaScript 渲染的網站
- 包含錯誤處理和日誌記錄
- 設定合理的請求間隔避免被封鎖
- 驗證代理伺服器的有效性

## **示例輸出格式**

`markdown`

`# Free Proxy List - 抓取時間: 2023-12-01 14:30:00`

`| IP Address | Port | Protocol | Country | Speed | Anonymity | Last Checked |`
`|------------|------|----------|---------|-------|-----------|-------------|`
`| 192.168.1.1 | 8080 | HTTP | US | 1.2s | Anonymous | 2023-12-01 |`

`| 10.0.0.1 | 3128 | HTTPS | DE | 0.8s | Elite | 2023-12-01 | `
