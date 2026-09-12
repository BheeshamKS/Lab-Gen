#!/usr/bin/env bash
# Run LabGenius Web Dashboard
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
    UVICORN="$SCRIPT_DIR/.venv/bin/uvicorn"
else
    PYTHON="python3"
    UVICORN="uvicorn"
fi

echo "=========================================================="
echo " Starting LabGenius Web Application Dashboard..."
echo " Open in your browser: http://127.0.0.1:8000"
echo "=========================================================="

"$UVICORN" web_app:app --host 127.0.0.1 --port 8000 --reload
