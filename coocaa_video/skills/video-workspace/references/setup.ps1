param(
  [switch]$InstallDependencies
)

$ErrorActionPreference = "Stop"

$workspace = Get-Location
Write-Host "Video workspace: $workspace"

function Test-Command {
  param([Parameter(Mandatory = $true)][string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

$required = @("node", "npm", "ffmpeg")
$missing = @()
foreach ($cmd in $required) {
  if (-not (Test-Command $cmd)) {
    $missing += $cmd
  }
}

if ($missing.Count -gt 0) {
  Write-Host "Missing commands: $($missing -join ', ')"
  if ($InstallDependencies) {
    Write-Host "Dependency installation is not run automatically by default."
    Write-Host "Install the missing tools, then run doctor.ps1 again."
  }
} else {
  Write-Host "Required commands are available."
}

$dirs = @("assets", "projects", "outputs", ".codex-tmp")
foreach ($dir in $dirs) {
  $path = Join-Path $workspace $dir
  if (-not (Test-Path -LiteralPath $path)) {
    New-Item -ItemType Directory -Path $path | Out-Null
    Write-Host "Created $dir/"
  }
}

if (-not (Test-Path -LiteralPath (Join-Path $workspace ".env.local")) -and
    (Test-Path -LiteralPath (Join-Path $workspace ".env.example"))) {
  Copy-Item -LiteralPath (Join-Path $workspace ".env.example") -Destination (Join-Path $workspace ".env.local")
  Write-Host "Created .env.local from .env.example. Fill in your own API keys."
}

Write-Host "Setup complete. Run .\doctor.ps1 for a full environment report."
