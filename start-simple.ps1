#!/usr/bin/env pwsh
# 簡化版 Docker 開發環境啟動腳本
# 使用精簡配置，大幅降低資源消耗和複雜度

Write-Host "🚀 啟動簡化版 Proxy Crawler System" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Green

# 檢查 Docker 是否運行
Write-Host "📋 檢查 Docker 狀態..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker 運行正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未運行或未安裝，請先啟動 Docker Desktop" -ForegroundColor Red
    exit 1
}

# 檢查簡化版配置文件
if (-not (Test-Path "docker-compose.simple.yml")) {
    Write-Host "❌ 找不到 docker-compose.simple.yml 文件" -ForegroundColor Red
    exit 1
}

# 停止可能運行的服務
Write-Host "🛑 停止現有服務..." -ForegroundColor Yellow
docker-compose -f docker-compose.simple.yml down --remove-orphans

# 清理舊的容器和映像（可選）
$cleanup = Read-Host "是否清理舊的容器和映像？這將釋放磁碟空間但需要重新下載 (y/N)"
if ($cleanup -eq 'y' -or $cleanup -eq 'Y') {
    Write-Host "🧹 清理舊資源..." -ForegroundColor Yellow
    docker system prune -f
    docker-compose -f docker-compose.simple.yml down --volumes --rmi all
}

# 創建必要的目錄
Write-Host "📁 創建必要目錄..." -ForegroundColor Yellow
$directories = @(
    "logs",
    "data",
    "data/raw",
    "data/processed", 
    "data/transformed",
    "config"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✅ 創建目錄: $dir" -ForegroundColor Green
    }
}

# 檢查環境變數文件
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "📝 複製環境變數範例文件..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "  ✅ 已創建 .env 文件，請根據需要修改配置" -ForegroundColor Green
    } else {
        Write-Host "⚠️  未找到 .env 文件，將使用預設配置" -ForegroundColor Yellow
    }
}

# 構建和啟動服務
Write-Host "🔨 構建並啟動簡化版服務..." -ForegroundColor Yellow
Write-Host "這可能需要幾分鐘時間，請耐心等待..." -ForegroundColor Cyan

# 啟動核心服務（不包含可選工具）
docker-compose -f docker-compose.simple.yml up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "🎉 簡化版服務啟動成功！" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 服務狀態:" -ForegroundColor Cyan
    docker-compose -f docker-compose.simple.yml ps
    Write-Host ""
    Write-Host "🌐 可用服務:" -ForegroundColor Cyan
    Write-Host "  • 主應用 API:     http://localhost:8000" -ForegroundColor White
    Write-Host "  • API 文檔:       http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  • 系統健康檢查:   http://localhost:8000/health" -ForegroundColor White
    Write-Host "  • PostgreSQL:     localhost:5432" -ForegroundColor White
    Write-Host "  • Redis:          localhost:6379" -ForegroundColor White
    Write-Host ""
    Write-Host "🛠️  可選管理工具 (需要額外啟動):" -ForegroundColor Cyan
    Write-Host "  • pgAdmin:        docker-compose -f docker-compose.simple.yml --profile tools up pgadmin -d" -ForegroundColor Gray
    Write-Host "  • 然後訪問:       http://localhost:5050" -ForegroundColor Gray
    Write-Host ""
    Write-Host "📝 常用命令:" -ForegroundColor Cyan
    Write-Host "  • 查看日誌:       docker-compose -f docker-compose.simple.yml logs -f" -ForegroundColor White
    Write-Host "  • 停止服務:       .\stop-simple.ps1" -ForegroundColor White
    Write-Host "  • 重啟服務:       docker-compose -f docker-compose.simple.yml restart" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 提示: 這是簡化版配置，資源消耗約為完整版的 30%" -ForegroundColor Yellow
    Write-Host "如需完整功能，請使用 .\start-dev.ps1" -ForegroundColor Yellow
    
} else {
    Write-Host "" 
    Write-Host "❌ 服務啟動失敗！" -ForegroundColor Red
    Write-Host "請檢查以下內容:" -ForegroundColor Yellow
    Write-Host "  1. Docker Desktop 是否正常運行" -ForegroundColor White
    Write-Host "  2. 端口 5432, 6379, 8000 是否被占用" -ForegroundColor White
    Write-Host "  3. 磁碟空間是否充足" -ForegroundColor White
    Write-Host ""
    Write-Host "查看詳細錯誤信息:" -ForegroundColor Yellow
    Write-Host "  docker-compose -f docker-compose.simple.yml logs" -ForegroundColor White
    
    exit 1
}

Write-Host "" 
Write-Host "按任意鍵繼續..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")