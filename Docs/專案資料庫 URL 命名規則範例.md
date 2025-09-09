### **專案資料庫 URL 命名規則**

#### **1\. PostgreSQL 資料庫**

格式：

`bash`

`postgresql://用戶名:密碼@主機:端口/資料庫名`

專案規定：

`bash`

*`# Docker 容器內連接（標準用法）`*  
`postgresql://proxyadmin:secret123@postgres_db:5432/proxypool`

*`# 宿主機本地開發連接`*  
`postgresql://proxyadmin:secret123@localhost:5432/proxypool`

*`# 使用 asyncpg 驅動（推薦用於異步）`*

`postgresql+asyncpg://proxyadmin:secret123@postgres_db:5432/proxypool`

#### **2\. Redis 資料庫**

格式：

`bash`

`redis://[密碼@]主機:端口[/數據庫編號]`

專案規定：

`bash`

*`# Docker 容器內連接`*  
`redis://redis_cache:6379/0`

*`# 宿主機本地開發連接`*    
`redis://localhost:6379/0`

*`# 帶密碼連接（如需）`*

`redis://:yourpassword@redis_cache:6379/0`

#### **3\. 環境變數配置 (.env)**

`bash`

*`# 必須統一的認證資訊`*  
`DB_USER=proxyadmin`  
`DB_PASSWORD=secret123`  
`DB_NAME=proxypool`

*`# 根據環境選擇主機`*  
`DEV_DB_HOST=localhost`  
`DOCKER_DB_HOST=postgres_db`

*`# 完整的連接字符串`*  
`DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DOCKER_DB_HOST}:5432/${DB_NAME}`  
`LOCAL_DB_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DEV_DB_HOST}:5432/${DB_NAME}`

`REDIS_URL=redis://redis_cache:6379/0`

### **核心規則總結**

1. 主機名稱決定連接位置：  
   * `postgres_db` / `redis_cache` → Docker 容器內連接  
   * `localhost` → 宿主機本地連接  
2. 認證資訊必須統一：  
   * 用戶名：`proxyadmin`  
   * 密碼：`secret123`  
   * 資料庫：`proxypool`  
3. 端口固定：  
   * PostgreSQL：`5432`  
   * Redis：`6379`  
4. 驅動程式選擇：  
   * 同步操作：`postgresql://`  
   * 異步優化：`postgresql+asyncpg://`

### **使用範例**

`python`

*`# 在 Docker 容器內的應用使用`*  
`DATABASE_URL = "postgresql://proxyadmin:secret123@postgres_db:5432/proxypool"`  
`REDIS_URL = "redis://redis_cache:6379/0"`

*`# 在本機開發時使用`*    
`DATABASE_URL = "postgresql://proxyadmin:secret123@localhost:5432/proxypool"`

`REDIS_URL = "redis://localhost:6379/0"`

記住：Docker 容器內用服務名，本機開發用 localhost。  
