# Dependencies (Proxy Crawler Project)

本文件列出專案依賴分類、對應安裝方式、以及已鎖定版本示例 (requirements.txt)。同時提供瀏覽器自動化與環境建議，協助快速、可重現地建置開發/生產環境。

## 1. Python 分類依賴 (按功能模組)

### 1.1 Core

```bash
# 異步框架與 HTTP 客戶端 (現代首選)
uv add aiohttp
uv add httpx
uv add asyncio

# 資料模型與驗證
uv add pydantic

# 日誌系統
uv add loguru

# 傳統同步 HTTP (備用)
uv add requests
uv add urllib3
```

### 1.2 HTML / XML 解析與內容抽取

```bash
uv add lxml
uv add beautifulsoup4
uv add parsel

# HTML → Markdown / 文章正文抽取
uv add markdownify html2text readability-lxml newspaper3k trafilatura
```

### 1.3 瀏覽器自動化與反爬

```bash
# 現代瀏覽器自動化
uv add playwright

# 傳統方案與驅動管理
uv add selenium undetected-chromedriver webdriver-manager

# 全功能爬蟲框架與整合
uv add scrapy scrapy-playwright
```

### 1.4 資料庫與快取

```bash
uv add sqlalchemy psycopg2-binary sqlite3
uv add redis redis-py
```

### 1.5 代理輔助與輪換 (可選)

```bash
uv add proxybroker rotating-proxies requests[socks] PySocks
```

### 1.6 反檢測與指紋模擬 (可選)

```bash
uv add fake-useragent python-random-user-agent tls-client curl_cffi
```

### 1.7 並發工具與實用程式

```bash
uv add aiofiles pandas numpy
uv add tenacity retrying
uv add tqdm python-dateutil
```

### 1.8 監控與指標

```bash
uv add prometheus-client
```

### 1.9 配置與 CLI

```bash
uv add python-dotenv click typer
```

### 1.10 其他 (間接依賴說明)

如 urllib3、certifi、charset-normalizer、idna 等為傳遞依賴，通常不需手動列出；供應鏈審計可使用：

```bash
uv pip list
uv export --format=requirements-txt > lock.txt
```

## 2. JavaScript / 瀏覽器執行環境

### 2.1 必要工具

1. Chrome / Chromium (Playwright 可自動安裝)
2. Node.js (僅在需要 JS 執行 / Playwright 安裝瀏覽器時使用)

### 2.2 補充 Python 安裝指令

```bash
pip install webdriver-manager undetected-chromedriver
```

## 3. 已鎖定版本示例 (requirements.txt)

下列版本示例對應當前專案歷史；實際生產請依 CI 測試結果定期調整：

```txt
# ===== 核心技術棧 =====
aiohttp==3.9.1
httpx==0.25.2
requests==2.31.0
urllib3==2.1.0
pydantic==2.5.0
loguru==0.7.2

# ===== HTML/XML 解析與資料提取 =====
lxml==4.9.3
beautifulsoup4==4.12.2
parsel==1.8.1
markdownify==0.11.6
html2text==2020.1.16
readability-lxml==0.8.1
newspaper3k==0.2.8
trafilatura==1.6.0

# ===== 瀏覽器自動化與反檢測 =====
playwright==1.40.0
selenium==4.15.2
undetected-chromedriver==3.5.5
webdriver-manager==4.0.1
scrapy==2.11.0
scrapy-playwright==0.0.28

# ===== 資料庫與快取 =====
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1

# ===== 代理管理與輪換 =====
proxybroker==0.3.2
rotating-proxies==0.6.2
PySocks==1.7.1

# ===== 反檢測與隱匿技術 =====
fake-useragent==1.4.0
python-random-user-agent==1.0.1
tls-client==0.2.2
curl-cffi==0.5.10

# ===== 並發處理與工具 =====
aiofiles==23.2.1
pandas==2.1.3
numpy==1.26.2
tenacity==8.2.3
retrying==1.3.4
tqdm==4.66.1
python-dateutil==2.8.2

# ===== Monitoring =====
prometheus-client==0.19.0

# ===== 配置管理與環境 =====
python-dotenv==1.0.0
click==8.1.7
typer==0.9.0

# ===== 其他核心依賴 =====
certifi==2023.11.17
charset-normalizer==3.3.2
idna==3.4
```

## 4. WebDriver 安裝

### 4.1 自動安裝 (webdriver-manager)

```python
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver

driver = webdriver.Chrome(ChromeDriverManager().install())
```

### 4.2 手動安裝步驟

1. 下載對應版本 ChromeDriver
2. 加入系統 PATH (或程式內指定 executable_path)

## 5. 建議匯入 (樣例)

```python
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import asyncio
import aiohttp
from fake_useragent import UserAgent
from datetime import datetime
import logging
from loguru import logger
import time
```

### 5.1 代理驗證模組樣例

```python
from proxy_checker import ProxyChecker
import socket
```

## 6. 安裝指令

### 6.1 使用 uv (推薦)

```bash
uv venv
uv shell
uv pip install -r requirements.txt

# 或逐步添加核心依賴（分行列出避免續行符與可讀性下降）
uv add aiohttp httpx pydantic lxml beautifulsoup4 loguru
uv add markdownify html2text trafilatura playwright
uv add scrapy tenacity fake-useragent proxybroker
```

### 6.2 使用 pip (傳統)

```bash
pip install -r requirements.txt
pip install aiohttp httpx pydantic lxml beautifulsoup4 loguru
pip install markdownify html2text trafilatura playwright scrapy
pip install tenacity fake-useragent proxybroker
```

### 6.3 Playwright 瀏覽器下載

```bash
playwright install chromium
```

## 7. 注意事項

### 7.1 環境需求

1. Python 3.11+（改進 asyncio 與效能）
2. 優先使用 uv（更快的解析與安裝）
3. 生產部署建議鎖定版本並啟用 CI 安全與相依掃描

### 7.2 系統/原生依賴

1. lxml 需 libxml2 / libxslt（Windows 由 wheels 提供）
2. Node.js 僅在需要瀏覽器自動化／JS 渲染時安裝
3. SSL 憑證需保持最新（避免請求失敗）

### 7.3 效能與安全

1. 優先使用異步 I/O（aiohttp/httpx）
2. 代理驗證需外部網路可用
3. 反檢測庫僅在必要情境啟用，避免額外維護負擔
4. 監控：Prometheus 指標 + 結構化日誌(loguru)

### 7.4 開發規範

1. 程式碼風格/靜態分析：ruff
2. 類型：全域啟用 typing（mypy / pyright）
3. 日誌：統一 loguru 封裝（避免混合 print / logging）
4. 配置：dotenv + pydantic Settings（避免硬編碼）

## 8. 總結

此依賴配置支援：

- 多來源代理爬取（靜態 / 動態 / 文章正文抽取）
- 異步高併發 + 重試與指標監控
- 反檢測與指紋模擬擴展
- 模組化與可觀測性（指標 + 日誌）

後續優化建議：導入可選 Redis / Postgres 持久化、分層快取策略、以及按功能劃分 extras（如 `.[crawler]`、`.[browser]`）。
