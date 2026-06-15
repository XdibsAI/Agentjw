#!/bin/bash
# install_media_deps.sh — Install semua deps untuk media support
# Auto-generated oleh agentjw_flutter_patcher.py
set -e
cd ~/agentjw
source venv/bin/activate 2>/dev/null || true

echo "[1/3] Install Python media deps..."
pip install fal-client aiofiles python-multipart pillow --quiet

echo "[2/3] Install Flutter deps..."
if [ -d "/home/dibs/agentjw_remote" ]; then
    cd "/home/dibs/agentjw_remote"
    flutter pub get
    cd ~/agentjw
fi

echo "[3/3] Restart api_server..."
pkill -f api_server.py 2>/dev/null || true
sleep 1
nohup uvicorn api_server:app --host 0.0.0.0 --port 18790 > logs/api.log 2>&1 &
echo "  ✅ api_server started (port 18790)"
echo ""
echo "Done! Test: curl http://localhost:18790/api/status"
