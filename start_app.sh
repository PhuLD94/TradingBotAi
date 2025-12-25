#!/bin/bash

echo "=========================================="
echo "   MT5 LABELER - MAC/LINUX SETUP"
echo "=========================================="

# 1. CHECK FOR PYTHON
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 is not installed."
    echo "Please install it via:"
    echo "  - macOS: download from python.org or run 'brew install python'"
    echo "  - Linux: run 'sudo apt install python3 python3-venv'"
    exit 1
fi

echo "[OK] Python 3 found."

# 2. SETUP VIRTUAL ENVIRONMENT
if [ ! -d "venv" ]; then
    echo "[SETUP] Creating virtual environment..."
    python3 -m venv venv
fi

# 3. ACTIVATE AND INSTALL
echo "[SETUP] Activating environment..."
source venv/bin/activate

echo "[SETUP] Installing dependencies..."
pip install --upgrade pip -q
pip install dash pandas plotly -q

# 4. LAUNCH APP
echo ""
echo "=========================================="
echo "   LAUNCHING APP..."
echo "   Open your browser to: http://127.0.0.1:8050"
echo "=========================================="

# Open browser automatically (works on both Mac and Linux)
if which xdg-open > /dev/null; then
  xdg-open http://127.0.0.1:8050/ &
elif which open > /dev/null; then
  open http://127.0.0.1:8050/ &
fi

# Run the Python code
python label.py