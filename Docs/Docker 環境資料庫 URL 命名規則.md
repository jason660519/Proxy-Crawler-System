# **Proxy Crawler & Management System**

## **Docker 環境資料庫 URL 命名規則**

在 Docker 環境中，容器之間是通過服務名稱(service name) 而不是 `localhost` 進行通訊的。您的 `docker-compose.yml` 中定義的服務名稱就是容器的主機名。

**文檔更新時間**: 2025-01-07  
**適用版本**: 當前專案狀態  
**更新內容**: 根據實際 Docker 配置和資料庫配置管理器更新

#### **1\. 標準格式 (Standard Format)**

`bash`

`protocol://username:password@host:port/database_name`

- `protocol`: `postgresql` (或舊的 `postgres`)
- `username`: 資料庫使用者名稱
- `password`: 資料庫密碼
- `host`: Docker 服務名稱 (最重要！)
- `port`: 資料庫對外暴露的端口 (預設為 `5432`)
- `database_name`: 要連接的具體資料庫名稱

#### **2\. 常見情境與範例 (Scenarios & Examples)**

**情境一：在 Python 應用程式容器中連接 PostgreSQL 容器**

根據當前專案的 `docker-compose.yml` 配置：

```yaml
services:
  postgres_db: # <-- 這就是「服務名稱」(hostname)
    image: postgres:15
    environment:
      POSTGRES_USER: ${DB_USER:-proxyadmin}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME:-proxypool}
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-proxyadmin}"]

  redis_cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  proxy_crawler: # 您的Python應用
    build: .
    environment:
      - ENVIRONMENT=docker
      - DB_USER=${DB_USER:-proxyadmin}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME:-proxypool}
    depends_on:
      postgres_db:
        condition: service_healthy
      redis_cache:
        condition: service_healthy
```

**正確的連接 URL**：

- **PostgreSQL**: `postgresql://proxyadmin:${DB_PASSWORD}@postgres_db:5432/proxypool`
- **Redis**: `redis://redis_cache:6379/0`
- **Hostname**: `postgres_db` 和 `redis_cache` (使用 Docker 服務名稱)

**情境二：在本機開發環境連接 Docker 中的 PostgreSQL**

當您從宿主機 (Windows 10) 連接時，需要使用 `localhost` 或 `127.0.0.1`：

**正確的連接 URL (從宿主機連接)**：

- **PostgreSQL**: `postgresql://proxyadmin:${DB_PASSWORD}@localhost:5432/proxypool`
- **Redis**: `redis://localhost:6379/0`
- **Hostname**: `localhost` (因為端口已映射到宿主機)

**情境三：使用不同的驅動程式 (如 asyncpg)**

為了獲得更好的非同步性能，您可能會使用 `asyncpg` 驅動：

**正確的連接 URL (使用 asyncpg)**：

- **Docker 環境**: `postgresql+asyncpg://proxyadmin:${DB_PASSWORD}@postgres_db:5432/proxypool`
- **本地環境**: `postgresql+asyncpg://proxyadmin:${DB_PASSWORD}@localhost:5432/proxypool`

#### **3\. 在 Python 程式碼中使用 (推薦使用智能配置管理器)**

**方法一：使用專案的智能配置管理器 (推薦)**

```python
# 導入專案的智能配置管理器
from database_config import db_config, get_sync_database_url, get_async_database_url, get_redis_url

# 自動取得正確的資料庫 URL（無需手動組合）
sync_url = get_sync_database_url()      # postgresql://user:pass@host:port/db
async_url = get_async_database_url()    # postgresql+asyncpg://user:pass@host:port/db
redis_url = get_redis_url()             # redis://host:port/0

# 查看當前配置資訊
config_info = db_config.get_connection_info()
print(config_info)
```

**方法二：傳統 SQLAlchemy 方式**

````python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# 從環境變數讀取，這是12因子應用(12-Factor App)的最佳實踐
DATABASE_URL = os.getenv("DATABASE_URL")

# 同步引擎 (適用於 requests, scrapy)
sync_engine = create_engine(DATABASE_URL)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# 異步引擎 (適用於 aiohttp, FastAPI)
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# 依賴注入函數
async def get_async_db():
    async with AsyncSessionLocal() as db:
        yield db

#### **4\. 環境變數配置建議 (.env 文件)**

**當前專案推薦的配置方式**：

編輯 `.env` 文件時，確保將其添加到 `.gitignore` 中：

```bash
# 核心配置 - 僅需這 4 個變數
ENVIRONMENT=docker          # 或 local
DB_USER=proxyadmin
DB_PASSWORD=your_secure_password_here
DB_NAME=proxypool

# 可選配置（有預設值）
# REDIS_PASSWORD=redis_password
# DB_HOST=postgres_db
# REDIS_HOST=redis_cache
```

**傳統配置方式（如果需要手動管理 URL）**：

```bash
# Database
DB_HOST=postgres_db
DB_PORT=5432
DB_NAME=proxypool
DB_USER=proxyadmin
DB_PASSWORD=your_secure_password_here

# 組合成完整的 URL (在 Docker 容器內使用)
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# 為宿主機開發提供的 URL
LOCAL_DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}

# Redis
REDIS_URL=redis://redis_cache:6379/0
```

**在 `docker-compose.yml` 中的使用**：

```yaml
services:
  proxy_crawler:
    build: .
    environment:
      - ENVIRONMENT=docker
      - DB_USER=${DB_USER:-proxyadmin}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_NAME=${DB_NAME:-proxypool}
    # 或者使用 env_file
    # env_file:
    #   - .env
```

### **總結**

1. **關鍵規則**：在 Docker 容器內，永遠使用 `服務名稱` 作為 `hostname`。
2. **安全性**：永遠不要將真實的密碼或 `.env` 文件提交到版本控制 (git)。
3. **最佳實踐**：使用環境變數來管理資料庫連接字符串，並區分 Docker 內部和宿主機的連接方式。
4. **推薦方式**：使用專案的智能配置管理器 (`database_config.py`) 來自動處理環境差異。
5. **當前專案狀態**：已整合智能配置管理器，支援自動環境檢測和 URL 生成。

---

### **🚀 優化後的解決方案**

基於上述複雜的配置需求，我們已經開發了一套**智能配置管理器**來簡化 Docker 環境的資料庫 URL 管理。

#### **新的使用方式**

```python
# 導入配置管理器
from database_config import db_config, get_sync_database_url, get_async_database_url, get_redis_url

# 自動取得正確的資料庫 URL（無需手動組合）
sync_url = get_sync_database_url()      # postgresql://user:pass@host:port/db
async_url = get_async_database_url()    # postgresql+asyncpg://user:pass@host:port/db
redis_url = get_redis_url()             # redis://host:port/0

# 查看當前配置資訊
config_info = db_config.get_connection_info()
print(config_info)
````

#### **簡化的環境變數配置**

```bash
# .env 文件（僅需核心配置）
ENVIRONMENT=docker          # 或 local
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=proxy_crawler

# 可選配置（有預設值）
# REDIS_PASSWORD=redis_password
# DB_HOST=postgres
# REDIS_HOST=redis
```

#### **主要改進**

1. **配置複雜度降低 60%**：從 10+ 個環境變數減少到 4 個核心變數
2. **自動環境檢測**：智能判斷 Docker 或本地環境
3. **統一介面**：一個函數取得所有類型的資料庫 URL
4. **錯誤處理**：內建連接驗證和錯誤提示
5. **向後相容**：支援現有的環境變數配置

#### **相關檔案**

- `database_config.py` - 智能配置管理器 ✅
- `env.example` - 環境變數範本 ✅
- `docker-compose.yml` - Docker 配置 ✅
- `src/main.py` - 主應用程式入口 ✅
- `src/simple_api.py` - 簡化 API 端點 ✅

#### **當前專案狀態**

- ✅ Docker 服務正常運行
- ✅ 智能配置管理器已整合
- ✅ 環境變數配置簡化
- ✅ API 端點基本可用
- ✅ 資料庫連接正常

---

**文檔更新完成時間**: 2025-01-07  
**更新內容**: 根據實際專案狀況更新了 Docker 配置、環境變數設定和智能配置管理器的使用方式
