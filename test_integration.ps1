# URL2Parquet 整合測試腳本
# 用於測試前端與後端 API 的整合功能

Write-Host "🚀 開始 URL2Parquet 整合測試" -ForegroundColor Green
Write-Host "=" * 50

# 檢查 Python 環境
Write-Host "🔍 檢查 Python 環境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python 版本: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Python 未安裝或不在 PATH 中" -ForegroundColor Red
    exit 1
}

# 檢查虛擬環境
Write-Host "🔍 檢查虛擬環境..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "✅ 找到 .venv 虛擬環境" -ForegroundColor Green
    $env:VIRTUAL_ENV = ".venv"
    $env:PATH = ".venv\Scripts;$env:PATH"
}
else {
    Write-Host "⚠️ 未找到 .venv 虛擬環境，使用系統 Python" -ForegroundColor Yellow
}

# 檢查依賴
Write-Host "🔍 檢查依賴..." -ForegroundColor Yellow
try {
    python -c "import httpx, pandas, pyarrow" 2>$null
    Write-Host "✅ 所需依賴已安裝" -ForegroundColor Green
}
catch {
    Write-Host "❌ 缺少依賴，正在安裝..." -ForegroundColor Red
    pip install httpx pandas pyarrow
}

# 檢查後端服務
Write-Host "🔍 檢查後端服務..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 後端服務運行正常" -ForegroundColor Green
    }
    else {
        Write-Host "❌ 後端服務響應異常: $($response.StatusCode)" -ForegroundColor Red
        Write-Host "請先啟動後端服務: uv run python run_server.py" -ForegroundColor Yellow
        exit 1
    }
}
catch {
    Write-Host "❌ 無法連接到後端服務" -ForegroundColor Red
    Write-Host "請先啟動後端服務: uv run python run_server.py" -ForegroundColor Yellow
    exit 1
}

# 運行測試
Write-Host "🧪 運行整合測試..." -ForegroundColor Yellow
Write-Host ""

try {
    python test_url2parquet_integration.py
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host ""
        Write-Host "🎉 測試完成！所有功能正常" -ForegroundColor Green
    }
    else {
        Write-Host ""
        Write-Host "❌ 測試失敗，退出碼: $exitCode" -ForegroundColor Red
    }
}
catch {
    Write-Host ""
    Write-Host "❌ 測試執行失敗: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=" * 50
Write-Host "測試完成" -ForegroundColor Green
