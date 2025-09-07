Param(
  [string]$GrafanaUrl = "http://localhost:3001",
  [string]$User = "admin",
  [string]$Pass = "admin",
  [string]$DashboardPath = "docker/grafana/dashboards/proxy_system_overview.json"
)

$ErrorActionPreference = "Stop"
$body = @{ dashboard = (Get-Content -Raw -Path $DashboardPath | ConvertFrom-Json) ; overwrite = $true } | ConvertTo-Json -Depth 10

Write-Host "Importing dashboard to $GrafanaUrl"
Invoke-RestMethod -Method Post -Uri "$GrafanaUrl/api/dashboards/db" -Credential (New-Object System.Management.Automation.PSCredential($User,(ConvertTo-SecureString $Pass -AsPlainText -Force))) -ContentType 'application/json' -Body $body
Write-Host "Done."


