#!/usr/bin/env pwsh
# Proxy Crawler System 開發環境啟動腳本
# 使用方法: .\start-dev.ps1

Write-Host "=== Proxy Crawler System 開發環境啟動腳本 ===" -ForegroundColor Green
Write-Host ""

# 檢查 Docker 是否運行
Write-Host "檢查 Docker 服務狀態..." -ForegroundColor Yellow
try {
    docker info | Out-Null
    Write-Host "✓ Docker 服務正常運行" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker 服務未運行，請先啟動 Docker Desktop" -ForegroundColor Red
    exit 1
}

# 檢查 docker-compose.dev.yml 是否存在
if (-not (Test-Path "docker-compose.dev.yml")) {
    Write-Host "✗ 找不到 docker-compose.dev.yml 文件" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "正在啟動開發環境..." -ForegroundColor Yellow
Write-Host "這可能需要幾分鐘時間，請耐心等待..." -ForegroundColor Cyan
Write-Host ""

# 停止並清理現有容器
Write-Host "清理現有容器..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml down --remove-orphans

# 構建並啟動服務
Write-Host "構建並啟動服務..." -ForegroundColor Yellow
docker-compose -f docker-compose.dev.yml up --build -d

# 等待服務啟動
Write-Host "等待服務啟動..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 檢查服務狀態
Write-Host ""
Write-Host "=== 服務狀態檢查 ===" -ForegroundColor Green
docker-compose -f docker-compose.dev.yml ps

Write-Host ""
Write-Host "=== 開發環境已啟動 ===" -ForegroundColor Green
Write-Host "前端服務: http://localhost:5174" -ForegroundColor Cyan
Write-Host "後端 API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "API 文檔: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "PostgreSQL: localhost:5432 (用戶: postgres, 密碼: postgres)" -ForegroundColor Cyan
Write-Host "Redis: localhost:6379" -ForegroundColor Cyan
Write-Host ""
Write-Host "如需啟動管理工具，請執行:" -ForegroundColor Yellow
Write-Host "docker-compose -f docker-compose.dev.yml --profile tools up -d" -ForegroundColor White
Write-Host "  - pgAdmin: http://localhost:5050 (admin@example.com / admin)" -ForegroundColor Cyan
Write-Host "  - Redis Commander: http://localhost:8081" -ForegroundColor Cyan
Write-Host ""
Write-Host "停止開發環境: .\stop-dev.ps1" -ForegroundColor Yellow
Write-Host "查看日誌: docker-compose -f docker-compose.dev.yml logs -f [service_name]" -ForegroundColor Yellow