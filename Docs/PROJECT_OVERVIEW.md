# Proxy Crawler System - 專案總覽

## 專案簡介

本專案是一個基於 LLMFeeder 架構開發的代理伺服器爬蟲系統，目標是從指定網址抓取proxy資料。系統採用模組化設計，具有高效能、可擴展性和易用性。

## 技術架構

### 核心設計理念

參考 LLMFeeder 專案的架構設計，採用以下核心原則：

1. **模組化設計**: 每個爬蟲都是獨立的模組，易於維護和擴展
2. **統一的基礎類別**: 所有爬蟲都繼承自`BaseCrawler`，確保一致性
3. **錯誤處理機制**: 完善的錯誤處理和重試機制
4. **日誌記錄**: 詳細的操作日誌，便於除錯和監控
5. **資料格式統一**: 統一的資料結構和輸出格式

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Proxy Crawler System                             │
│                        (基於 LLMFeeder 架構設計)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  應用層 (Application Layer)                                                │
│  ├── Main Program (main.py) - 主程式入口                                  │
│  ├── ProxyCrawlerSystem - 系統協調器                                       │
│  ├── REST API Service - RESTful API 服務 (FastAPI)                       │
│  ├── Web Management Interface - Web 管理界面                              │
│  └── CLI Interface - 命令列介面 (typer/click)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  核心業務層 (Core Business Layer)                                          │
│  ├── 爬蟲模組 (Crawler Module)                                             │
│  │   ├── BaseCrawler - 基礎爬蟲類別                                        │
│  │   ├── Anti-Detection Engine - 反檢測引擎                               │
│  │   │   ├── User-Agent Manager - UA 管理器                              │
│  │   │   ├── TLS Fingerprint Simulator - TLS 指紋模擬                    │
│  │   │   └── Request Pattern Randomizer - 請求模式隨機化                  │
│  │   ├── Data Extraction Engine - 資料提取引擎                            │
│  │   │   ├── CSS Selector Engine - CSS 選擇器引擎                        │
│  │   │   ├── XPath Engine - XPath 引擎                                   │
│  │   │   └── Regex Pattern Matcher - 正則表達式匹配器                    │
│  │   └── Browser Automation - 瀏覽器自動化                               │
│  │       ├── Playwright Integration - Playwright 整合                    │
│  │       ├── Selenium WebDriver - Selenium 驅動                          │
│  │       └── Undetected Chrome - 反檢測 Chrome                          │
│  ├── 代理管理模組 (Proxy Manager Module)                                   │
│  │   ├── ProxyManager - 代理管理器                                         │
│  │   ├── ProxyValidator - 智能驗證系統                                     │
│  │   │   ├── Connectivity Checker - 連通性檢查器                          │
│  │   │   ├── Speed Tester - 速度測試器                                    │
│  │   │   ├── Anonymity Validator - 匿名性驗證器                          │
│  │   │   └── Geographic Detector - 地理位置檢測器                        │
│  │   ├── Pool Management - 代理池管理                                     │
│  │   │   ├── Hot Pool - 熱池 (高性能代理)                                │
│  │   │   ├── Warm Pool - 溫池 (中等性能代理)                             │
│  │   │   ├── Cold Pool - 冷池 (低性能代理)                               │
│  │   │   └── Blacklist - 黑名單 (失效代理)                               │
│  │   ├── Performance Monitoring - 性能監控                                │
│  │   │   ├── Response Time Tracker - 響應時間追蹤                        │
│  │   │   ├── Success Rate Monitor - 成功率監控                           │
│  │   │   └── Geographic Distribution - 地理分佈統計                      │
│  │   └── Intelligent Scoring - 智能評分系統                               │
│  │       ├── Performance Score - 性能評分                                │
│  │       ├── Reliability Score - 可靠性評分                              │
│  │       └── Composite Score - 綜合評分                                  │
│  ├── 資料處理模組 (Data Processing Module)                                 │
│  │   ├── ETL Pipeline - ETL 流程引擎                                       │
│  │   │   ├── Data Extractor - 資料提取器                                 │
│  │   │   ├── Data Transformer - 資料轉換器                               │
│  │   │   └── Data Loader - 資料載入器                                    │
│  │   ├── Data Validation - 資料驗證器                                      │
│  │   │   ├── Schema Validator - 結構驗證器                               │
│  │   │   ├── Format Checker - 格式檢查器                                 │
│  │   │   └── Business Rule Validator - 業務規則驗證器                    │
│  │   ├── DataStorage - 格式化輸出                                          │
│  │   │   ├── Markdown Exporter - Markdown 匯出器                        │
│  │   │   ├── JSON Exporter - JSON 匯出器                                │
│  │   │   ├── CSV Exporter - CSV 匯出器                                   │
│  │   │   └── Database Persister - 資料庫持久化                           │
│  │   └── Report Generator - 報告生成器                                    │
│  │       ├── Summary Report - 摘要報告                                   │
│  │       ├── Performance Report - 性能報告                               │
│  │       └── Statistical Analysis - 統計分析                             │
│  ├── HTML to Markdown 轉換模組 (HTML to Markdown Converter)               │
│  │   ├── Multi-Engine Converter - 多引擎轉換器                            │
│  │   │   ├── Markdownify Engine - Markdownify 引擎                      │
│  │   │   ├── Html2text Engine - Html2text 引擎                          │
│  │   │   ├── Trafilatura Engine - Trafilatura 引擎                      │
│  │   │   └── TurndownService Engine - TurndownService 引擎              │
│  │   ├── Content Cleaning Engine - 內容清理引擎                           │
│  │   │   ├── HTML Sanitizer - HTML 清理器                               │
│  │   │   ├── Noise Remover - 雜訊移除器                                  │
│  │   │   └── Structure Optimizer - 結構優化器                            │
│  │   ├── Smart Content Extractor - 智能提取器                             │
│  │   │   ├── Main Content Detector - 主要內容檢測器                      │
│  │   │   ├── Table Extractor - 表格提取器                                │
│  │   │   └── List Extractor - 列表提取器                                 │
│  │   └── Quality Assurance - 品質保證                                     │
│  │       ├── Conversion Validator - 轉換驗證器                           │
│  │       ├── Format Checker - 格式檢查器                                 │
│  │       └── Content Integrity Checker - 內容完整性檢查器                │
│  └── 配置管理模組 (Configuration Module)                                   │
│      ├── Environment Config - 環境設定                                     │
│      │   ├── Development Config - 開發環境配置                           │
│      │   ├── Production Config - 生產環境配置                            │
│      │   └── Testing Config - 測試環境配置                               │
│      ├── Crawler Parameters - 爬蟲參數                                     │
│      │   ├── Request Settings - 請求設定                                 │
│      │   ├── Retry Policies - 重試策略                                   │
│      │   └── Rate Limiting - 頻率限制                                    │
│      ├── Validation Rules - 驗證規則                                       │
│      │   ├── Proxy Validation Rules - 代理驗證規則                       │
│      │   ├── Data Quality Rules - 資料品質規則                           │
│      │   └── Business Logic Rules - 業務邏輯規則                         │
│      └── Security Settings - 安全設定                                     │
│          ├── API Key Management - API 金鑰管理                           │
│          ├── Access Control - 存取控制                                   │
│          └── Encryption Settings - 加密設定                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  個別爬蟲層 (Individual Crawlers Layer)                                    │
│  ├── SSLProxiesOrgCrawler - sslproxies.org 爬蟲                           │
│  └── GeonodeCrawler - geonode.com 爬蟲                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  基礎設施層 (Infrastructure Layer)                                         │
│  ├── Database Layer - 資料庫層                                            │
│  │   ├── PostgreSQL - 主要資料庫 (代理資料、統計資料)                     │
│  │   ├── Redis - 快取系統 (代理池快取、會話管理)                          │
│  │   └── SQLite - 輕量級存儲 (開發環境、測試資料)                         │
│  ├── Network Layer - 網路層                                               │
│  │   ├── Async HTTP Clients - 異步 HTTP 客戶端                           │
│  │   │   ├── aiohttp - 主要異步 HTTP 庫                                  │
│  │   │   ├── httpx - 現代 HTTP 客戶端                                    │
│  │   │   └── requests - 同步 HTTP 庫 (向後兼容)                          │
│  │   ├── Connection Pool - 連接池管理                                     │
│  │   ├── SSL/TLS Handler - SSL/TLS 處理器                                │
│  │   └── Proxy Rotation - 代理輪換機制                                   │
│  ├── Logging System - 日誌系統                                           │
│  │   ├── Structured Logging - 結構化日誌 (loguru)                        │
│  │   ├── Log Aggregation - 日誌聚合                                      │
│  │   ├── Log Rotation - 日誌輪轉                                         │
│  │   └── Error Tracking - 錯誤追蹤                                       │
│  ├── Monitoring & Metrics - 監控與指標收集                                │
│  │   ├── Performance Metrics - 性能指標 (prometheus-client)               │
│  │   ├── Health Checks - 健康檢查                                        │
│  │   ├── Alerting System - 告警系統                                      │
│  │   └── Dashboard Integration - 儀表板整合                               │
│  ├── Security Layer - 安全層                                             │
│  │   ├── Authentication - 身份驗證                                       │
│  │   ├── Authorization - 授權管理                                        │
│  │   ├── Data Encryption - 資料加密                                      │
│  │   └── Audit Logging - 審計日誌                                        │
│  └── Deployment & Orchestration - 部署與編排                             │
│      ├── Docker Containers - Docker 容器                                 │
│      ├── Docker Compose - 服務編排                                       │
│      ├── Kubernetes Support - Kubernetes 支援 (未來)                     │
│      └── CI/CD Pipeline - 持續整合/部署管道                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 資料流向圖

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   網站數據源    │    │   GitHub 倉庫   │    │   配置文件      │
│                 │    │                 │    │                 │
│ • sslproxies.   │    │                 │    │ • crawler_      │
│   org           │    │                 │    │   config.yaml   │
│ • geonode.com   │    │                 │    │ • validation_   │
│                 │    │                 │    │   rules.yaml    │
│                 │    │                 │    │ • output_       │
│                 │    │                 │    │   format.yaml   │
│                 │    │                 │    │ • security_     │
│                 │    │                 │    │   settings.yaml │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    個別爬蟲模組                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Web Crawler │  │ API Crawler │  │ File Crawler│            │
│  │             │  │             │  │             │            │
│  │ • Playwright│  │ • aiohttp   │  │ • requests  │            │
│  │ • Selenium  │  │ • httpx     │  │ • urllib3   │            │
│  │ • requests  │  │ • asyncio   │  │ • aiofiles  │            │
│  │ • lxml/bs4  │  │ • pydantic  │  │ • json      │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    反檢測與驗證層                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ User-Agent  │  │ TLS 指紋    │  │ 請求模式    │            │
│  │ 智能管理    │  │ 模擬系統    │  │ 隨機化      │            │
│  │             │  │             │  │             │            │
│  │ • 動態輪換  │  │ • curl_cffi │  │ • 頻率控制  │            │
│  │ • 成功率追蹤│  │ • tls-client│  │ • 延遲隨機  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    代理驗證與評分系統                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ 連通性檢查  │  │ 速度測試    │  │ 匿名性驗證  │            │
│  │             │  │             │  │             │            │
│  │ • 多端點測試│  │ • 響應時間  │  │ • IP 洩漏檢測│            │
│  │ • 超時處理  │  │ • 吞吐量測試│  │ • 地理位置  │            │
│  │ • 重試機制  │  │ • 穩定性評估│  │ • 協議支援  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    資料處理與轉換層                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ ETL Pipeline│  │ 資料驗證    │  │ HTML to MD  │            │
│  │             │  │             │  │ 轉換引擎    │            │
│  │ • 提取器    │  │ • Schema    │  │             │            │
│  │ • 轉換器    │  │ • 格式檢查  │  │ • 多引擎支援│            │
│  │ • 載入器    │  │ • 業務規則  │  │ • 內容清理  │            │
│  │ • 錯誤處理  │  │ • 品質保證  │  │ • 智能提取  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    代理池管理與智能分類                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ 動態池管理  │  │ 智能評分    │  │ 自動分類    │            │
│  │             │  │             │  │             │            │
│  │ • 熱池      │  │ • 性能評分  │  │ • 地理分佈  │            │
│  │ • 溫池      │  │ • 可靠性評分│  │ • 協議類型  │            │
│  │ • 冷池      │  │ • 綜合評分  │  │ • 用途分類  │            │
│  │ • 黑名單    │  │ • 動態調整  │  │ • 品質等級  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    多格式輸出與存儲層                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Markdown    │  │ 結構化資料  │  │ 資料庫      │            │
│  │ 表格輸出    │  │ 輸出        │  │ 持久化      │            │
│  │             │  │             │  │             │            │
│  │ • 時間戳    │  │ • JSON 報告 │  │ • PostgreSQL│            │
│  │ • 統計摘要  │  │ • CSV 匯出  │  │ • Redis 快取│            │
│  │ • 品質指標  │  │ • XML 格式  │  │ • SQLite    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    監控、日誌與告警系統                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ 性能監控    │  │ 結構化日誌  │  │ 智能告警    │            │
│  │             │  │             │  │             │            │
│  │ • Prometheus│  │ • loguru    │  │ • 閾值監控  │            │
│  │ • 健康檢查  │  │ • 錯誤追蹤  │  │ • 異常檢測  │            │
│  │ • 儀表板    │  │ • 審計日誌  │  │ • 通知系統  │            │
│  │ • 統計分析  │  │ • 日誌輪轉  │  │ • 報告生成  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API 與管理介面                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ REST API    │  │ Web 管理    │  │ CLI 工具    │            │
│  │ (FastAPI)   │  │ 介面        │  │             │            │
│  │             │  │             │  │ • typer     │            │
│  │ • 身份驗證  │  │ • 即時監控  │  │ • click     │            │
│  │ • 授權管理  │  │ • 配置管理  │  │ • 批次操作  │            │
│  │ • API 文檔  │  │ • 報告查看  │  │ • 腳本整合  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## 功能特色

### 1. 多來源爬取

- 支援多個代理來源（SSL Proxies、Geonode、GitHub 專案等）
- 整合 ProxyScraper 和三個 GitHub 代理專案
- 自動處理不同的 HTML 結構和資料格式
- 支援 HTTP、SOCKS4、SOCKS5 等多種協議

### 2. 代理輪換機制

- 自動代理輪換避免被封鎖
- 失敗代理自動標記和排除
- 支援隨機和順序輪換模式

### 3. 代理驗證系統

- 多執行緒並行驗證
- 多個測試 URL 確保準確性
- 速度測試和效能評估

### 4. 資料儲存

- 支援 Markdown、JSON、CSV 格式
- 自動時間戳記檔案命名
- 綜合報告生成

### 5. 錯誤處理

- 完善的異常處理機制
- 自動重試和降級策略
- 詳細的錯誤日誌記錄

## 檔案結構

```
JasonSpider/
├── src/                                 # 源代碼目錄
│   ├── __init__.py                      # 套件初始化
│   ├── main.py                          # 主程式入口 (FastAPI 應用)
│   ├── html_to_markdown/                # HTML to Markdown 轉換模組
│   │   ├── __init__.py                  # 模組初始化
│   │   ├── core.py                      # 核心轉換邏輯
│   │   ├── converters.py                # 轉換器實現
│   │   ├── api_server.py                # API 服務器
│   │   └── adapters.py                  # 適配器模組
│   └── proxy_manager/                   # 代理管理模組
│       ├── __init__.py                  # 模組初始化
│       ├── server.py                    # 代理管理服務器
│       ├── database_config.py           # 資料庫配置
│       └── README.md                    # 模組說明
├── Docs/                                # 專案文檔
│   ├── PROJECT_OVERVIEW.md              # 專案總覽
│   ├── 架構設計總覽.md                   # 架構設計文檔
│   ├── ProxyScraper整合分析與建議.md     # ProxyScraper 整合分析
│   ├── 三個GitHub代理專案分析與整合建議.md # GitHub 專案分析
│   └── 其他技術文檔...                   # 其他相關文檔
├── data/                                # 資料目錄
│   ├── processed/                       # 處理後的資料
│   ├── proxy_manager/                   # 代理管理資料
│   ├── raw/                             # 原始資料
│   └── transformed/                     # 轉換後的資料
├── docker/                              # Docker 相關檔案
│   └── html-to-markdown/                # HTML to Markdown Docker 配置
├── check_proxy_websites.py              # 代理網站檢查工具
├── requirements.txt                     # 主要依賴清單
├── requirements_html_to_markdown.txt    # HTML to Markdown 專用依賴
├── pyproject.toml                       # 專案配置檔案
├── Dockerfile                           # Docker 容器配置
├── docker-compose.yml                   # Docker Compose 配置
├── .env.example                         # 環境變數範例
├── .env                                 # 環境變數配置 (本地)
└── README.md                           # 專案說明文件
```

### 檔案命名規範

- **Python 模組**: 使用 `snake_case.py` 格式
- **爬蟲檔案**: 使用 `{source_website}__proxy_crawler__.py` 格式 (未來實現)
- **配置檔案**: 使用 `snake_case.yaml` 或 `snake_case.toml` 格式
- **輸出檔案**: 使用 `{source_website}_{timestamp}_1000proxies.md` 格式
- **目錄命名**: 使用 `kebab-case` 或 `snake_case` 格式

## 使用方式

### 1. 快速開始

```bash
# 設置虛擬環境 (推薦使用 uv)
uv venv
uv shell

# 安裝依賴
uv sync
# 或使用 pip
pip install -r requirements.txt

# 啟動 FastAPI 應用
python src/main.py

# 或使用 uvicorn 直接啟動
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Docker 部署

```bash
# 使用 Docker Compose 啟動
docker-compose up -d

# 或單獨構建和運行
docker build -t jason-spider .
docker run -p 8000:8000 jason-spider
```

### 3. HTML to Markdown 轉換服務

```bash
# 啟動轉換服務 (包含在主應用中)
curl -X POST "http://localhost:8000/convert" \
     -H "Content-Type: application/json" \
     -d '{"html": "<h1>Hello World</h1>", "engine": "markdownify"}'
```

### 3. 示範程式

```bash
# 執行示範程式
python demo.py
```

## 輸出範例

### Markdown 輸出

```markdown
# free_proxy_list_net - 抓取時間: 2023-12-01 14:30:00

總共抓取到 1000 個代理伺服器

| IP Address  | Port | Protocol | Country | Speed | Anonymity | Last Checked | Status     |
| ----------- | ---- | -------- | ------- | ----- | --------- | ------------ | ---------- |
| 192.168.1.1 | 8080 | HTTP     | US      | 1.2s  | Anonymous | 2023-12-01   | ✅ Working |
| 10.0.0.1    | 3128 | HTTPS    | DE      | 0.8s  | Elite     | 2023-12-01   | ✅ Working |
```

### 綜合報告

系統會自動生成綜合報告，包含：

- 各來源統計資訊
- 總體可用率
- 詳細代理列表
- 效能統計

## 技術特點

### 核心架構特色
- **基於 LLMFeeder 架構**: 採用現代化的網頁內容提取與處理架構，專為 AI 上下文優化
- **分層式設計**: 應用層、核心業務層、個別爬蟲層、基礎設施層的清晰分離
- **模組化架構**: 高內聚低耦合的模組設計，支援獨立開發與測試

### 性能與可靠性
- **高效能異步處理**: 基於 `asyncio` + `aiohttp`/`httpx` 的異步架構
- **智能代理池管理**: 熱/溫/冷/黑名單四級分類管理系統
- **反檢測技術**: 整合多種反檢測策略，包括 User-Agent 輪換、TLS 指紋模擬
- **容錯與重試**: 內建智能重試機制和錯誤恢復策略

### 資料處理能力
- **HTML to Markdown 轉換**: 多引擎轉換器支援 (markdownify, html2text, TurndownService)
- **智能內容提取**: 基於 CSS 選擇器和 XPath 的精確資料提取
- **ETL 流程引擎**: 完整的資料清理、驗證、標準化流程
- **多格式輸出**: 支援 Markdown、JSON、CSV 等多種輸出格式

### 監控與管理
- **實時性能監控**: 代理響應時間、成功率、地理位置等指標追蹤
- **Web 管理界面**: 直觀的代理池狀態管理和統計面板
- **結構化日誌**: 基於 `loguru` 的現代化日誌系統
- **RESTful API**: 完整的 API 服務支援外部整合

### 技術棧整合
- **現代 Python 生態**: Python 3.11+, `uv` 包管理, `pydantic` 資料驗證
- **高性能網路庫**: `aiohttp`, `httpx`, `requests` 的最佳實踐組合
- **專業爬蟲工具**: `beautifulsoup4`, `lxml`, `parsel` 的多引擎支援
- **容器化部署**: Docker + Docker Compose 的完整部署方案

## 注意事項

1. **遵守網站規則**: 請遵守各網站的 robots.txt 和使用條款
2. **請求頻率**: 系統已內建請求延遲，避免對目標網站造成過大負載
3. **代理品質**: 免費代理的品質和可用性可能不穩定
4. **法律合規**: 請確保使用符合當地法律法規

## 未來改進

### 短期目標 (1-3 個月)
- **智能代理評分系統**: 基於響應時間、穩定性、匿名性的綜合評分
- **Web 管理界面優化**: 實時監控面板、代理池狀態視覺化
- **API 服務擴展**: RESTful API 的完整 CRUD 操作支援
- **配置熱重載**: 無需重啟的動態配置更新機制

### 中期目標 (3-6 個月)
- **機器學習整合**: 基於歷史資料的代理品質預測模型
- **分散式爬取**: 多節點協同爬取，提升整體效能
- **智能反檢測**: AI 驅動的反檢測策略自動調整
- **資料分析面板**: 代理來源分析、地理分佈統計、趨勢預測

### 長期目標 (6-12 個月)
- **雲原生部署**: Kubernetes 支援，自動擴縮容
- **多協議支援**: SOCKS4/5、HTTP/HTTPS、透明代理的統一管理
- **商業化代理整合**: 付費代理服務的 API 整合
- **國際化支援**: 多語言界面，全球代理來源覆蓋

### 技術債務與優化
- **性能優化**: 記憶體使用優化、並發處理能力提升
- **測試覆蓋率**: 單元測試、整合測試、端到端測試的完整覆蓋
- **文檔完善**: API 文檔、部署指南、最佳實踐文檔
- **安全強化**: 資料加密、存取控制、審計日誌

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request 來改善這個專案。

---

**開發完成時間**: 2024 年 12 月  
**基於架構**: LLMFeeder  
**核心技術**: Python 3.11+, asyncio, aiohttp, pydantic, loguru  
**特色功能**: 智能代理池管理、HTML to Markdown 轉換、反檢測技術整合  
**部署方式**: Docker + Docker Compose 容器化部署

## 技術棧

### 核心技術棧
- **程式語言**: Python 3.11+
- **包管理器**: `uv` (主要) / `pip` (備用)
- **異步框架**: `asyncio` + `aiohttp` / `httpx`
- **資料模型**: `pydantic` (驗證) + `dataclasses` (輕量級)
- **日誌系統**: `loguru` (結構化日誌)

### HTTP 客戶端與網路
- **異步 HTTP**: `aiohttp`, `httpx` (現代首選)
- **同步 HTTP**: `requests` (傳統穩定)
- **底層網路**: `urllib3`

### HTML/XML 解析與資料提取
- **HTML 解析**: `beautifulsoup4` (易用), `lxml` (高性能)
- **選擇器引擎**: `parsel` (XPath + CSS)
- **HTML to Markdown**: `markdownify`, `html2text`, `TurndownService`

### 瀏覽器自動化 (反檢測)
- **現代方案**: `playwright` (微軟出品，性能優異)
- **傳統方案**: `selenium` + `undetected-chromedriver`
- **反檢測技術**: `fake-useragent`, `tls-client`, `curl_cffi`

### 資料庫與快取
- **關聯式資料庫**: `PostgreSQL` + `sqlalchemy`
- **快取系統**: `Redis` + `redis-py`
- **輕量級存儲**: `sqlite3`

### 代理管理與輪換
- **代理發現**: `proxybroker`
- **代理輪換**: `rotating-proxies`
- **智能驗證**: 自研驗證系統

### 開發工具與品質保證
- **程式碼格式化**: `ruff format`
- **程式碼檢查**: `ruff check`
- **測試框架**: `pytest`
- **類型檢查**: `mypy`
- **配置管理**: `python-dotenv`

### 部署與監控
- **容器化**: `Docker` + `Docker Compose`
- **監控指標**: `prometheus-client`
- **進度追蹤**: `tqdm`
- **重試機制**: `tenacity`

### 版本控制與協作
- **版本控制**: `Git`
- **提交規範**: Conventional Commits
- **分支策略**: Feature Branch Workflow
