# API 金鑰配置指南

本指南說明如何配置 JasonSpider 代理管理系統的外部 API 金鑰。

## 🔑 支援的 API 服務

### 1. ProxyScrape API

- **用途**: 獲取免費代理列表
- **獲取地址**: https://proxyscrape.com/api
- **費用**: 免費（有速率限制）
- **環境變量**: `PROXYSCRAPE_API_KEY`

### 2. GitHub Personal Access Token

- **用途**: 從 GitHub 開源專案獲取代理列表
- **獲取地址**: https://github.com/settings/tokens
- **費用**: 免費
- **權限**: `public_repo` (讀取公開倉庫)
- **環境變量**: `GITHUB_TOKEN`

### 3. Shodan API

- **用途**: 使用 Shodan 搜尋引擎發現代理服務
- **獲取地址**: https://account.shodan.io/
- **費用**: 需要購買 API 額度
- **環境變量**: `SHODAN_API_KEY`

### 4. Censys API

- **用途**: 使用 Censys 搜尋引擎發現代理服務
- **獲取地址**: https://censys.io/account/api
- **費用**: 免費版本每月 250 次搜尋，付費版本無限制
- **環境變量**: `CENSYS_API_ID`, `CENSYS_API_SECRET`

## 🚀 快速配置

### 方法 1: 使用配置工具（推薦）

```bash
# 運行交互式配置工具
python setup_api_config.py
```

### 方法 2: 環境變量配置

1. 複製環境變量模板：

```bash
cp env.example .env
```

2. 編輯 `.env` 文件，填入您的 API 金鑰：

```bash
# ProxyScrape API 金鑰
PROXYSCRAPE_API_KEY=your_proxyscrape_api_key_here

# GitHub Personal Access Token
GITHUB_TOKEN=your_github_token_here

# Shodan API 金鑰
SHODAN_API_KEY=your_shodan_api_key_here

# Censys API 憑證
CENSYS_API_ID=your_censys_api_id_here
CENSYS_API_SECRET=your_censys_api_secret_here
```

3. 載入環境變量：

```bash
# Linux/macOS
source .env

# Windows
# 在 PowerShell 中運行
Get-Content .env | ForEach-Object { if($_ -match "^([^#][^=]+)=(.*)$") { [Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }
```

### 方法 3: 配置文件

1. 複製配置模板：

```bash
cp config/api_config_template.yaml config/api_config.yaml
```

2. 編輯 `config/api_config.yaml` 文件，填入您的 API 金鑰：

```yaml
api:
  proxyscrape_api_key: "your_proxyscrape_api_key_here"
  github_token: "your_github_token_here"
  shodan_api_key: "your_shodan_api_key_here"
  censys_api_id: "your_censys_api_id_here"
  censys_api_secret: "your_censys_api_secret_here"
```

## 🔒 安全配置

### 加密存儲 API 金鑰

系統支援加密存儲 API 金鑰，確保敏感信息安全：

```python
from src.proxy_manager.api_config_manager import ApiConfigManager

# 創建配置管理器
manager = ApiConfigManager()

# 添加加密的 API 金鑰
manager.add_api_key(
    name="shodan_api_key",
    key="your_api_key_here",
    description="Shodan API 金鑰",
    encrypt=True  # 加密存儲
)
```

### 環境變量加密金鑰

設置加密金鑰用於加密存儲：

```bash
# 生成隨機加密金鑰
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 設置環境變量
export PROXY_MANAGER_ENCRYPTION_KEY="your_encryption_key_here"
```

## 📋 配置驗證

### 驗證所有 API 金鑰

```python
from src.proxy_manager.api_config_manager import ApiConfigManager

manager = ApiConfigManager()

# 列出所有金鑰
keys = manager.list_api_keys()
for key_info in keys:
    print(f"{key_info['name']}: {key_info['key_preview']}")

# 驗證特定金鑰
is_valid = manager.validate_api_key("shodan_api_key")
print(f"Shodan API 金鑰有效: {is_valid}")
```

### 使用配置工具驗證

```bash
python setup_api_config.py
# 選擇選項 4: 驗證現有配置
```

## 🔧 進階配置

### 自定義配置目錄

```python
from pathlib import Path
from src.proxy_manager.api_config_manager import ApiConfigManager

# 使用自定義配置目錄
config_dir = Path("/path/to/your/config")
manager = ApiConfigManager(config_dir)
```

### 導出配置

```python
# 導出到 YAML 文件
manager.export_to_config("my_api_config.yaml")

# 獲取配置字典
config_dict = manager.get_config_dict()
```

## 🚨 故障排除

### 常見問題

1. **API 金鑰無效**

   - 檢查金鑰格式是否正確
   - 確認金鑰是否過期
   - 驗證 API 服務是否正常

2. **環境變量未載入**

   - 確認 `.env` 文件存在
   - 檢查環境變量名稱是否正確
   - 重新載入環境變量

3. **配置文件格式錯誤**
   - 檢查 YAML 語法是否正確
   - 確認縮進是否一致
   - 驗證 JSON 格式是否有效

### 日誌調試

啟用詳細日誌來調試配置問題：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 運行配置管理器
from src.proxy_manager.api_config_manager import ApiConfigManager
manager = ApiConfigManager()
```

## 📚 相關文檔

- [ProxyManager 配置文檔](src/proxy_manager/config.py)
- [API 配置管理器文檔](src/proxy_manager/api_config_manager.py)
- [環境變量配置示例](env.example)
- [配置文件模板](config/api_config_template.yaml)

## 🤝 支援

如果您在配置過程中遇到問題，請：

1. 檢查本指南的故障排除部分
2. 查看系統日誌獲取詳細錯誤信息
3. 確認 API 服務的官方文檔
4. 聯繫開發團隊獲取支援
