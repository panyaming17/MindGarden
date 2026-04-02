param(
    [Parameter(Mandatory = $false)]
    [string] $Message = ""
)
$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

if (-not $Message) {
    $Message = "chore: sync $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

git add -A
$status = git status --porcelain
if (-not $status) {
    Write-Host "Working tree clean, nothing to commit."
    exit 0
}

git commit -m $Message
git push
