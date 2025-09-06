# JasonSpider - 代理爬蟲與管理系統

一個功能完整的代理爬蟲與管理系統，支援多來源代理獲取、HTML 轉 Markdown 服務，以及智能代理管理功能。

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

# 3. 安裝依賴
uv sync
# 或使用 pip
pip install -r requirements.txt

# 4. 配置 API 金鑰（可選）
python setup_api_config.py interactive

# 5. 測試核心功能
python test_core_functionality.py

# 6. 啟動服務
python src/main.py
```

### Docker 部署

```bash
# 使用 Docker Compose 啟動所有服務
docker-compose up -d

# 或單獨構建和運行
docker build -t jason-spider .
docker run -p 8000:8000 jason-spider
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
