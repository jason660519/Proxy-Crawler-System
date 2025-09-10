# execute_full_push.ps1 - PowerShell GitHub Push Script

param(
    [switch]$WhatIf,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Write-ColorOutput {
    param([string]$Message, [string]$Color = "White")
    Write-Host $Message -ForegroundColor $Color
}

function Write-Success { param([string]$Message) Write-ColorOutput "OK $Message" "Green" }
function Write-Info { param([string]$Message) Write-ColorOutput "INFO $Message" "Cyan" }
function Write-Warning { param([string]$Message) Write-ColorOutput "WARN $Message" "Yellow" }
function Write-Error { param([string]$Message) Write-ColorOutput "ERROR $Message" "Red" }

Write-ColorOutput "JasonSpider Complete GitHub Push Process (PowerShell)" "Magenta"
Write-ColorOutput "Target Repository: https://github.com/jason660519/Proxy-Crawler-System" "Gray"
Write-ColorOutput ("=" * 60) "Gray"

$REPO_URL = "https://github.com/jason660519/Proxy-Crawler-System.git"

# Step 1: Update README badges
Write-ColorOutput ""
Write-Info "Step 1/3: Updating README.md badges..."
Write-ColorOutput ("=" * 30) "Gray"

if (Test-Path "README.md") {
    Copy-Item "README.md" "README.md.backup" -Force
    Write-Success "Backed up original README.md"
}

$NewReadmeContent = @"
# JasonSpider - Proxy Crawler and Management System

![GitHub Stars](https://img.shields.io/github/stars/jason660519/Proxy-Crawler-System?style=flat-square)
![GitHub Forks](https://img.shields.io/github/forks/jason660519/Proxy-Crawler-System?style=flat-square)
![GitHub Issues](https://img.shields.io/github/issues/jason660519/Proxy-Crawler-System?style=flat-square)
![GitHub License](https://img.shields.io/github/license/jason660519/Proxy-Crawler-System?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-Ready-009688?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square)
![CI/CD](https://img.shields.io/github/actions/workflow/status/jason660519/Proxy-Crawler-System/ci.yml?branch=main&style=flat-square)

An observable, modular, and scalable "Proxy Crawler + Smart Proxy Pool + HTML to Markdown" integrated platform that provides API services, metrics monitoring, and elastic scaling capabilities to help build reliable web data extraction infrastructure.

> Quick Start: ``git clone https://github.com/jason660519/Proxy-Crawler-System.git && cd Proxy-Crawler-System && uv sync && uv run python src/main.py``

"@

if (Test-Path "README.md.backup") {
    $OriginalContent = Get-Content "README.md.backup" -Raw
    $Lines = $OriginalContent -split "`n"
    
    $ContentToKeep = $Lines | Where-Object { 
        $_ -notmatch "^# JasonSpider" -and 
        $_ -notmatch "^An observable" 
    } | Select-Object -Skip 2
    
    if ($ContentToKeep) {
        $NewReadmeContent += "`n" + ($ContentToKeep -join "`n")
    }
}

$NewReadmeContent | Out-File -FilePath "README.md" -Encoding UTF8 -Force
Write-Success "README.md badges updated"

# Step 2: Git operations and push
Write-ColorOutput ""
Write-Info "Step 2/3: Git operations and push..."
Write-ColorOutput ("=" * 30) "Gray"

try {
    & git rev-parse --git-dir 2>$null | Out-Null
}
catch {
    Write-Info "Initializing Git repository..."
    & git init
    Write-Success "Git repository initialized"
}

Write-ColorOutput ""
Write-Info "Checking current status..."
& git status --short

Write-ColorOutput ""
Write-Info "Adding all files..."
if (-not $WhatIf) {
    & git add .
}

Write-ColorOutput ""
Write-Info "Files to be committed (first 20):"
$StagedFiles = & git diff --cached --name-status
$StagedFiles | Select-Object -First 20 | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }

$TotalFiles = ($StagedFiles | Measure-Object).Count
if ($TotalFiles -gt 20) {
    Write-Host "... and $($TotalFiles - 20) more files" -ForegroundColor DarkGray
}
Write-Info "Total: $TotalFiles files"

Write-ColorOutput ""
Write-Info "Committing changes..."

$CommitMessage = @"
feat: Reorganize JasonSpider project structure and push to GitHub

Architecture Reorganization:
- Establish modular directory structure (src/common, tests/, tools/, docs/, scripts/)
- Move test files to tests/ directory
- Reorganize documentation structure, unified to docs/ directory
- Create common modules (config, logging, utils)

File Organization:
- Update all file path references and import statements
- Clean up redundant and invalid files
- Optimize Docker and deployment configuration

Documentation Updates:
- Rewrite README.md to provide clear project navigation
- Add GitHub badges and quick start guide
- Create complete API documentation and architecture description

Deployment Optimization:
- Update Docker configuration to support new structure
- Create automated deployment scripts
- Add health checks and monitoring configuration

GitHub Integration:
- Set up CI/CD workflows
- Add code quality checks
- Configure automated testing and deployment

This reorganization significantly improves project maintainability, modularity, and development experience.
"@

try {
    $HasChanges = & git diff --cached --quiet; $LASTEXITCODE -ne 0
    if ($HasChanges -and -not $WhatIf) {
        & git commit -m $CommitMessage
        Write-Success "Changes committed"
    } elseif (-not $HasChanges) {
        Write-Warning "No changes to commit"
    }
}
catch {
    Write-Error "Commit failed: $($_.Exception.Message)"
    exit 1
}

Write-ColorOutput ""
Write-Info "Setting up remote repository..."

try {
    $CurrentUrl = & git remote get-url origin 2>$null
    if ($CurrentUrl -ne $REPO_URL) {
        Write-Info "Updating remote repository URL..."
        & git remote set-url origin $REPO_URL
        Write-Success "Remote repository URL updated"
    } else {
        Write-Success "Remote repository already configured correctly"
    }
}
catch {
    Write-Info "Adding remote repository..."
    & git remote add origin $REPO_URL
    Write-Success "Remote repository added"
}

Write-Info "Remote repository:"
& git remote -v

$CurrentBranch = & git branch --show-current
Write-ColorOutput ""
Write-Info "Current branch: $CurrentBranch"

Write-ColorOutput ""
Write-Info "Pushing to GitHub..."
Write-Warning "If this is the first push, you may need to enter GitHub credentials"
Write-Host "   Username: jason660519" -ForegroundColor Yellow
Write-Host "   Password: Use Personal Access Token (not password)" -ForegroundColor Yellow

if (-not $WhatIf) {
    try {
        $RemoteBranches = & git ls-remote --heads origin $CurrentBranch 2>$null
        
        if ($RemoteBranches) {
            Write-Info "Pushing to existing branch..."
            & git push origin $CurrentBranch
        } else {
            Write-Info "First push of branch $CurrentBranch..."
            & git push -u origin $CurrentBranch
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Successfully pushed to GitHub!"
            
            # Step 3: Show setup suggestions
            Write-ColorOutput ""
            Write-Info "Step 3/3: GitHub Repository Setup Suggestions"
            Write-ColorOutput ("=" * 30) "Gray"
            
            Write-ColorOutput ""
            Write-ColorOutput "Repository Link:" "Yellow"
            Write-Host "   https://github.com/jason660519/Proxy-Crawler-System" -ForegroundColor Cyan
            
            Write-ColorOutput ""
            Write-ColorOutput "Suggested GitHub Settings:" "Yellow"
            Write-ColorOutput ""
            Write-Host "1. Repository Description (About):" -ForegroundColor White
            Write-Host "   Proxy Crawler and Management System - Observable, modular, scalable proxy pool management platform" -ForegroundColor Gray
            Write-ColorOutput ""
            Write-Host "2. Suggested Topics:" -ForegroundColor White
            Write-Host "   proxy-crawler, proxy-pool, web-scraping, fastapi, python," -ForegroundColor Gray
            Write-Host "   monitoring, docker, async, data-pipeline, html-to-markdown" -ForegroundColor Gray
            Write-ColorOutput ""
            Write-Host "3. Secrets Setup (for CI/CD):" -ForegroundColor White
            Write-Host "   Settings > Secrets and variables > Actions" -ForegroundColor Gray
            Write-Host "   - DOCKER_USERNAME: Docker Hub username" -ForegroundColor Gray
            Write-Host "   - DOCKER_PASSWORD: Docker Hub password or token" -ForegroundColor Gray
            
            Write-ColorOutput ""
            Write-ColorOutput "Immediate Checklist:" "Yellow"
            Write-Host "[] Visit GitHub repository to check file structure" -ForegroundColor White
            Write-Host "[] Confirm README.md displays correctly on GitHub" -ForegroundColor White
            Write-Host "[] Check if GitHub Actions are running properly" -ForegroundColor White
            Write-Host "[] Set repository description and topics" -ForegroundColor White
            Write-Host "[] Configure CI/CD secrets (if needed)" -ForegroundColor White
            
            Write-ColorOutput ""
            Write-ColorOutput "Quick Test Deployment:" "Yellow"
            Write-Host "   git clone https://github.com/jason660519/Proxy-Crawler-System.git" -ForegroundColor Cyan
            Write-Host "   cd Proxy-Crawler-System" -ForegroundColor Cyan
            Write-Host "   uv sync && uv run python src/main.py" -ForegroundColor Cyan
            
            Write-ColorOutput ""
            Write-Success "Complete push process executed successfully!"
        }
        else {
            throw "Git push failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        Write-Error "Push failed!"
        Write-ColorOutput ""
        Write-ColorOutput "Common Solutions:" "Yellow"
        Write-ColorOutput ""
        Write-Host "1. Authentication Issue - Set up Personal Access Token:" -ForegroundColor White
        Write-Host "   a. Visit: https://github.com/settings/tokens" -ForegroundColor Gray
        Write-Host "   b. Generate new token (classic)" -ForegroundColor Gray
        Write-Host "   c. Select 'repo' permission" -ForegroundColor Gray
        Write-Host "   d. Copy token" -ForegroundColor Gray
        Write-Host "   e. Re-run push, username: jason660519, password: paste token" -ForegroundColor Gray
        Write-ColorOutput ""
        Write-Host "2. Or use credential helper:" -ForegroundColor White
        Write-Host "   git config --global credential.helper manager" -ForegroundColor Cyan
        Write-ColorOutput ""
        Write-Host "3. Or use SSH Key (if configured):" -ForegroundColor White
        Write-Host "   git remote set-url origin git@github.com:jason660519/Proxy-Crawler-System.git" -ForegroundColor Cyan
        
        exit 1
    }
} else {
    Write-Warning "This is a simulation - no actual push to GitHub"
}
