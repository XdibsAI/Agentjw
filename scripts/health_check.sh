#!/bin/bash
# Health check untuk SiCuan services

check_service() {
    local name=$1
    local pid_file=$2
    local port=$3
    
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "✅ $name running (PID: $pid)"
            return 0
        else
            echo "❌ $name dead (stale PID: $pid)"
            return 1
        fi
    else
        echo "❌ $name not running"
        return 1
    fi
}

# Check API
check_service "API" "/home/dibs/agentjw/logs/api_server.pid" 18790

# Check Telegram Bot
check_service "Telegram Bot" "/home/dibs/agentjw/logs/telegram_bot.pid"

# Check Scheduler
check_service "Scheduler" "/home/dibs/agentjw/logs/scheduler.pid"
