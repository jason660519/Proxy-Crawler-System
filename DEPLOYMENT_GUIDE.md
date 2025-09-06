# 部署指南

本指南將詳細說明如何在不同環境中部署 JasonSpider 代理管理系統。

## 📋 目錄

- [系統要求](#系統要求)
- [安裝步驟](#安裝步驟)
- [配置設置](#配置設置)
- [運行方式](#運行方式)
- [Docker 部署](#docker-部署)
- [生產環境部署](#生產環境部署)
- [監控和維護](#監控和維護)
- [故障排除](#故障排除)

## 系統要求

### 最低要求

| 組件     | 最低版本 | 推薦版本 |
| -------- | -------- | -------- |
| Python   | 3.11+    | 3.12+    |
| 記憶體   | 2GB      | 8GB+     |
| 磁盤空間 | 1GB      | 10GB+    |
| 網路     | 寬頻連接 | 高速連接 |

### 依賴服務

| 服務       | 用途     | 必需性 |
| ---------- | -------- | ------ |
| PostgreSQL | 數據存儲 | 可選   |
| Redis      | 緩存     | 可選   |
| Docker     | 容器化   | 可選   |

## 安裝步驟

### 1. 克隆專案

```bash
git clone https://github.com/your-org/jason-spider.git
cd jason-spider
```

### 2. 創建虛擬環境

```bash
# 使用 venv
python -m venv venv

# 激活虛擬環境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3. 安裝依賴

```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv（推薦）
uv pip install -r requirements.txt
```

### 4. 驗證安裝

```bash
python -c "import src.proxy_manager; print('安裝成功')"
```

## 配置設置

### 1. 環境變量配置

創建 `.env` 文件：

```bash
cp env.example .env
```

編輯 `.env` 文件：

```env
# API 金鑰配置
GITHUB_TOKEN=your_github_token_here
SHODAN_API_KEY=your_shodan_api_key_here
CENSYS_API_ID=your_censys_api_id_here
CENSYS_API_SECRET=your_censys_api_secret_here

# 數據庫配置
DATABASE_URL=postgresql://user:password@localhost:5432/jason_spider
REDIS_URL=redis://localhost:6379/0

# 系統配置
LOG_LEVEL=INFO
MAX_CONCURRENT_SCANS=100
MAX_CONCURRENT_VALIDATIONS=50
```

### 2. 配置文件設置

```bash
# 創建配置目錄
mkdir -p config

# 生成配置文件
python setup_api_config.py template
```

### 3. 數據目錄設置

```bash
# 創建數據目錄
mkdir -p data/proxy_manager
mkdir -p data/backups
mkdir -p logs
```

## 運行方式

### 1. 直接運行

```bash
# 基本運行
python src/main.py

# 指定配置文件
python src/main.py --config config/production.yaml

# 指定日誌級別
python src/main.py --log-level DEBUG
```

### 2. 使用代理管理器

```bash
# 啟動代理管理器服務
python src/proxy_manager/server.py

# 指定端口
python src/proxy_manager/server.py --port 8080
```

### 3. 使用配置工具

```bash
# 交互式配置
python setup_api_config.py interactive

# 驗證配置
python setup_api_config.py validate

# 顯示配置
python setup_api_config.py show
```

## Docker 部署

### 1. 使用 Docker Compose（推薦）

創建 `docker-compose.yml`：

```yaml
version: "3.8"

services:
  jason-spider:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - SHODAN_API_KEY=${SHODAN_API_KEY}
      - CENSYS_API_ID=${CENSYS_API_ID}
      - CENSYS_API_SECRET=${CENSYS_API_SECRET}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: jason_spider
      POSTGRES_USER: jason_spider
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

創建 `Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴文件
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案文件
COPY . .

# 創建數據目錄
RUN mkdir -p data/proxy_manager data/backups logs

# 設置權限
RUN chmod +x src/main.py

# 暴露端口
EXPOSE 8000

# 啟動命令
CMD ["python", "src/main.py"]
```

### 2. 構建和運行

```bash
# 構建鏡像
docker-compose build

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f

# 停止服務
docker-compose down
```

### 3. 使用 Docker 單容器

```bash
# 構建鏡像
docker build -t jason-spider .

# 運行容器
docker run -d \
  --name jason-spider \
  -p 8000:8000 \
  -e GITHUB_TOKEN=your_token \
  -v $(pwd)/data:/app/data \
  jason-spider
```

## 生產環境部署

### 1. 使用 systemd（Linux）

創建服務文件 `/etc/systemd/system/jason-spider.service`：

```ini
[Unit]
Description=JasonSpider Proxy Manager
After=network.target

[Service]
Type=simple
User=jason-spider
WorkingDirectory=/opt/jason-spider
Environment=PATH=/opt/jason-spider/venv/bin
ExecStart=/opt/jason-spider/venv/bin/python src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

啟動服務：

```bash
sudo systemctl daemon-reload
sudo systemctl enable jason-spider
sudo systemctl start jason-spider
```

### 2. 使用 Nginx 反向代理

創建 Nginx 配置 `/etc/nginx/sites-available/jason-spider`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 靜態文件
    location /static/ {
        alias /opt/jason-spider/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

啟用配置：

```bash
sudo ln -s /etc/nginx/sites-available/jason-spider /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 使用 SSL/TLS

使用 Let's Encrypt：

```bash
# 安裝 Certbot
sudo apt install certbot python3-certbot-nginx

# 獲取證書
sudo certbot --nginx -d your-domain.com

# 自動續期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

## 監控和維護

### 1. 日誌監控

```bash
# 查看實時日誌
tail -f logs/jason-spider.log

# 查看錯誤日誌
grep ERROR logs/jason-spider.log

# 日誌輪轉
sudo logrotate -f /etc/logrotate.d/jason-spider
```

### 2. 性能監控

```bash
# 檢查系統資源
htop
iostat -x 1

# 檢查 Python 進程
ps aux | grep python

# 檢查記憶體使用
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'記憶體使用: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

### 3. 健康檢查

創建健康檢查腳本 `health_check.py`：

```python
#!/usr/bin/env python3
import requests
import sys

def check_health():
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ 服務健康")
            return True
        else:
            print(f"❌ 服務異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康檢查失敗: {e}")
        return False

if __name__ == "__main__":
    success = check_health()
    sys.exit(0 if success else 1)
```

設置定時檢查：

```bash
# 添加到 crontab
*/5 * * * * /opt/jason-spider/health_check.py
```

### 4. 備份策略

創建備份腳本 `backup.sh`：

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/jason-spider"
DATE=$(date +%Y%m%d_%H%M%S)

# 創建備份目錄
mkdir -p $BACKUP_DIR

# 備份數據
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# 備份配置
cp -r config/ $BACKUP_DIR/config_$DATE/

# 清理舊備份（保留 30 天）
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "備份完成: $BACKUP_DIR/data_$DATE.tar.gz"
```

設置定時備份：

```bash
# 每天凌晨 2 點備份
0 2 * * * /opt/jason-spider/backup.sh
```

## 故障排除

### 1. 常見問題

#### 問題：服務無法啟動

**症狀**：服務啟動失敗，日誌顯示錯誤

**解決方案**：

```bash
# 檢查 Python 版本
python --version

# 檢查依賴
pip check

# 檢查配置文件
python setup_api_config.py validate

# 檢查端口占用
netstat -tlnp | grep :8000
```

#### 問題：代理獲取失敗

**症狀**：無法獲取代理，API 錯誤

**解決方案**：

```bash
# 檢查 API 金鑰
python setup_api_config.py show

# 測試網路連接
curl -I https://api.github.com

# 檢查防火牆
sudo ufw status
```

#### 問題：記憶體使用過高

**症狀**：系統記憶體使用率過高

**解決方案**：

```bash
# 調整並發參數
export MAX_CONCURRENT_SCANS=50
export MAX_CONCURRENT_VALIDATIONS=25

# 重啟服務
sudo systemctl restart jason-spider
```

### 2. 調試技巧

#### 啟用調試模式

```bash
# 設置調試環境變量
export LOG_LEVEL=DEBUG
export DEBUG_MODE=true

# 運行調試版本
python src/main.py --debug
```

#### 檢查內部狀態

```python
# 連接到運行中的服務
import requests
response = requests.get('http://localhost:8000/stats')
print(response.json())
```

#### 性能分析

```bash
# 使用 cProfile 分析性能
python -m cProfile -o profile.prof src/main.py

# 分析結果
python -c "
import pstats
p = pstats.Stats('profile.prof')
p.sort_stats('cumulative').print_stats(10)
"
```

### 3. 緊急恢復

#### 數據恢復

```bash
# 從備份恢復數據
tar -xzf /opt/backups/jason-spider/data_20250107_020000.tar.gz

# 恢復配置
cp -r /opt/backups/jason-spider/config_20250107_020000/* config/
```

#### 服務重置

```bash
# 停止服務
sudo systemctl stop jason-spider

# 清理數據
rm -rf data/proxy_manager/*

# 重新初始化
python setup_api_config.py interactive

# 啟動服務
sudo systemctl start jason-spider
```

## 安全考慮

### 1. API 金鑰安全

```bash
# 設置文件權限
chmod 600 .env
chmod 600 config/api_config.yaml

# 使用環境變量而非配置文件
export GITHUB_TOKEN=your_token
```

### 2. 網路安全

```bash
# 配置防火牆
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 使用 HTTPS
# 配置 SSL 證書
```

### 3. 數據安全

```bash
# 加密敏感數據
python -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(f'加密金鑰: {key.decode()}')
"
```

## 更新和升級

### 1. 版本更新

```bash
# 備份當前版本
cp -r /opt/jason-spider /opt/jason-spider.backup

# 拉取新版本
cd /opt/jason-spider
git pull origin main

# 更新依賴
pip install -r requirements.txt

# 重啟服務
sudo systemctl restart jason-spider
```

### 2. 數據遷移

```bash
# 導出當前數據
python src/main.py --export data/backup.json

# 更新後導入數據
python src/main.py --import data/backup.json
```

---

**文檔版本**: v1.0.0  
**最後更新**: 2025-01-07  
**維護者**: AI Assistant (TRAE)
