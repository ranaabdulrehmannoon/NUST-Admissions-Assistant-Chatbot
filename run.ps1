$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

$venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Virtual environment not found. Run .\setup.ps1 first."
}

$ollamaUp = $false
try {
    $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
    $ollamaUp = $true
} catch {
    $ollamaUp = $false
}

if (-not $ollamaUp) {
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden | Out-Null
    Start-Sleep -Seconds 3
}

& $venvPython -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
