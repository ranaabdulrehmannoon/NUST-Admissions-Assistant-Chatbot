#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
else
  echo "Virtual environment not found. Run bash setup.sh first."
  exit 1
fi

if ! curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  if command -v nohup >/dev/null 2>&1; then
    nohup ollama serve >/tmp/ollama.log 2>&1 &
  else
    ollama serve >/dev/null 2>&1 &
  fi
  sleep 3
fi

streamlit run app.py --server.port 8501 --server.address 0.0.0.0
