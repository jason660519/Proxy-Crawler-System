# JasonSpider - 代理爬蟲與管理系統

![Status](https://img.shields.io/badge/status-active-success)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-%F0%9F%9A%80-009688)
![License](https://img.shields.io/badge/License-MIT-green)
![uv](https://img.shields.io/badge/deps-managed%20by%20uv-orange)
<!-- CI / Coverage (待導入)
![CI](https://img.shields.io/github/actions/workflow/status/<org>/<repo>/ci.yml)
![Coverage](https://img.shields.io/codecov/c/github/<org>/<repo>) -->

一個可觀測、模組化、可擴充的「代理爬蟲 + 智能代理池 + HTML 轉 Markdown」整合平台，提供 API 化服務、指標監控與彈性擴展能力，協助構建可靠的網路資料擷取基礎設施。

> TL;DR：啟動主後端只需 `uv sync` → `uv run python run_server.py`，然後開啟 <http://127.0.0.1:8000/docs>。

---

## 🧭 目錄 (Table of Contents)

- [主要功能](#-主要功能)
- [專案結構](#-專案結構)
- [安裝 (Installation)](#-安裝與使用)
     - [快速開始 (Quick Start)](#快速開始)
     - [使用 uv 的標準開發工作流程](#使用-uv-的標準開發工作流程)
- [啟動與存取網址速查](#-啟動與存取網址速查)
- [API 使用](#-api-使用)
- [系統健康檢查與監控](#-系統健康檢查與監控)
- [技術棧 (Tech Stack)](#-技術棧-tech-stack)
- [配置](#-配置)
- [文檔](#-文檔)
- [開發 / 貢獻指南](#-貢獻)
- [故障排查 (Troubleshooting)](#-故障排查-troubleshooting)
- [授權](#-授權)
- [致謝 (Acknowledgements)](#-致謝-acknowledgements)

---

## 🖼️ 預覽 (Screenshots / Diagrams)

| 類別 | 圖示 |
|------|------|
| 系統架構 (Architecture) | （參考 `Docs/架構設計總覽.md` 可自行加入 mermaid / 圖片） |
| 指標監控 (Prometheus / Grafana) | （待補：可將 dashboard 擷圖放於 `Docs/images/`） |
| Swagger API | ![Swagger](https://img.shields.io/badge/Swagger-UI-green?logo=swagger) |

> 可在後續提交中新增實際截圖：`Docs/images/architecture.png`、`Docs/images/dashboard.png` 等。

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

```bash
# 1. 克隆專案
git clone <repository-url>
cd JasonSpider

# 2. 設置虛擬環境（推薦使用 uv）
uv venv
uv shell

# 3. 安裝依賴（推薦）
uv sync
# 備註: 以 pyproject.toml 為主，requirements.txt 僅作相容用途

# 4. 配置環境與 API 金鑰
cp .env.example .env  # Windows PowerShell: Copy-Item .env.example .env
python setup_api_config.py interactive  # 可選

# 5. 測試核心功能
python test_core_functionality.py

# 6. 啟動服務（見下方速查指令與網址）
```

> 提示：現在只需在專案根目錄執行 `uv sync`，即可快速、可靠地建立與專案定義完全一致的 Python 開發環境，無需再關心複雜的 pip 與 venv 指令。這大幅簡化入門流程並保證環境一致性。

### 使用 uv 的標準開發工作流程

> 狀態：專案已統一使用單一虛擬環境目錄 `.venv`（多餘的 `venv/` 已清理）。請勿手動建立第二個環境，以免產生套件漂移。

常用指令速查 (於專案根目錄 PowerShell 執行)：

```powershell
# 建立 / 修復虛擬環境（若 .venv 遺失）
uv venv

# 解析並安裝 pyproject.toml 中宣告的依賴（含開發依賴）
uv sync

# 執行任意模組 / 腳本（自動使用 .venv）
uv run python run_server.py
uv run pytest -q

# 新增依賴（預設寫入 pyproject.toml）
uv add requests
uv add "fastapi[standard]"

# 新增開發用依賴（--dev 或 -d）
uv add --dev ruff pytest

# 移除依賴
uv remove requests

# 升級某個或全部依賴（重新求解鎖定）
uv lock --upgrade requests
uv lock --upgrade

# 匯出為 requirements.txt（部署或相容用途）
uv export > requirements.txt

# 檢視依賴樹（快速審查 transitive 依賴）
uv tree

# 清理後完全重建（遇到環境污染時）
Remove-Item -Recurse -Force .venv; uv venv; uv sync
```

工作流建議：

1. 同步環境：拉取最新程式後先執行 `uv sync`（會快取並僅做必要變更）。
2. 變更依賴：使用 `uv add/remove`，勿直接手改 `uv.lock` 或手動 `pip install`。
3. 執行程式 / 測試：一律透過 `uv run <command>` 或已進入 `uv shell` 的互動環境。
4. 版本升級：批次升級前先建立 Git 分支，執行 `uv lock --upgrade`，再跑完整測試套件。
5. 排除環境問題：若出現「模組找不到 / 版本錯亂」，優先嘗試重建 `.venv`。

為何選擇 uv：

- 更快的解析與安裝（Rust 實作）
- 直接使用 `pyproject.toml` 作為單一事實來源（無需多套工具）
- 內建 lockfile（`uv.lock`）確保可重現性
- 指令介面簡潔；減少 on-boarding 心智負擔

故障排查速表：

| 現象 | 建議指令 | 補充 |
|------|----------|------|
| 找不到模組 | `uv sync` | 可能是剛 pull 下來尚未安裝依賴 |
| 版本不符 | `uv lock --upgrade <pkg>` | 升級後務必跑測試 |
| 執行時混用全域 Python | `where python` / `uv run python -V` | 用 `uv run` 強制鎖定環境 |
| 套件殘留或環境污染 | 重建 `.venv` | 刪除後 `uv venv && uv sync` |
| 要產出 requirements.txt | `uv export > requirements.txt` | CI/部署相容模式 |

進階：可在 CI 中直接使用：

```bash
uv sync --frozen  # 嚴格依鎖檔安裝，若 pyproject 與 uv.lock 不一致會失敗
```

> 若未來需要多 Python 版本測試，可結合 `uv tool install python@3.12` 與矩陣測試策略；現階段專案鎖定 3.11+。

---

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

### HTML to Markdown 轉換

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

## 🩺 系統健康檢查與監控

提供下列健康與運維相關端點／資源：

| 類型 | 路徑 | 說明 |
|------|------|------|
| 健康檢查 | `/health` | 簡易 redirect 至 `/api/health` |
| 健康檢查 (API) | `/api/health` | FastAPI app 層級健康狀態 |
| 系統總覽 | `/api/system/health` | 彙總版本、時間戳、ProxyManager 內部統計 |
| 指標 (Prometheus) | `/metrics` | 供 Prometheus 抓取的 metrics exposition |
| API Docs | `/docs` | Swagger UI |

Prometheus 可整合 `docker/prometheus/` 設定，Grafana 可透過 `docker/grafana/` dashboard 載入監控。建議追蹤：

- 代理池大小（熱/溫/冷）
- 驗證成功率與耗時直方圖
- 來源抓取成功/失敗計數
- 系統任務心跳 (heartbeat loop)

若 `/api/system/health` 回傳 `proxy_manager.initialized = false`，表示尚未於 lifespan 中完成初始化（檢查啟動 log 或異常）。

---

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

## 🧱 技術棧 (Tech Stack)

| 類別 | 使用技術 | 說明 |
|------|----------|------|
| 語言 | Python 3.11+ | 以異步 IO 為核心任務執行模式 |
| 後端框架 | FastAPI + Uvicorn | 高效非同步 API 服務框架 |
| 依賴管理 | uv | 單一事實來源 / 快速鎖定與重建環境 |
| 代理功能 | 自研模組 (pools / fetchers / validators / scanner) | 智能分層池 + 來源聚合 + 驗證評分 |
| 抓取 / HTTP | aiohttp / requests | 異步與同步混合使用場景 |
| 內容轉換 | markdownify / html2text / pandoc | 多引擎 HTML -> Markdown 轉換 |
| 資料儲存 | SQLite / (可選 Redis) | 快速原型與快取管理 / 任務分發 |
| 指標監控 | Prometheus + Grafana | 指標採集 / 視覺化儀表板 |
| 前端 | Vite + TypeScript | Dev server / 未來管理介面擴充 |
| 佈署 | Docker / docker compose | 容器化與可移植性 |
| 測試 | pytest | 單元 / 整合測試框架 |
| 程式風格 | ruff / type hints | 靜態分析與一致風格 |

> 可依未來引入的外部代理來源或儲存服務（如 PostgreSQL / ClickHouse）擴充。

---

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

## �️ 故障排查 (Troubleshooting)

| 現象 / 訊號 | 可能原因 | 解法 | 指令範例 |
|--------------|----------|------|-----------|
| 啟動時 ImportError / circular import | 模組互相引用 | 延遲匯入 / TYPE_CHECKING | （已處理於程式碼，若再現請檢查新增路由 import） |
| `NameError: self not defined` | 類別屬性縮排錯誤 | 修正縮排 / 確保屬性在 `__init__` 中 |  |
| `AttributeError: 'ProxyValidator' object has no attribute 'close'` | 非同步/同步 close 混用 | 已統一 async `close()` + `close_sync()` |  |
| Pydantic 警告：欄位名稱 `validate` 衝突 | 欄位名影射 BaseModel 方法 | 已改名為 `perform_validation` |  |
| 無法取得代理 / pool 為空 | 抓取來源失敗或尚未完成初始化 | 等待第一次 fetch 任務或確認來源 API 金鑰 | 查看 log |
| `/api/system/health` 顯示 initialized=false | lifespan 尚未執行完 | 檢查啟動路徑 / 重啟 | `uv run python run_server.py` |
| Port 已被占用 | 之前實例未正常關閉 | 終止殘留進程或改 port | `netstat -ano \| findstr 8000` |
| 依賴錯亂 / 找不到模組 | 環境污染 | 重建虛擬環境 | `Remove-Item -Recurse -Force .venv; uv venv; uv sync` |

> 如需新增更多常見錯誤，請更新本表；建議同步記錄於 `Docs/測試策略與驗證方案.md`。

---

## �📄 授權

本專案採用 MIT 授權條款。詳見 [LICENSE](LICENSE) 檔案。

## 🙏 致謝 (Acknowledgements)

感謝以下專案及生態系提供的能力與靈感：

- [FastAPI](https://fastapi.tiangolo.com/): 高效非同步 API 框架
- [uv](https://github.com/astral-sh/uv): 極速 Python 依賴與環境管理
- [Prometheus](https://prometheus.io/) 與 [Grafana](https://grafana.com/): 指標監控與視覺化
- `markdownify`, `html2text`, `pandoc`: 多樣化 HTML -> Markdown 轉換引擎
- Python 網路庫：`aiohttp`, `requests`
- 其他協助靈感與結構設計的開源專案作者

若本專案的代理模組實作或文檔對你有幫助，歡迎 star ⭐ 或分享！

---

## 🔗 相關連結

- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [aiohttp 文檔](https://docs.aiohttp.org/)
- [Beautiful Soup 文檔](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

---

**新增**: 已加入集中設定模組 `config.settings` 與 `/metrics` 指標端點；請勿在程式碼硬編碼金鑰。

**注意**: 本專案仍在積極開發中，部分功能可能尚未完全實現。請參考文檔了解最新進度。
