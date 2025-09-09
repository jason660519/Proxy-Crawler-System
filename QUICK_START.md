# 🚀 快速開始指南

本指南將幫助您在 10 分鐘內啟動並使用 Proxy Crawler System。

## 📋 前置需求

- Windows 10/11
- Python 3.11+
- Node.js 16+ (用於前端)
- PowerShell 5.0+

## ⚡ 快速啟動（5 分鐘）

### 1. 克隆專案並設置環境

```powershell
# 進入專案目錄
cd Proxy-Crawler-System

# 創建並激活虛擬環境
uv venv
uv shell

# 安裝依賴
uv sync
```

### 2. 啟動後端服務

```powershell
# 在專案根目錄執行
uv run python run_server.py
```

等待看到以下訊息表示啟動成功：

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 3. 啟動前端服務

```powershell
# 新開一個 PowerShell 視窗
cd frontend
npm ci
npm run dev
```

等待看到以下訊息表示啟動成功：

```
  VITE v7.1.2  ready in 1234 ms

  ➜  Local:   http://127.0.0.1:5173/
  ➜  Network: use --host to expose
```

### 4. 訪問應用

打開瀏覽器訪問：http://127.0.0.1:5173

## 🧪 快速測試（2 分鐘）

### 方法一：使用整合測試腳本

```powershell
# 在專案根目錄執行（確保後端已啟動）
.\test_integration.ps1
```

### 方法二：手動測試 API

```powershell
# 測試健康檢查
curl http://localhost:8000/health

# 測試 URL2Parquet API
curl -X POST "http://localhost:8000/api/url2parquet/jobs" `
     -H "Content-Type: application/json" `
     -d '{"urls":["https://free-proxy-list.net/"],"output_formats":["md","json","parquet","csv"]}'
```

### 方法三：使用前端界面

1. 訪問 http://127.0.0.1:5173
2. 點擊「URL 轉換與代理擷取」
3. 輸入代理網站 URL（預設已填入）
4. 點擊「開始轉換」
5. 等待處理完成並下載文件

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

## 🔧 常見問題

### Q: 後端啟動失敗

**A:** 檢查端口 8000 是否被占用：

```powershell
netstat -ano | findstr :8000
```

### Q: 前端無法連接後端

**A:** 檢查 Vite 代理配置：

```javascript
// frontend/vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

### Q: 依賴安裝失敗

**A:** 使用 uv 重新安裝：

```powershell
uv sync --reinstall
```

### Q: 文件下載失敗

**A:** 檢查文件權限和磁碟空間：

```powershell
# 檢查 data 目錄權限
ls -la data/url2parquet/outputs/
```

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

- 後端日誌：`logs/proxy-crawler.log`
- 健康檢查：http://localhost:8000/health
- API 文檔：http://localhost:8000/docs

## 🎯 下一步

1. **探索前端功能**：嘗試不同的代理網站和輸出格式
2. **自定義配置**：根據需求調整系統參數
3. **集成到工作流**：將 API 集成到您的自動化腳本中
4. **監控性能**：使用內建的監控功能優化系統性能

## 📞 獲取幫助

- 查看完整文檔：`README.md`
- 檢查 API 文檔：http://localhost:8000/docs
- 查看專案文檔：`Docs/` 目錄
- 運行測試：`.\test_integration.ps1`

---

**恭喜！** 🎉 您已成功啟動並測試了 Proxy Crawler System。現在可以開始使用這個強大的代理爬蟲和管理系統了！
