$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

Write-Host "[1/6] Detecting Python..."
$pythonExe = $null
$pythonArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = 'py'
    $pythonArgs = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = 'python'
    $pythonArgs = @()
} else {
    throw "Python 3.10+ is not installed. Install Python and rerun setup.ps1."
}

Write-Host "[2/6] Creating virtual environment..."
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    & $pythonExe @pythonArgs -m venv .venv
}
$venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment creation failed."
}

Write-Host "[3/6] Installing Python dependencies..."
& $venvPython -m pip install --upgrade pip setuptools wheel
& $venvPython -m pip install -r requirements.txt

Write-Host "[4/6] Ensuring Ollama is installed..."
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
    } else {
        throw "Ollama not found and winget is unavailable. Install Ollama manually from https://ollama.com/download/windows"
    }
}

Write-Host "[5/6] Starting Ollama service if needed..."
$ollamaUp = $false
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
    $ollamaUp = $true
} catch {
    $ollamaUp = $false
}

if (-not $ollamaUp) {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 4
}

$model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "phi3:mini" }
Write-Host "Pulling model: $model"
ollama pull $model

Write-Host "[6/6] Fetching and indexing NUST FAQs..."
& $venvPython ingest.py

Write-Host "Setup complete. Start the chatbot with: .\run.ps1"
