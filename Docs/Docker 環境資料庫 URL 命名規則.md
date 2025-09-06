### **Proxy Crawler & Management System**

### **Docker 環境資料庫 URL 命名規則**

在 Docker 環境中，容器之間是通過服務名稱(service name) 而不是 `localhost` 進行通訊的。您的 `docker-compose.yml` 中定義的服務名稱就是容器的主機名。

#### **1\. 標準格式 (Standard Format)**

`bash`

`protocol://username:password@host:port/database_name`

* `protocol`: `postgresql` (或舊的 `postgres`)  
* `username`: 資料庫使用者名稱  
* `password`: 資料庫密碼  
* `host`: Docker 服務名稱 (最重要！)  
* `port`: 資料庫對外暴露的端口 (預設為 `5432`)  
* `database_name`: 要連接的具體資料庫名稱

#### **2\. 常見情境與範例 (Scenarios & Examples)**

情境一：在 Python 應用程式容器中連接 PostgreSQL 容器

* 假設 `docker-compose.yml` 定義如下：  
* `yaml`

`services:`  
  `postgres_db:        # <-- 這就是「服務名稱」(hostname)`  
    `image: postgres:15`  
    `environment:`  
      `POSTGRES_USER: proxyadmin`  
      `POSTGRES_PASSWORD: secretpassword`  
      `POSTGRES_DB: proxypool`  
    `ports:`  
      `- "5432:5432"`  
    `volumes:`  
      `- postgres_data:/var/lib/postgresql/data`

  `redis_cache:`  
    `image: redis:7-alpine`

  `proxy_api:          # 您的Python應用`  
    `build: .`  
    `depends_on:`  
      `- postgres_db`  
      `- redis_cache`  
    `environment:`  
      `- DATABASE_URL=postgresql://proxyadmin:secretpassword@postgres_db:5432/proxypool`

*       `- REDIS_URL=redis://redis_cache:6379/0`  
* 正確的 DATABASE\_URL:  
  `postgresql://proxyadmin:secretpassword@postgres_db:5432/proxypool`  
  * Hostname: `postgres_db` (使用 Docker 服務名稱)

情境二：在本機開發環境連接 Docker 中的 PostgreSQL

* 當您從宿主機(您的 Windows 10\) 連接時，需要使用 `localhost` 或 `127.0.0.1`。  
* 正確的 DATABASE\_URL (從宿主機連接):  
  `postgresql://proxyadmin:secretpassword@localhost:5432/proxypool`  
  * Hostname: `localhost` (因為端口 `5432` 已映射到宿主機)

情境三：使用不同的驅動程式 (如 asyncpg)

* 為了獲得更好的非同步性能，您可能會使用 `asyncpg` 驅動。  
* 正確的 DATABASE\_URL (使用 asyncpg):  
  `postgresql+asyncpg://proxyadmin:secretpassword@postgres_db:5432/proxypool`

#### **3\. 在 Python 程式碼中使用 (以 SQLAlchemy 為例)**

`python`

`import os`  
`from sqlalchemy import create_engine`  
`from sqlalchemy.orm import sessionmaker`  
`from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession`

*`# 從環境變數讀取，這是12因子應用(12-Factor App)的最佳實踐`*  
`DATABASE_URL = os.getenv("DATABASE_URL")`

*`# 同步引擎 (適用於 requests, scrapy)`*  
`sync_engine = create_engine(DATABASE_URL)`  
`SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)`

*`# 異步引擎 (適用於 aiohttp, FastAPI)`*  
`ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)`  
`async_engine = create_async_engine(ASYNC_DATABASE_URL)`  
`AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)`

*`# 依賴注入函數`*  
`async def get_async_db():`  
    `async with AsyncSessionLocal() as db:`

        `yield db`

#### **4\. 環境變數配置建議 (.env 文件)**

編輯 `.env` 文件時，確保將其添加到 `.gitignore` 和 TRAE 的 Ignore Files 中！：

`bash`

*`# Database`*  
`DB_HOST=postgres_db`  
`DB_PORT=5432`  
`DB_NAME=proxypool`  
`DB_USER=proxyadmin`  
`DB_PASSWORD=secretpassword`

*`# 組合成完整的 URL (在 Docker 容器內使用)`*  
`DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}`

*`# 為宿主機開發提供的 URL`*  
`LOCAL_DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@localhost:${DB_PORT}/${DB_NAME}`

*`# Redis`*

`REDIS_URL=redis://redis_cache:6379/0`

然後在 `docker-compose.yml` 中引入：

`yaml`

`services:`  
  `proxy_api:`  
    `build: .`  
    `env_file:`  
      `- .env # <-- 加載 .env 文件中的環境變數`

    `...`

### **總結**

1. 關鍵規則： 在 Docker 容器內，永遠使用 `服務名稱` 作為 `hostname`。  
2. 安全性： 永遠不要將真實的密碼或 `.env` 文件提交到版本控制 (git)。  
3. 最佳實踐： 使用環境變數來管理資料庫連接字符串，並區分 Docker 內部和宿主機的連接方式。

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
```

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

- `database_config.py` - 智能配置管理器
- `database_usage_example.py` - 完整使用範例
- `.env.example` - 簡化的環境變數範本
- `docker-compose.yml` - 更新的 Docker 配置
- `Docker 資料庫 URL 命名規則優化建議.md` - 詳細優化方案

