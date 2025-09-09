# JasonSpider - 代理爬蟲與管理系統

一個高效、可擴展的代理 IP 爬取、驗證和管理系統，具備完整的監控、優化和 API 功能。支援多來源代理獲取、HTML 轉 Markdown 服務，以及智能代理管理功能。

## 🚀 主要功能

### 1. HTML to Markdown 轉換服務

- 支援多種轉換引擎（markdownify、html2text、pandoc）
- RESTful API 介面
- 批量轉換支援
- 自動檔案儲存與時間戳記

### 2. 代理網站監控

- 多來源代理網站可用性檢查
- 支援 SSL Proxies、Geonode、GitHub 專案等
- 異步並發檢查機制
- 詳細的狀態報告

### 3. 智能代理管理系統 ✅

- **多來源代理獲取**：支援 ProxyScrape、GitHub、Shodan、Censys 等
- **智能代理池管理**：熱池、溫池、冷池、黑名單分類
- **代理驗證與評分**：多維度代理品質評估
- **多協議支援**：HTTP、HTTPS、SOCKS4、SOCKS5
- **地理位置分類**：基於 IP 的地理位置識別
- **自建代理探測器**：IP 範圍掃描、端口檢測、協議識別
- **API 配置管理**：安全的 API 金鑰管理系統

## 📁 專案結構

```
JasonSpider/
├── src/                                 # 源代碼目錄
│   ├── html_to_markdown/                # HTML to Markdown 轉換模組
│   ├── proxy_manager/                   # 代理管理模組
│   │   ├── manager.py                   # 核心代理管理器
│   │   ├── pools.py                     # 代理池管理
│   │   ├── fetchers.py                  # 代理獲取器
│   │   ├── advanced_fetchers.py         # 高級代理獲取器
│   │   ├── validators.py                # 代理驗證器
│   │   ├── scanner.py                   # 代理掃描器
│   │   ├── models.py                    # 數據模型
│   │   ├── config.py                    # 配置管理
│   │   └── api_config_manager.py        # API 配置管理
│   └── main.py                          # 主應用程序
├── JasonSpider-Dev/                     # 開發環境（自建探測器）
├── Docs/                                # 專案文檔
├── config/                              # 配置文件
├── data/                                # 資料目錄
├── docker/                              # Docker 相關檔案
├── check_proxy_websites.py              # 代理網站檢查工具
├── test_core_functionality.py           # 核心功能測試
├── test_censys_integration.py           # Censys 整合測試
├── setup_api_config.py                  # API 配置工具
└── requirements.txt                     # 依賴清單
```

## 🛠️ 安裝與使用

### 環境需求

- Python 3.11+
- 推薦使用 `uv` 進行依賴管理

### 快速開始

#### 🚀 簡化版 Docker 環境 (新手推薦)

如果您是新手或希望快速體驗系統功能，推薦使用簡化版配置：

```bash
# Windows PowerShell
.\start-simple.ps1

# 啟動後可以訪問：
# - 整合應用: http://localhost:8000
# - API 文檔: http://localhost:8000/docs
# - 系統狀態: http://localhost:8000/health
```

**簡化版特點：**
- 🎯 只需 2-3 個容器 (vs 完整版 7+ 個)
- 💾 記憶體使用降低 70% (~500MB vs ~2GB)
- ⚡ 啟動時間縮短 75% (~15秒 vs ~60秒)
- 🔧 維護複雜度大幅降低

#### 🔧 完整版 Docker 開發環境

如果您需要完整的微服務架構和所有功能：

```bash
# Windows PowerShell
.\start-dev.ps1

# 啟動後可以訪問：
# - 前端界面: http://localhost:3000
# - 主後端 API: http://localhost:8000
# - HTML 轉換服務: http://localhost:8001
# - pgAdmin: http://localhost:8080
# - Redis Commander: http://localhost:8081
```

詳細的 Docker 開發環境指南請參考：[DOCKER_DEV_README.md](DOCKER_DEV_README.md)

#### 📋 配置選擇指南

| 使用場景 | 推薦配置 | 資源需求 | 啟動時間 |
|---------|---------|---------|----------|
| 新手學習、快速測試 | 簡化版 | 低 (500MB) | 快 (15秒) |
| 開發調試、功能完整 | 完整版 | 中 (2GB) | 中 (60秒) |
| 生產部署 | 自定義 | 依需求 | 依配置 |

> 📚 **詳細開發環境指南**：請參閱 [`DEV_ENVIRONMENT.md`](./DEV_ENVIRONMENT.md) 獲取完整的 Docker 和本地開發環境設置說明。

#### 🏠 傳統本地環境設置

```bash
# 1. 克隆專案
git clone <repository-url>
cd JasonSpider

# 2. 設置虛擬環境（推薦使用 uv）
uv venv
uv shell

# 3. 安裝依賴
uv sync
# 或使用 pip
pip install -r requirements.txt

# 4. 配置 API 金鑰（可選）
python setup_api_config.py interactive

# 5. 測試核心功能
python test_core_functionality.py

# 6. 啟動服務（見下方速查指令與網址）
```

> 提示：現在只需在專案根目錄執行 `uv sync`，即可快速、可靠地建立與專案定義完全一致的 Python 開發環境，無需再關心複雜的 pip 與 venv 指令。這大幅簡化入門流程並保證環境一致性。

### Docker 部署

```bash
# 使用 Docker Compose 啟動所有服務（新插件語法）
docker compose up -d --build

# 停止並清理
docker compose down
```

## 🧭 啟動與存取網址速查

> 下列指令均在專案根目錄執行，除前端須先進入 `frontend`。

### 前端（Vite 開發伺服器）

```bash
cd frontend
npm ci
npm run dev
# 開啟瀏覽器存取
# http://127.0.0.1:5173
```

### 主後端 API（Port 8000）

```bash
uv run python run_server.py
# 健康檢查
# http://127.0.0.1:8000/health
# API 文件（Swagger）
# http://127.0.0.1:8000/docs
```

### ETL API（Port 8001）

> 注意：ETL API 的文件與健康檢查路徑與主後端不同。

```bash
uv run uvicorn src.etl.etl_api:etl_app --host 0.0.0.0 --port 8001 --log-level info
# 文件（Swagger）
# http://127.0.0.1:8001/etl/docs
# 健康檢查
# http://127.0.0.1:8001/api/etl/health
```

### 以 Docker 啟動（可選）

```bash
docker compose up -d --build
# 主後端: http://127.0.0.1:8000
# ETL API: http://127.0.0.1:8001 (文件與健康檢查同上)
# Redis: 6379（容器內部網路）
```

## 📖 API 使用

### URL2Parquet（新一代內容轉換管線）

URL2Parquet 是系統的核心功能，提供完整的網頁內容轉換和代理數據提取服務。

#### 基本使用

```bash
# 建立轉換任務（支援多 URL 和重定向處理）
curl -X POST "http://127.0.0.1:8000/api/url2parquet/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "urls": ["https://free-proxy-list.net/", "https://www.sslproxies.org/"],
       "output_formats": ["md", "json", "parquet", "csv"],
       "timeout_seconds": 30,
       "engine": "smart"
     }'

# 查詢任務狀態
curl "http://127.0.0.1:8000/api/url2parquet/jobs/<job_id>"

# 取得文件下載清單
curl "http://127.0.0.1:8000/api/url2parquet/jobs/<job_id>/download"

# 下載特定格式文件
curl "http://127.0.0.1:8000/api/url2parquet/jobs/<job_id>/files/parquet/download" \
     --output "output.parquet"
```

#### 重定向處理

```bash
# 當檢測到重定向時，確認並繼續處理
curl -X POST "http://127.0.0.1:8000/api/url2parquet/jobs/<job_id>/confirm-redirect" \
     -H "Content-Type: application/json" \
     -d '["https://redirected-url.com"]'
```

#### 本地文件管理

```bash
# 列出本地 Markdown 文件
curl "http://127.0.0.1:8000/api/url2parquet/local-md?work_dir=data/url2parquet"

# 讀取本地文件內容
curl "http://127.0.0.1:8000/api/url2parquet/local-md/content?filename=sample.md&work_dir=data/url2parquet"
```

### HTML to Markdown 轉換（舊版，建議使用 URL2Parquet）

```bash
# 基本轉換
curl -X POST "http://localhost:8000/convert" \
     -H "Content-Type: application/json" \
     -d '{"html": "<h1>Hello World</h1>", "engine": "markdownify"}'

# 批量轉換
curl -X POST "http://localhost:8000/batch-convert" \
     -H "Content-Type: application/json" \
     -d '{"items": [{"html": "<h1>Title 1</h1>"}, {"html": "<h2>Title 2</h2>"}]}'
```

### 代理網站檢查

```bash
# 檢查所有代理網站狀態
python check_proxy_websites.py
```

## 🧪 測試與驗證

### 快速測試

```bash
# 運行整合測試（需要後端服務運行）
.\test_integration.ps1

# 或直接運行 Python 測試
python test_url2parquet_integration.py
```

### 前端測試

```bash
cd frontend
npm run dev
# 訪問 http://127.0.0.1:5173
# 使用 URL 轉換與代理擷取功能
```

### 手動 API 測試

```bash
# 1. 啟動後端服務
uv run python run_server.py

# 2. 在另一個終端測試 API
curl -X POST "http://localhost:8000/api/url2parquet/jobs" \
     -H "Content-Type: application/json" \
     -d '{"urls":["https://free-proxy-list.net/"],"output_formats":["md","json","parquet","csv"]}'
```

## 🔧 配置

### 環境變數

複製 `.env.example` 到 `.env` 並根據需要修改配置：

```bash
cp .env.example .env
```

主要配置項目：

- `HOST`: 服務器主機地址（預設：0.0.0.0）
- `PORT`: 服務器端口（預設：8000）
- `LOG_LEVEL`: 日誌級別（預設：INFO）

## 📚 文檔

### 核心文檔

- [API 參考文檔](API_REFERENCE.md) - 完整的 API 接口說明
- [部署指南](DEPLOYMENT_GUIDE.md) - 詳細的部署和維護指南
- [API 配置指南](API_CONFIGURATION.md) - API 金鑰配置說明
- [專案依賴包說明（2025-09-08）](Docs/專案依賴包說明_2025-09-08.md) - 依賴套件用途與分類

### 專案文檔

- [專案總覽](Docs/PROJECT_OVERVIEW.md) - 完整的專案功能與架構說明
- [架構設計總覽](Docs/架構設計總覽.md) - 系統架構設計文檔
- [第一階段工作規劃](Docs/第一階段未完成工作細部規劃與注意事項.md) - 開發計劃和進度

### 技術文檔

- [自建探測器開發總結](JasonSpider-Dev/DEVELOPMENT_SUMMARY.md) - 自建代理探測器實現
- [ProxyScraper 整合分析](Docs/ProxyScraper整合分析與建議.md) - ProxyScraper 整合方案
- [GitHub 專案分析](Docs/三個GitHub代理專案分析與整合建議.md) - GitHub 代理專案整合建議

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！

### 開發規範

- 遵循 PEP 8 代碼風格
- 使用 `ruff` 進行代碼格式化和檢查
- 所有函數和類別必須包含中文文檔字符串
- 使用類型提示（Type Hints）

### 提交規範

使用 Conventional Commits 格式：

```
<type>(<scope>): <subject>

例如：
feat(crawler): add free-proxy-list.net crawler module
fix(api): resolve markdown conversion encoding issue
```

## 📄 授權

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 檔案。

## 🔗 相關連結

- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [aiohttp 文檔](https://docs.aiohttp.org/)
- [Beautiful Soup 文檔](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

---

**注意**: 本專案仍在積極開發中，部分功能可能尚未完全實現。請參考文檔了解最新進度。
