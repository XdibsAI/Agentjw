#!/bin/bash
cd /home/dibs/agentjw
source venv/bin/activate

echo "[$(date)] Starting SiCuan services..."

# Kill semua
pkill -9 -f "telegram_bot" 2>/dev/null
pkill -9 -f "run_bot" 2>/dev/null  
pkill -9 -f "uvicorn" 2>/dev/null
sleep 3

# Verify bersih
REMAINING=$(ps aux | grep -E "telegram|uvicorn" | grep -v grep | wc -l)
echo "Remaining processes: $REMAINING"

# API Server
nohup uvicorn api_server:app --host 0.0.0.0 --port 18790 \
    > logs/api_server.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"

sleep 2

# Telegram Bot
nohup python3 << 'PYEOF' > logs/sicuan_telegram.log 2>&1 &
import sys
sys.path.insert(0, '/home/dibs/agentjw')
from sicuan.telegram_bot import run_bot
run_bot()
PYEOF
TG_PID=$!
echo "Telegram Bot PID: $TG_PID"

# Simpan PID
echo "$API_PID" > logs/api_server.pid
echo "$TG_PID" > logs/telegram_bot.pid

sleep 5
echo ""
echo "=== STATUS ==="
curl -s http://localhost:18790/health | python3 -m json.tool 2>/dev/null || echo "API not ready yet"
echo ""
tail -5 logs/sicuan_telegram.log

# Tunggu bot benar-benar ready sebelum return
sleep 5
if ps -p $(cat logs/telegram_bot.pid 2>/dev/null) > /dev/null 2>&1; then
    echo "✓ All services confirmed running"
else
    echo "⚠️ Bot may have failed, check logs/sicuan_telegram.log"
fi
