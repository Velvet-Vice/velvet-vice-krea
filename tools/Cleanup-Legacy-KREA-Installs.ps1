[CmdletBinding()]
param([string]$ComfyUIRoot, [switch]$Yes)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($ComfyUIRoot)) {
    $ComfyUIRoot = @(
        (Join-Path $env:USERPROFILE 'Desktop\ComfyUI_windows_portable\ComfyUI'),
        (Join-Path $env:USERPROFILE 'ComfyUI_windows_portable\ComfyUI'),
        (Join-Path $env:USERPROFILE 'ComfyUI')
    ) | Where-Object { Test-Path (Join-Path $_ 'main.py') -PathType Leaf } | Select-Object -First 1
}
if ([string]::IsNullOrWhiteSpace($ComfyUIRoot)) {
    $ComfyUIRoot = Read-Host 'Full ComfyUI path'
}

$root = [IO.Path]::GetFullPath($ComfyUIRoot.Trim('"'))
if (-not (Test-Path (Join-Path $root 'main.py') -PathType Leaf)) {
    throw "Invalid ComfyUI folder: $root"
}
$customNodes = Join-Path $root 'custom_nodes'

# The canonical Manager/Registry folder is deliberately NOT in this list.
$candidates = @(
    'ComfyUI-Velvet-Vice-KREA',
    'ComfyUI-Velvet-Vice-KREA.disabled',
    'ComfyUI-Velvet-Vice-KREA-main',
    'ComfyUI-Velvet-Vice-KREA-main.disabled',
    'velvet-vice-krea-main',
    'velvet-vice-krea-main.disabled',
    'ComfyUI-ILLUMINATE-AI-KREA',
    'ComfyUI-ILLUMINATE-AI-KREA.disabled'
)

function Test-VelvetViceKreaFolder([string]$Path) {
    if (-not (Test-Path $Path -PathType Container)) { return $false }

    $pyproject = Join-Path $Path 'pyproject.toml'
    if (Test-Path $pyproject -PathType Leaf) {
        $raw = Get-Content -LiteralPath $pyproject -Raw -ErrorAction SilentlyContinue
        if ($raw -match '(?im)^\s*name\s*=\s*["'']velvet-vice-krea["'']') { return $true }
    }

    $init = Join-Path $Path '__init__.py'
    if (Test-Path $init -PathType Leaf) {
        $raw = Get-Content -LiteralPath $init -Raw -ErrorAction SilentlyContinue
        if ($raw -match 'VelvetViceKrea' -or $raw -match 'velvet_vice_krea') { return $true }
    }

    return $false
}

$found = @()
foreach ($name in $candidates) {
    $path = Join-Path $customNodes $name
    if (Test-VelvetViceKreaFolder $path) { $found += $path }
}

if ($found.Count -eq 0) {
    Write-Host 'No legacy Velvet Vice KREA duplicate installation was found.'
    Write-Host 'The canonical Manager/Registry folder velvet-vice-krea was left untouched.'
    exit 0
}

Write-Host 'Detected legacy Velvet Vice KREA installation(s):' -ForegroundColor Cyan
$found | ForEach-Object { Write-Host " - $_" }

if (-not $Yes) {
    if ((Read-Host 'Close ComfyUI. Remove ALL detected legacy KREA copies? Type JA').Trim().ToUpperInvariant() -ne 'JA') {
        throw 'Cancelled.'
    }
}

foreach ($path in $found) {
    Remove-Item -LiteralPath $path -Recurse -Force
    Write-Host "Removed: $path" -ForegroundColor Green
}

Write-Host ''
Write-Host 'Legacy KREA copies removed.' -ForegroundColor Green
Write-Host 'The canonical Manager installation velvet-vice-krea was NOT removed.'
Write-Host 'Restart ComfyUI completely and hard-refresh the browser with Ctrl+F5.'
