#!/usr/bin/env pwsh
# Proxy Crawler System 開發環境停止腳本
# 使用方法: .\stop-dev.ps1

Write-Host "=== Proxy Crawler System 開發環境停止腳本 ===" -ForegroundColor Red
Write-Host ""

# 檢查 docker-compose.dev.yml 是否存在
if (-not (Test-Path "docker-compose.dev.yml")) {
    Write-Host "✗ 找不到 docker-compose.dev.yml 文件" -ForegroundColor Red
    exit 1
}

Write-Host "正在停止開發環境..." -ForegroundColor Yellow

# 停止所有服務（包括 tools profile）
docker-compose -f docker-compose.dev.yml --profile tools down

Write-Host ""
Write-Host "=== 開發環境已停止 ===" -ForegroundColor Green
Write-Host ""
Write-Host "如需完全清理（包括數據卷），請執行:" -ForegroundColor Yellow
Write-Host "docker-compose -f docker-compose.dev.yml down -v --remove-orphans" -ForegroundColor White
Write-Host ""
Write-Host "重新啟動開發環境: .\start-dev.ps1" -ForegroundColor Cyan