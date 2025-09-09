# 🐳 Docker 開發環境腳本說明

本目錄包含了用於快速啟動和管理 Proxy Crawler System 開發環境的 Docker 腳本。

## 📁 文件說明

### 核心文件

- **`docker-compose.dev.yml`** - 開發環境的 Docker Compose 配置文件
- **`start-dev.ps1`** - 一鍵啟動開發環境的 PowerShell 腳本
- **`stop-dev.ps1`** - 停止開發環境的 PowerShell 腳本
- **`DEV_ENVIRONMENT.md`** - 完整的開發環境設置指南

## 🚀 快速使用

### 啟動開發環境

```powershell
# 在專案根目錄執行
.\start-dev.ps1
```

這個腳本會：
1. 檢查 Docker 是否運行
2. 驗證配置文件是否存在
3. 清理舊容器（如果存在）
4. 構建並啟動所有服務
5. 顯示服務狀態和訪問 URL

### 停止開發環境

```powershell
# 在專案根目錄執行
.\stop-dev.ps1
```

這個腳本會：
1. 停止所有開發環境服務
2. 停止可選的管理工具
3. 提供清理和重啟選項

## 🎯 服務訪問

啟動成功後，您可以訪問以下服務：

| 服務 | URL | 說明 | 容器名稱 |
|------|-----|------|----------|
| 前端應用 | http://localhost:5174 | React + Vite 開發服務器 | proxy_frontend_dev |
| 後端 API | http://localhost:8000 | FastAPI 應用 | proxy_backend_dev |
| API 文檔 | http://localhost:8000/docs | Swagger UI 文檔 | proxy_backend_dev |
| PostgreSQL | localhost:5432 | 數據庫（postgres/postgres） | proxy_postgres_dev |
| Redis | localhost:6379 | 緩存服務 | proxy_redis_dev |
| HTML to Markdown | http://localhost:3001 | 文件轉換服務 | proxy_html_markdown_dev |

## 🛠️ 可選管理工具

```powershell
# 啟動數據庫和 Redis 管理工具
docker-compose -f docker-compose.dev.yml --profile tools up -d
```

| 工具 | URL | 登錄信息 | 容器名稱 |
|------|-----|----------|----------|
| pgAdmin | http://localhost:5050 | admin@example.com / admin | proxy_pgadmin_dev |
| Redis Commander | http://localhost:8081 | 無需登錄 | proxy_redis_commander_dev |

## 🔧 常用命令

```powershell
# 查看服務狀態
docker-compose -f docker-compose.dev.yml ps

# 查看服務日誌
docker-compose -f docker-compose.dev.yml logs -f [service_name]

# 進入容器
docker-compose -f docker-compose.dev.yml exec backend bash
docker-compose -f docker-compose.dev.yml exec frontend sh

# 重新構建服務
docker-compose -f docker-compose.dev.yml up --build -d

# 完全清理（包括數據）
docker-compose -f docker-compose.dev.yml down -v --remove-orphans
```

## 🐛 故障排除

### 常見問題

1. **端口被占用**
   ```powershell
   # 檢查端口占用
   netstat -ano | findstr :5174
   netstat -ano | findstr :8000
   ```

2. **Docker 服務未啟動**
   ```powershell
   # 檢查 Docker 狀態
   docker info
   ```

3. **權限問題**
   ```powershell
   # 以管理員身份運行 PowerShell
   Start-Process powershell -Verb runAs
   ```

4. **容器構建失敗**
   ```powershell
   # 清理並重新構建
   docker-compose -f docker-compose.dev.yml down -v --remove-orphans
   docker system prune -f
   .\start-dev.ps1
   ```

### 重置環境

如果遇到問題，可以完全重置開發環境：

```powershell
# 停止所有服務
.\stop-dev.ps1

# 清理所有容器和數據
docker-compose -f docker-compose.dev.yml down -v --remove-orphans
docker system prune -f

# 重新啟動
.\start-dev.ps1
```

## 📝 開發工作流程

1. **啟動環境**：`./start-dev.ps1`
2. **開發代碼**：在本地編輯器中修改代碼
3. **自動重載**：前後端都支持熱重載
4. **測試功能**：使用瀏覽器或 API 工具測試
5. **查看日誌**：使用 `docker-compose logs` 查看日誌
6. **停止環境**：`./stop-dev.ps1`

## 🔗 相關文檔

- [`DEV_ENVIRONMENT.md`](./DEV_ENVIRONMENT.md) - 完整開發環境指南
- [`QUICK_START.md`](./QUICK_START.md) - 快速開始指南
- [`README.md`](./README.md) - 專案主要說明文檔

---

**提示**：如果您是第一次使用，建議先閱讀 [`DEV_ENVIRONMENT.md`](./DEV_ENVIRONMENT.md) 獲取更詳細的說明。