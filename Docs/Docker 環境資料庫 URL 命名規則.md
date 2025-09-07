# Proxy Crawler & Management System

## Database/Cache URL Conventions (Docker & Local)

在 Docker 環境中，容器之間是通過服務名稱(service name) 而不是 `localhost` 進行通訊的。您的 `docker-compose.yml` 中定義的服務名稱就是容器的主機名。

**文檔更新時間**: 2025-01-07  
**適用版本**: 當前專案狀態  
**更新內容**: 根據實際 Docker 配置和資料庫配置管理器更新

#### Standard Format

`protocol://username:password@host:port/database_name`

- `protocol`: `postgresql`
- `username`: database user
- `password`: database password
- `host`: Docker service name (in-container) or `localhost` (host machine)
- `port`: default `5432`
- `database_name`: target database

#### Scenarios & Examples

Scenario A: From application container to Postgres container

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

Correct URLs:

- Postgres: `postgresql://proxyadmin:${DB_PASSWORD}@postgres_db:5432/proxypool`
- Redis: `redis://redis_cache:6379/0`
- Hostname: `postgres_db`, `redis_cache` (Compose service names)

Scenario B: From host (Windows 10) to Postgres in Docker

當您從宿主機 (Windows 10) 連接時，需要使用 `localhost` 或 `127.0.0.1`：

Correct URLs:

- Postgres: `postgresql://proxyadmin:${DB_PASSWORD}@localhost:5432/proxypool`
- Redis: `redis://localhost:6379/0`
- Hostname: `localhost` (ports mapped)

Scenario C: Async drivers (asyncpg/SQLAlchemy async)

為了獲得更好的非同步性能，您可能會使用 `asyncpg` 驅動：

Correct URLs:

- Docker: `postgresql+asyncpg://proxyadmin:${DB_PASSWORD}@postgres_db:5432/proxypool`
- Local: `postgresql+asyncpg://proxyadmin:${DB_PASSWORD}@localhost:5432/proxypool`

#### In Python (Recommended: project config manager)

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

Legacy SQLAlchemy example

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

#### Env variables (.env)

Recommended minimal set:

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

Full explicit form (if managing URLs manually):

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

In `docker-compose.yml`:

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

### Summary

1. In-container use service names; on host use localhost.
2. Do not commit secrets or `.env`.
3. Prefer env vars; differentiate Docker vs local.
4. Use `database_config.py` to auto-resolve URLs.
5. Current project: auto-detect env; runs Alembic on start; `/api/health` probes DB/Redis.

---

### Improved approach

基於上述複雜的配置需求，我們已經開發了一套**智能配置管理器**來簡化 Docker 環境的資料庫 URL 管理。

Usage

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

Minimal env

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

Key improvements

1. **配置複雜度降低 60%**：從 10+ 個環境變數減少到 4 個核心變數
2. **自動環境檢測**：智能判斷 Docker 或本地環境
3. **統一介面**：一個函數取得所有類型的資料庫 URL
4. **錯誤處理**：內建連接驗證和錯誤提示
5. **向後相容**：支援現有的環境變數配置

References

- `database_config.py` - 智能配置管理器 ✅
- `env.example` - 環境變數範本 ✅
- `docker-compose.yml` - Docker 配置 ✅
- `src/main.py` - 主應用程式入口 ✅
- `src/simple_api.py` - 簡化 API 端點 ✅

Current state

- ✅ Docker 服務正常運行
- ✅ 智能配置管理器已整合
- ✅ 環境變數配置簡化
- ✅ API 端點基本可用
- ✅ 資料庫連接正常

---

Updated: 2025-01-07  
Notes: aligned to current Docker config, env variables, and config manager usage
