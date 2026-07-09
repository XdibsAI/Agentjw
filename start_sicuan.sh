#!/bin/bash
cd /home/dibs/agentjw
source venv/bin/activate

echo "[$(date)] Starting SiCuan services..."

pkill -9 -f "run_bot" 2>/dev/null
pkill -9 -f "uvicorn" 2>/dev/null
pkill -9 -f "run_scheduler" 2>/dev/null
sleep 3

REMAINING=$(ps aux | grep -E "telegram|uvicorn|scheduler" | grep -v grep | wc -l)
echo "Remaining processes: $REMAINING"

# API Server
nohup uvicorn api_server:app --host 0.0.0.0 --port 18790 \
    > logs/api_server.log 2>&1 &
API_PID=$!
echo "API Server PID: $API_PID"
sleep 2

# Telegram Bot
nohup python3 -c "
import sys
sys.path.insert(0, '/home/dibs/agentjw')
run_bot()
" > logs/sicuan_telegram.log 2>&1 &
TG_PID=$!
echo "Telegram Bot PID: $TG_PID"
sleep 2

# Scheduler (morning briefing + nightly consolidation)
nohup python3 -c "
import sys
sys.path.insert(0, '/home/dibs/agentjw')
from sicuan.scheduler import run_scheduler
run_scheduler()
" > logs/sicuan_scheduler.log 2>&1 &
SCHED_PID=$!
echo "Scheduler PID: $SCHED_PID"

echo "$API_PID" > logs/api_server.pid
echo "$SCHED_PID" > logs/scheduler.pid

sleep 5
echo ""
echo "=== STATUS ==="
curl -s http://localhost:18790/health | python3 -m json.tool 2>/dev/null || echo "API not ready yet"
echo ""
tail -3 logs/sicuan_telegram.log
echo ""
tail -3 logs/sicuan_scheduler.log

sleep 3
ALL_OK=true
    PID=$(cat $pidfile 2>/dev/null)
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "⚠️ Process from $pidfile is dead"
        ALL_OK=false
    fi
done
if $ALL_OK; then
    echo "✓ All 3 services confirmed running (API + Telegram + Scheduler)"
fi
export PYTHONPATH=/home/dibs/agentjw:/home/dibs/agentjw/core:/home/dibs/agentjw/sicuan:$PYTHONPATH
