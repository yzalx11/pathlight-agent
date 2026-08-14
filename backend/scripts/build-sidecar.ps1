param(
    [string]$TargetTriple = "x86_64-pc-windows-msvc"
)

$ErrorActionPreference = "Stop"
$backendRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent $backendRoot
$python = Join-Path $backendRoot ".venv\Scripts\python.exe"
$outputDir = Join-Path $projectRoot "frontend\src-tauri\binaries"
$workDir = Join-Path $backendRoot ".pyinstaller"

if (-not (Test-Path $python)) {
    throw "Pathlight virtual environment is missing: $python"
}

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
& $python -m PyInstaller `
    --noconfirm `
    --onefile `
    --name "pathlight-api-$TargetTriple" `
    --paths $backendRoot `
    --collect-all rapidocr `
    --collect-binaries onnxruntime.capi `
    --collect-data rapidocr.models `
    --collect-all keyring `
    --collect-all fitz `
    --collect-submodules websockets `
    --distpath $outputDir `
    --workpath (Join-Path $workDir "build") `
    --specpath $workDir `
    (Join-Path $backendRoot "app\desktop.py")
