# 🐳 開發環境快速啟動指南

本指南提供兩種開發環境啟動方式：**Docker 容器化環境**（推薦）和**本地環境**。

## 🚀 方式一：Docker 容器化開發環境（推薦）

### 📋 前置需求

- Windows 10/11
- Docker Desktop
- PowerShell 5.0+

### ⚡ 一鍵啟動（2 分鐘）

```powershell
# 進入專案目錄
cd Proxy-Crawler-System

# 一鍵啟動開發環境
.\start-dev.ps1
```

### 🎯 啟動後可用服務

#### 🚀 主要服務容器 (5個)

- **前端服務**: http://localhost:5174 (Node.js + Vite 開發服務器)
- **後端 API**: http://localhost:8000 (FastAPI + uvicorn)
- **API 文檔**: http://localhost:8000/docs (Swagger UI)
- **PostgreSQL 資料庫**: localhost:5432 (用戶: postgres, 密碼: postgres)
- **Redis 快取**: localhost:6379 (無密碼)
- **HTML to Markdown 服務**: http://localhost:3001 (文件轉換服務)

### 🛠️ 可選管理工具

```powershell
# 啟動資料庫和 Redis 管理工具
docker-compose -f docker-compose.dev.yml --profile tools up -d
```

- **pgAdmin**: http://localhost:5050 (admin@example.com / admin)
- **Redis Commander**: http://localhost:8081

### 🔧 常用操作

```powershell
# 停止開發環境
.\stop-dev.ps1

# 查看服務狀態
docker-compose -f docker-compose.dev.yml ps

# 查看服務日誌
docker-compose -f docker-compose.dev.yml logs -f [service_name]
# 例如：docker-compose -f docker-compose.dev.yml logs -f backend

# 進入容器內部
docker-compose -f docker-compose.dev.yml exec backend bash
docker-compose -f docker-compose.dev.yml exec frontend sh

# 重新構建並啟動
docker-compose -f docker-compose.dev.yml up --build -d

# 完全清理（包括數據卷）
docker-compose -f docker-compose.dev.yml down -v --remove-orphans
```

### 🔄 開發工作流程

1. **代碼修改**: 直接在本地編輯器中修改代碼
2. **自動重載**: 
   - 後端：uvicorn 的 `--reload` 模式會自動重載 Python 代碼
   - 前端：Vite 的熱重載會自動更新前端變更
3. **數據持久化**: PostgreSQL 和 Redis 數據會保存在 Docker 卷中
4. **日誌查看**: 使用 `docker-compose logs` 查看各服務日誌

### 🐛 故障排除

```powershell
# 檢查 Docker 服務
docker info

# 檢查端口占用
netstat -ano | findstr :5174
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# 重置開發環境
.\stop-dev.ps1
docker-compose -f docker-compose.dev.yml down -v --remove-orphans
.\start-dev.ps1
```

---

## 🏠 方式二：本地開發環境

### 📋 前置需求

- Windows 10/11
- Python 3.11+
- Node.js 16+
- PowerShell 5.0+
- PostgreSQL 15+ (可選)
- Redis 7+ (可選)

### ⚡ 快速啟動（5 分鐘）

#### 1. 設置 Python 環境

```powershell
# 進入專案目錄
cd Proxy-Crawler-System

# 創建並激活 uv 虛擬環境
uv venv
uv shell

# 安裝 Python 依賴
uv sync
```

#### 2. 啟動後端服務

```powershell
# 在專案根目錄執行
uv run python run_server.py
# 或者
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

等待看到以下訊息表示啟動成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### 3. 啟動前端服務

```powershell
# 新開一個 PowerShell 視窗
cd frontend
npm ci
npm run dev
```

等待看到以下訊息表示啟動成功：

```
  VITE v7.1.2  ready in 1234 ms

  ➜  Local:   http://127.0.0.1:5174/
  ➜  Network: use --host to expose
```

#### 4. 訪問應用

打開瀏覽器訪問：http://127.0.0.1:5174

### 🧪 快速測試（2 分鐘）

#### 方法一：使用整合測試腳本

```powershell
# 在專案根目錄執行（確保後端已啟動）
.\test_integration.ps1
```

#### 方法二：手動測試 API

```powershell
# 測試健康檢查
curl http://localhost:8000/health

# 測試 URL2Parquet API
curl -X POST "http://localhost:8000/api/url2parquet/jobs" `
     -H "Content-Type: application/json" `
     -d '{"urls":["https://free-proxy-list.net/"],"output_formats":["md","json","parquet","csv"]}'
```

#### 方法三：使用前端界面

1. 訪問 http://127.0.0.1:5174
2. 點擊「URL 轉換與代理擷取」
3. 輸入代理網站 URL（預設已填入）
4. 點擊「開始轉換」
5. 等待處理完成並下載文件

### 🔧 本地環境常見問題

#### Q: 後端啟動失敗

**A:** 檢查端口 8000 是否被占用：

```powershell
netstat -ano | findstr :8000
```

#### Q: 前端無法連接後端

**A:** 檢查 Vite 代理配置：

```javascript
// frontend/vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

#### Q: 依賴安裝失敗

**A:** 使用 uv 重新安裝：

```powershell
uv sync --reinstall
```

#### Q: uv 虛擬環境問題

**A:** 重新創建虛擬環境：

```powershell
# 刪除現有虛擬環境
Remove-Item -Recurse -Force .venv

# 重新創建
uv venv
uv shell
uv sync
```

---

## 📊 功能驗證（3 分鐘）

### 1. 基本功能測試

- ✅ 前端界面載入正常
- ✅ 可以輸入多個 URL
- ✅ 可以選擇輸出格式（MD、JSON、Parquet、CSV）
- ✅ 任務創建成功
- ✅ 文件生成和下載正常

### 2. 重定向處理測試

- ✅ 檢測到重定向時顯示確認對話框
- ✅ 可以確認並繼續處理重定向 URL
- ✅ 重定向後的文件生成正常

### 3. 本地文件管理測試

- ✅ 可以列出本地 Markdown 文件
- ✅ 可以讀取和解析本地文件內容
- ✅ 代理數據解析和顯示正常

---

## 📈 進階使用

### 1. 自定義配置

編輯 `config/config.yaml` 來調整：

- 代理驗證參數
- 輸出格式選項
- 快取策略
- 日誌級別

### 2. 批量處理

使用 API 進行批量 URL 處理：

```bash
curl -X POST "http://localhost:8000/api/url2parquet/jobs" \
     -H "Content-Type: application/json" \
     -d '{
       "urls": [
         "https://free-proxy-list.net/",
         "https://www.sslproxies.org/",
         "https://www.us-proxy.org/"
       ],
       "output_formats": ["md", "json", "parquet", "csv"],
       "timeout_seconds": 60
     }'
```

### 3. 監控和日誌

- **Docker 環境**：使用 `docker-compose logs` 查看日誌
- **本地環境**：後端日誌在 `logs/proxy-crawler.log`
- **健康檢查**：http://localhost:8000/health
- **API 文檔**：http://localhost:8000/docs

---

## 🎯 推薦開發流程

### 新手開發者

1. **使用 Docker 環境**：`./start-dev.ps1`
2. **熟悉界面**：訪問前端和 API 文檔
3. **運行測試**：`./test_integration.ps1`
4. **開始開發**：修改代碼並觀察自動重載

### 經驗豐富的開發者

1. **選擇環境**：Docker（隔離性好）或本地（性能更佳）
2. **配置 IDE**：設置代碼格式化和類型檢查
3. **設置調試**：配置斷點和日誌級別
4. **集成測試**：編寫和運行自動化測試

---

## 📞 獲取幫助

- **完整文檔**：`README.md`
- **API 文檔**：http://localhost:8000/docs
- **專案文檔**：`Docs/` 目錄
- **整合測試**：`./test_integration.ps1`
- **快速開始**：`QUICK_START.md`

---

**恭喜！** 🎉 您已掌握了 Proxy Crawler System 的開發環境設置。選擇適合您的方式開始開發吧！