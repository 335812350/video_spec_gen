$ErrorActionPreference = "Continue"

function Test-Command {
  param([Parameter(Mandatory = $true)][string]$Name)
  return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

$checks = [ordered]@{
  node = Test-Command "node"
  npm = Test-Command "npm"
  ffmpeg = Test-Command "ffmpeg"
}

Write-Host "Video workspace doctor"
foreach ($name in $checks.Keys) {
  $status = if ($checks[$name]) { "OK" } else { "MISSING" }
  Write-Host ("{0,-10} {1}" -f $name, $status)
}

if ($checks["node"]) {
  node --version
}
if ($checks["npm"]) {
  npm --version
}
if ($checks["ffmpeg"]) {
  ffmpeg -version | Select-Object -First 1
}

Write-Host ""
Write-Host "Directory layout:"
foreach ($dir in @("assets", "projects", "outputs")) {
  $exists = Test-Path -LiteralPath (Join-Path (Get-Location) $dir)
  $status = if ($exists) { "OK" } else { "MISSING" }
  Write-Host ("{0,-10} {1}" -f $dir, $status)
}

Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Put source media under assets/<film-slug>/."
Write-Host "2. Fill required keys in .env.local."
Write-Host "3. Ask Codex to generate or revise video-spec.md."
Write-Host "4. Put task-scoped temporary files in .codex-tmp/<project-slug>/ and clean them up after the task."
