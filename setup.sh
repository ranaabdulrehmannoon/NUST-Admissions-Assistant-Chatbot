#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "[1/6] Detecting Python..."
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "Python is not installed. Install Python 3.10+ and run setup again."
  exit 1
fi

echo "[2/6] Creating virtual environment..."
if [ ! -d ".venv" ]; then
  "$PYTHON_CMD" -m venv .venv
fi

if [ -f ".venv/Scripts/activate" ]; then
  # Git Bash / Windows venv layout
  source .venv/Scripts/activate
else
  source .venv/bin/activate
fi

echo "[3/6] Installing Python dependencies..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo "[4/6] Ensuring Ollama is installed..."
if ! command -v ollama >/dev/null 2>&1; then
  OS_NAME="$(uname -s | tr '[:upper:]' '[:lower:]')"
  if [[ "$OS_NAME" == *"linux"* ]]; then
    curl -fsSL https://ollama.com/install.sh | sh
  elif [[ "$OS_NAME" == *"darwin"* ]]; then
    curl -fsSL https://ollama.com/install.sh | sh
  elif [[ "$OS_NAME" == *"mingw"* ]] || [[ "$OS_NAME" == *"msys"* ]] || [[ "$OS_NAME" == *"cygwin"* ]]; then
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements"
  else
    echo "Unsupported OS for automatic Ollama install. Install Ollama manually: https://ollama.com"
    exit 1
  fi
fi

echo "[5/6] Starting Ollama service if needed..."
if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  if command -v nohup >/dev/null 2>&1; then
    nohup ollama serve >/tmp/ollama.log 2>&1 &
  else
    ollama serve >/dev/null 2>&1 &
  fi
  sleep 4
fi

OLLAMA_MODEL="${OLLAMA_MODEL:-phi3:mini}"
echo "Pulling model: $OLLAMA_MODEL"
ollama pull "$OLLAMA_MODEL"

echo "[6/6] Fetching and indexing NUST FAQs..."
python ingest.py

echo "Setup complete. Start the chatbot with: bash run.sh"
