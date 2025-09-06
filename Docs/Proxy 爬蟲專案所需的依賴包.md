# **Proxy 爬蟲專案所需的依賴包**

## **Python 主要依賴包 (基於最新架構設計)**

### **核心技術棧 (必需)**

```bash
# 異步框架與 HTTP 客戶端 (現代首選)
uv add aiohttp  # 高性能異步 HTTP 客戶端
uv add httpx    # 現代異步/同步 HTTP 庫
uv add asyncio  # Python 內建異步 IO

# 資料模型與驗證 (強烈推薦)
uv add pydantic  # 資料驗證與設置管理
# dataclasses 為 Python 3.7+ 內建，無需安裝

# 日誌系統 (現代化首選)
uv add loguru  # 結構化、用戶友好的日誌記錄

# 同步 HTTP 客戶端 (傳統穩定)
uv add requests  # 備用方案
uv add urllib3   # 底層 HTTP 庫
```

### **HTML/XML 解析與資料提取**

```bash
# HTML 解析引擎
uv add lxml           # 極速解析，XPath 支援，生產環境首選
uv add beautifulsoup4 # 簡單易用，開發測試友好
uv add parsel         # Scrapy 使用的選擇器庫，整合 XPath 和 CSS

# HTML to Markdown 轉換 (新增核心功能)
uv add markdownify      # 簡單易用的轉換器
uv add html2text        # 功能豐富的轉換工具
uv add readability-lxml # Mozilla Readability 算法
uv add newspaper3k      # 新聞文章提取與轉換
uv add trafilatura      # 網頁內容提取專家
```

### **瀏覽器自動化 (反檢測技術)**

```bash
# 現代瀏覽器自動化 (推薦)
uv add playwright  # 微軟出品，性能優異，現代替代方案

# 傳統瀏覽器自動化
uv add selenium                 # 業界標準
uv add undetected-chromedriver  # 繞過 Cloudflare 等檢測
uv add webdriver-manager        # 自動管理瀏覽器驅動

# 全功能爬蟲框架
uv add scrapy            # 異步，高併發，業界標準框架
uv add scrapy-playwright # Scrapy + Playwright 集成
```

### **資料庫與快取系統**

```bash
# 關聯式資料庫
uv add sqlalchemy    # ORM 框架
uv add psycopg2-binary  # PostgreSQL 驅動
uv add sqlite3       # Python 內建輕量級資料庫

# 快取與分佈式存儲
uv add redis         # Redis 客戶端
uv add redis-py      # 另一個 Redis 客戶端選項
```

### **代理管理與輪換**

```bash
# 代理發現與驗證
uv add proxybroker           # 查找/驗證代理
uv add rotating-proxies      # 代理輪換中間件
uv add requests[socks]       # SOCKS 代理支援
uv add PySocks              # SOCKS 協議支援

# 自研智能驗證系統 (無需額外依賴)
# 基於 aiohttp + asyncio 實現
```

### **反檢測與隱匿技術**

```bash
# User-Agent 與指紋模擬
uv add fake-useragent           # 輪換 User-Agent
uv add python-random-user-agent # 另一種 UA 輪換方案
uv add tls-client              # 模擬 TLS 指紋
uv add curl_cffi               # 通過 cURL impersonate 模擬瀏覽器指紋
```

### **並發處理與工具**

```bash
# 異步文件操作
uv add aiofiles  # 異步文件 I/O

# 資料分析與處理
uv add pandas  # 資料分析與處理
uv add numpy   # 數值計算

# 重試機制與容錯
uv add tenacity  # 現代重試庫 (推薦)
uv add retrying  # 傳統重試庫

# 進度追蹤與工具
uv add tqdm              # 進度條
uv add python-dateutil   # 日期時間處理
```

### **監控與指標**

```bash
# 監控指標導出
uv add prometheus-client  # Prometheus 指標收集

# 結構化日誌 (已在核心技術棧中)
# loguru - 現代化日誌系統
```

### **配置管理與環境**

```bash
# 環境變數管理
uv add python-dotenv  # .env 檔案支援

# 命令列界面
uv add click   # 創建 CLI 工具
uv add typer   # 現代 CLI 框架
```

## **JavaScript 渲染相關**

### **需要安裝的軟體**

1. ChromeDriver \- 用於 Selenium  
2. Node.js \- 用於某些 JavaScript 執行環境

### **Python 包**

`bash`

`pip install webdriver-manager`

`pip install undetected-chromedriver`

## **完整的 requirements.txt (基於最新架構)**

```txt
# ===== 核心技術棧 (必需) =====
# 異步框架與 HTTP 客戶端
aiohttp==3.9.1          # 高性能異步 HTTP 客戶端
httpx==0.25.2            # 現代異步/同步 HTTP 庫
requests==2.31.0         # 傳統穩定的同步 HTTP 客戶端
urllib3==2.1.0           # 底層 HTTP 庫

# 資料模型與驗證
pydantic==2.5.0          # 資料驗證與設置管理 (強烈推薦)

# 日誌系統
loguru==0.7.2            # 結構化、用戶友好的日誌記錄

# ===== HTML/XML 解析與資料提取 =====
# HTML 解析引擎
lxml==4.9.3              # 極速解析，XPath 支援，生產環境首選
beautifulsoup4==4.12.2   # 簡單易用，開發測試友好
parsel==1.8.1            # Scrapy 選擇器庫，整合 XPath 和 CSS

# HTML to Markdown 轉換 (核心功能)
markdownify==0.11.6      # 簡單易用的轉換器
html2text==2020.1.16     # 功能豐富的轉換工具
readability-lxml==0.8.1  # Mozilla Readability 算法
newspaper3k==0.2.8       # 新聞文章提取與轉換
trafilatura==1.6.0       # 網頁內容提取專家

# ===== 瀏覽器自動化 (反檢測技術) =====
# 現代瀏覽器自動化
playwright==1.40.0       # 微軟出品，性能優異 (推薦)

# 傳統瀏覽器自動化
selenium==4.15.2         # 業界標準
undetected-chromedriver==3.5.5  # 繞過 Cloudflare 等檢測
webdriver-manager==4.0.1 # 自動管理瀏覽器驅動

# 全功能爬蟲框架
scrapy==2.11.0           # 異步，高併發，業界標準框架
scrapy-playwright==0.0.28  # Scrapy + Playwright 集成

# ===== 資料庫與快取系統 =====
# 關聯式資料庫
sqlalchemy==2.0.23       # ORM 框架
psycopg2-binary==2.9.9   # PostgreSQL 驅動

# 快取與分佈式存儲
redis==5.0.1             # Redis 客戶端

# ===== 代理管理與輪換 =====
# 代理發現與驗證
proxybroker==0.3.2       # 查找/驗證代理
rotating-proxies==0.6.2  # 代理輪換中間件
PySocks==1.7.1           # SOCKS 協議支援

# ===== 反檢測與隱匿技術 =====
# User-Agent 與指紋模擬
fake-useragent==1.4.0    # 輪換 User-Agent
python-random-user-agent==1.0.1  # 另一種 UA 輪換方案
tls-client==0.2.2        # 模擬 TLS 指紋
curl-cffi==0.5.10        # cURL impersonate 模擬瀏覽器指紋

# ===== 並發處理與工具 =====
# 異步文件操作
aiofiles==23.2.1         # 異步文件 I/O

# 資料分析與處理
pandas==2.1.3            # 資料分析與處理
numpy==1.26.2            # 數值計算

# 重試機制與容錯
tenacity==8.2.3          # 現代重試庫 (推薦)
retrying==1.3.4          # 傳統重試庫

# 進度追蹤與工具
tqdm==4.66.1             # 進度條
python-dateutil==2.8.2   # 日期時間處理

# ===== 監控與指標 =====
# 監控指標導出
prometheus-client==0.19.0  # Prometheus 指標收集

# ===== 配置管理與環境 =====
# 環境變數管理
python-dotenv==1.0.0     # .env 檔案支援

# 命令列界面
click==8.1.7             # 創建 CLI 工具
typer==0.9.0             # 現代 CLI 框架

# ===== 其他核心依賴 =====
certifi==2023.11.17      # SSL 憑證
charset-normalizer==3.3.2  # 字符編碼檢測
idna==3.4                # 國際化域名
```

`# 其他`  
`urllib3==2.1.0`  
`certifi==2023.11.17`  
`charset-normalizer==3.3.2`

`idna==3.4`

## **瀏覽器驅動設置**

### **自動安裝 ChromeDriver**

`python`

`from webdriver_manager.chrome import ChromeDriverManager`  
`from selenium import webdriver`

`driver = webdriver.Chrome(ChromeDriverManager().install())`

### **或者手動下載**

1. 下載對應版本的 ChromeDriver  
2. 添加到系統 PATH 或指定路徑

## **項目結構建議的依賴**

### **通用工具類 ([utils.py](https://utils.py/))**

`python`

`import requests`  
`from bs4 import BeautifulSoup`  
`from selenium import webdriver`  
`from selenium.webdriver.common.by import By`  
`from selenium.webdriver.support.ui import WebDriverWait`  
`from selenium.webdriver.support import expected_conditions as EC`  
`import pandas as pd`  
`import asyncio`  
`import aiohttp`  
`from fake_useragent import UserAgent`  
`from datetime import datetime`  
`import logging`  
`from loguru import logger`

`import time`

### **代理驗證模組**

`python`

`from proxy_checker import ProxyChecker`

`import socket`

## **安裝指令**

### **推薦方式 - 使用 uv 包管理器：**

```bash
# 創建虛擬環境
uv venv

# 啟動虛擬環境
uv shell

# 安裝所有依賴
uv pip install -r requirements.txt

# 或者逐步安裝核心依賴
uv add aiohttp httpx pydantic lxml beautifulsoup4 loguru
uv add markdownify html2text trafilatura playwright
uv add scrapy tenacity fake-useragent proxybroker
```

### **傳統方式 - 使用 pip：**

```bash
# 使用 requirements.txt
pip install -r requirements.txt

# 或一次性安裝核心依賴
pip install aiohttp httpx pydantic lxml beautifulsoup4 loguru markdownify html2text trafilatura playwright scrapy tenacity fake-useragent proxybroker
```

### **瀏覽器驅動安裝：**

```bash
# Playwright 瀏覽器安裝
playwright install chromium

# Selenium WebDriver 自動管理（已包含在依賴中）
# webdriver-manager 會自動下載所需驅動
```

## **注意事項**

### **環境需求：**
1. **Python 版本：** 建議使用 Python 3.11+ 以確保最佳性能和兼容性
2. **包管理器：** 優先使用 `uv` 進行依賴管理，提供更快的安裝速度
3. **虛擬環境：** 強烈建議使用虛擬環境隔離專案依賴

### **瀏覽器與驅動：**
1. **Playwright：** 推薦使用，支援 Chromium、Firefox、WebKit
2. **Chrome 瀏覽器：** 使用 Selenium 或 undetected-chromedriver 時需要
3. **自動驅動管理：** webdriver-manager 會自動下載所需的瀏覽器驅動

### **系統依賴：**
1. **lxml：** 可能需要系統級的 libxml2 和 libxslt 庫
2. **Node.js：** 某些 JavaScript 渲染功能可能需要（可選）
3. **SSL 憑證：** 確保系統 SSL 憑證是最新的

### **效能與安全：**
1. **異步優先：** 優先使用 aiohttp、httpx 等異步庫提升效能
2. **代理驗證：** proxybroker 需要網路連線進行代理發現和驗證
3. **反檢測技術：** curl-cffi 和 tls-client 提供進階反檢測能力
4. **監控指標：** prometheus-client 用於生產環境監控

### **開發建議：**
1. **程式碼品質：** 使用 ruff 進行程式碼格式化和檢查
2. **類型提示：** 所有程式碼應包含完整的類型提示
3. **日誌記錄：** 使用 loguru 進行結構化日誌記錄
4. **配置管理：** 使用 python-dotenv 管理環境變數

## **總結**

這個完整的技術棧配置能夠滿足代理爬蟲與管理系統的所有需求：

### **核心能力：**
- **多源代理爬取：** 支援靜態頁面、JavaScript 動態內容、GitHub 專案等多種來源
- **HTML to Markdown 轉換：** 提供多種轉換引擎，適應不同內容格式
- **高效能異步處理：** 基於 asyncio 的現代異步架構
- **智能反檢測：** 整合多種反檢測技術，提升爬取成功率
- **完整監控體系：** 從日誌記錄到指標監控的全方位可觀測性

### **架構優勢：**
- **模組化設計：** 各功能模組獨立，易於維護和擴展
- **技術棧現代化：** 採用最新穩定版本，確保效能和安全性
- **開發友好：** 完整的開發工具鏈，支援程式碼品質保證
- **部署靈活：** 支援本地開發到生產環境的無縫部署

此配置為建構穩定、高效、可擴展的代理爬蟲系統提供了堅實的技術基礎。
