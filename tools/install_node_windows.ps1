Param(
    [string]$Version = "22.12.0",
    [string]$Arch = "x64",
    [string]$Dest = "$PSScriptRoot/node"
)

$ErrorActionPreference = "Stop"

Write-Host "Installing Node.js v$Version for Windows $Arch..."

$zipName = "node-v$Version-win-$Arch.zip"
$url = "https://nodejs.org/dist/v$Version/$zipName"
$tmp = New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP "node-download")
$zipPath = Join-Path $tmp $zipName

Invoke-WebRequest -Uri $url -OutFile $zipPath

if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
Expand-Archive -Path $zipPath -DestinationPath $tmp -Force

$src = Join-Path $tmp "node-v$Version-win-$Arch"
Move-Item -Path $src -Destination $Dest

Remove-Item -Recurse -Force $zipPath

Write-Host "Node.js installed to $Dest"
Write-Host "Add to PATH for current session:"
$nodeBin = $Dest
$env:PATH = "$nodeBin;$env:PATH"
Write-Host $env:PATH

Write-Host "Done."


