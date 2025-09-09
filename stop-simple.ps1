#!/usr/bin/env pwsh
# 簡化版 Docker 開發環境停止腳本

Write-Host "🛑 停止簡化版 Proxy Crawler System" -ForegroundColor Red
Write-Host "===========================================" -ForegroundColor Red

# 檢查 Docker 是否運行
Write-Host "📋 檢查 Docker 狀態..." -ForegroundColor Yellow
try {
    docker version | Out-Null
    Write-Host "✅ Docker 運行正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 未運行，無需停止服務" -ForegroundColor Yellow
    exit 0
}

# 檢查簡化版配置文件
if (-not (Test-Path "docker-compose.simple.yml")) {
    Write-Host "❌ 找不到 docker-compose.simple.yml 文件" -ForegroundColor Red
    exit 1
}

# 顯示當前運行的服務
Write-Host "📊 當前運行的簡化版服務:" -ForegroundColor Cyan
docker-compose -f docker-compose.simple.yml ps

Write-Host ""
$confirm = Read-Host "確定要停止所有簡化版服務嗎？(y/N)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "❌ 操作已取消" -ForegroundColor Yellow
    exit 0
}

# 停止服務
Write-Host "🛑 正在停止簡化版服務..." -ForegroundColor Yellow
docker-compose -f docker-compose.simple.yml down

if ($LASTEXITCODE -eq 0) {
    Write-Host "" 
    Write-Host "✅ 簡化版服務已成功停止！" -ForegroundColor Green
    Write-Host "===========================================" -ForegroundColor Green
    Write-Host ""
    
    # 詢問是否清理資源
    $cleanup = Read-Host "是否同時清理相關資源？(容器、網路等) (y/N)"
    if ($cleanup -eq 'y' -or $cleanup -eq 'Y') {
        Write-Host "🧹 清理相關資源..." -ForegroundColor Yellow
        
        # 移除停止的容器
        docker-compose -f docker-compose.simple.yml down --remove-orphans
        
        # 清理未使用的網路
        docker network prune -f
        
        Write-Host "✅ 資源清理完成" -ForegroundColor Green
    }
    
    # 詢問是否清理數據卷
    $cleanVolumes = Read-Host "是否清理數據卷？(這將刪除資料庫數據) (y/N)"
    if ($cleanVolumes -eq 'y' -or $cleanVolumes -eq 'Y') {
        Write-Host "⚠️  正在清理數據卷..." -ForegroundColor Red
        docker-compose -f docker-compose.simple.yml down --volumes
        Write-Host "✅ 數據卷已清理" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "💡 提示:" -ForegroundColor Cyan
    Write-Host "  • 重新啟動: .\start-simple.ps1" -ForegroundColor White
    Write-Host "  • 查看狀態: docker-compose -f docker-compose.simple.yml ps" -ForegroundColor White
    Write-Host "  • 查看日誌: docker-compose -f docker-compose.simple.yml logs" -ForegroundColor White
    
} else {
    Write-Host "" 
    Write-Host "❌ 停止服務時發生錯誤！" -ForegroundColor Red
    Write-Host "請手動檢查並停止相關容器:" -ForegroundColor Yellow
    Write-Host "  docker ps" -ForegroundColor White
    Write-Host "  docker stop <container_id>" -ForegroundColor White
    
    exit 1
}

Write-Host "" 
Write-Host "按任意鍵繼續..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")