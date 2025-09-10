# final_cleanup.ps1 - PowerShell cleanup script

param(
    [switch]$WhatIf,
    [switch]$Force,
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "OK $Message" "Green" }
function Write-Info { param([string]$Message) Write-ColorOutput "INFO $Message" "Cyan" }
function Write-Warning { param([string]$Message) Write-ColorOutput "WARN $Message" "Yellow" }

Write-ColorOutput "JasonSpider Project Final Cleanup (PowerShell)" "Magenta"
Write-ColorOutput ("=" * 60) "Gray"

if ($WhatIf) {
    Write-Warning "Running in simulation mode - no files will be deleted"
}

$CleanupItems = @{
    "Temp Files" = @("*.tmp", "*.temp", "*.log", "*.bak", "*.backup", "*.old", "temp_*", "tmp_*", "*~", "*.swp", "*.swo")
    "Python Cache" = @("__pycache__", "*.pyc", "*.pyo", "*.pyd", ".pytest_cache", ".coverage", "htmlcov", "*.egg-info", "build", "dist")
    "IDE Files" = @(".vscode/settings.json", ".idea", "*.sublime-*", ".vs", "*.user", "*.suo")
    "System Files" = @("Thumbs.db", ".DS_Store", "desktop.ini", "*.lnk", "*.url")
    "Duplicate Files" = @("*_copy*", "*_backup*", "*_old*", "*_temp*", "Copy of *", "copy_*")
}

$TotalDeleted = 0
$TotalSize = 0

Write-Info "Starting cleanup of unnecessary files and directories..."
Write-ColorOutput ""

foreach ($Category in $CleanupItems.Keys) {
    Write-Info "Cleaning category: $Category"
    
    $CategoryDeleted = 0
    $CategorySize = 0
    
    foreach ($Pattern in $CleanupItems[$Category]) {
        try {
            $Files = Get-ChildItem -Path . -Recurse -Force -ErrorAction SilentlyContinue | 
                     Where-Object { $_.Name -like $Pattern -or $_.FullName -like "*\$Pattern" }
            
            foreach ($File in $Files) {
                try {
                    $Size = 0
                    if (-not $File.PSIsContainer) {
                        $Size = $File.Length
                    }
                    
                    if ($Verbose) {
                        $RelativePath = $File.FullName.Replace((Get-Location).Path, ".")
                        Write-Host "  DELETE $RelativePath" -ForegroundColor DarkGray
                    }
                    
                    if (-not $WhatIf) {
                        if ($File.PSIsContainer) {
                            Remove-Item -Path $File.FullName -Recurse -Force -ErrorAction SilentlyContinue
                        } else {
                            Remove-Item -Path $File.FullName -Force -ErrorAction SilentlyContinue
                        }
                    }
                    
                    $CategoryDeleted++
                    $CategorySize += $Size
                }
                catch {
                    if ($Verbose) {
                        Write-Warning "Cannot delete: $($File.FullName) - $($_.Exception.Message)"
                    }
                }
            }
        }
        catch {
            if ($Verbose) {
                Write-Warning "Error searching pattern '$Pattern': $($_.Exception.Message)"
            }
        }
    }
    
    if ($CategoryDeleted -gt 0) {
        $SizeStr = if ($CategorySize -gt 1MB) { "{0:N2} MB" -f ($CategorySize / 1MB) } 
                   elseif ($CategorySize -gt 1KB) { "{0:N2} KB" -f ($CategorySize / 1KB) }
                   else { "$CategorySize bytes" }
        
        Write-Success "$Category`: Deleted $CategoryDeleted items ($SizeStr)"
    } else {
        Write-Info "$Category`: No items found to clean"
    }
    
    $TotalDeleted += $CategoryDeleted
    $TotalSize += $CategorySize
}

Write-Info "Cleaning empty directories..."
$EmptyDirs = 0

try {
    for ($i = 0; $i -lt 3; $i++) {
        $Dirs = Get-ChildItem -Path . -Recurse -Directory -Force -ErrorAction SilentlyContinue |
                Where-Object { 
                    (Get-ChildItem -Path $_.FullName -Force -ErrorAction SilentlyContinue).Count -eq 0 
                } |
                Sort-Object FullName -Descending
        
        foreach ($Dir in $Dirs) {
            $ImportantDirs = @('.git', '.github', 'node_modules', '.venv', 'venv', '__pycache__')
            $Skip = $false
            foreach ($ImportantDir in $ImportantDirs) {
                if ($Dir.FullName -like "*\$ImportantDir*") {
                    $Skip = $true
                    break
                }
            }
            
            if (-not $Skip) {
                try {
                    if ($Verbose) {
                        $RelativePath = $Dir.FullName.Replace((Get-Location).Path, ".")
                        Write-Host "  FOLDER $RelativePath" -ForegroundColor DarkGray
                    }
                    
                    if (-not $WhatIf) {
                        Remove-Item -Path $Dir.FullName -Force -ErrorAction SilentlyContinue
                    }
                    $EmptyDirs++
                }
                catch {
                    if ($Verbose) {
                        Write-Warning "Cannot delete empty directory: $($Dir.FullName)"
                    }
                }
            }
        }
        
        if ($Dirs.Count -eq 0) { break }
    }
}
catch {
    Write-Warning "Error cleaning empty directories: $($_.Exception.Message)"
}

if ($EmptyDirs -gt 0) {
    Write-Success "Empty directories: Deleted $EmptyDirs empty directories"
} else {
    Write-Info "Empty directories: No empty directories found"
}

Write-Info "Checking duplicate configuration files..."
$DuplicateConfigs = @(
    @{ Original = "requirements.txt"; Duplicates = @("requirements_backup.txt", "requirements.bak") }
    @{ Original = "Dockerfile"; Duplicates = @("Dockerfile.backup", "Dockerfile.old") }
    @{ Original = "docker-compose.yml"; Duplicates = @("docker-compose.backup.yml", "docker-compose.old.yml") }
    @{ Original = ".env"; Duplicates = @(".env.backup", ".env.old", ".env.bak") }
)

$ConfigDeleted = 0
foreach ($Config in $DuplicateConfigs) {
    if (Test-Path $Config.Original) {
        foreach ($Duplicate in $Config.Duplicates) {
            if (Test-Path $Duplicate) {
                try {
                    if ($Verbose) {
                        Write-Host "  DUPLICATE $Duplicate (keeping $($Config.Original))" -ForegroundColor DarkGray
                    }
                    
                    if (-not $WhatIf) {
                        Remove-Item -Path $Duplicate -Force
                    }
                    $ConfigDeleted++
                }
                catch {
                    Write-Warning "Cannot delete duplicate config: $Duplicate"
                }
            }
        }
    }
}

if ($ConfigDeleted -gt 0) {
    Write-Success "Duplicate configs: Deleted $ConfigDeleted duplicate files"
}

if (Test-Path ".git") {
    Write-Info "Cleaning Git cache..."
    try {
        if (-not $WhatIf) {
            & git gc --prune=now --aggressive 2>$null
            & git remote prune origin 2>$null
        }
        Write-Success "Git cache cleaned"
    }
    catch {
        Write-Warning "Git cleanup failed: $($_.Exception.Message)"
    }
}

Write-ColorOutput ""
Write-ColorOutput "Cleanup Summary" "Magenta"
Write-ColorOutput ("-" * 30) "Gray"

$TotalSizeStr = if ($TotalSize -gt 1MB) { "{0:N2} MB" -f ($TotalSize / 1MB) } 
                elseif ($TotalSize -gt 1KB) { "{0:N2} KB" -f ($TotalSize / 1KB) }
                else { "$TotalSize bytes" }

Write-Success "Total deleted: $($TotalDeleted + $EmptyDirs + $ConfigDeleted) items"
Write-Success "Space freed: $TotalSizeStr"

if ($WhatIf) {
    Write-Warning "This was a simulation - no files were actually deleted"
    Write-Info "To actually run cleanup, use: .\final_cleanup.ps1"
}

Write-ColorOutput ""
Write-ColorOutput "Suggested next steps:" "Yellow"
Write-Host "1. Check project structure: " -NoNewline; Write-Host "Get-ChildItem -Recurse -Directory | Select-Object Name" -ForegroundColor Cyan
Write-Host "2. Verify Git status: " -NoNewline; Write-Host "git status" -ForegroundColor Cyan
Write-Host "3. Test project run: " -NoNewline; Write-Host "uv run python src/main.py" -ForegroundColor Cyan
Write-Host "4. Push to GitHub: " -NoNewline; Write-Host ".\execute_full_push.ps1" -ForegroundColor Cyan

Write-ColorOutput ""
Write-Success "Cleanup complete! Project is ready for final push."
