#!/bin/bash
echo "=========================================="
echo "AGENTJW HEALTH CHECK"
echo "=========================================="

cd ~/agentjw

# Check processes
echo "📊 PROCESS STATUS:"
ps aux | grep -E "agentjw|sicuan|monitor" | grep -v grep

# Check logs - dengan fallback
echo ""
echo "📋 RECENT LOGS:"
if [ -f logs/agentjw.log ]; then
    tail -20 logs/agentjw.log
else
    echo "⚠️  logs/agentjw.log not found"
    echo "📁 Checking other log files:"
    ls -la logs/ 2>/dev/null | head -10 || echo "No log directory"
fi

# Check burn-in monitor
echo ""
echo "📊 BURN-IN MONITOR STATUS:"
if pgrep -f "monitor.py" > /dev/null; then
    echo "✅ Monitor running"
    ps aux | grep monitor.py | grep -v grep
else
    echo "❌ Monitor not running"
fi

# Check metrics
echo ""
echo "📈 PRODUCTION METRICS:"
python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/dibs/agentjw')
try:
    from sicuan.core.production_metrics import get_production_metrics
    from sicuan.core.ceo_agent import get_ceo_agent
    
    metrics = get_production_metrics()
    ceo = get_ceo_agent()
    
    data = metrics._data
    print(f"Health Score: {ceo.get_health_score()}/100")
    print(f"Automation Rate: {ceo.get_automation_rate()}%")
    print(f"Workflow Rate: {data['workflow']['success_rate']:.1f}%")
    print(f"MTBF: {data['recovery']['mtbf']:.1f}s")
    print(f"MTTR: {data['recovery']['mttr']:.1f}s")
    print(f"Total Workflows: {data['workflow']['total']}")
    print(f"Total LLM Calls: {data['llm']['total_calls']}")
except Exception as e:
    print(f"Error: {e}")
PYEOF

echo ""
echo "=========================================="
echo "✅ HEALTH CHECK COMPLETE"
echo "=========================================="
