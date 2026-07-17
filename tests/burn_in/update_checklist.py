#!/usr/bin/env python3
"""Auto-update checklist with current metrics"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/dibs/agentjw')

def update_checklist():
    """Update checklist with current status"""
    try:
        from sicuan.core.production_metrics import get_production_metrics
        from sicuan.core.ceo_agent import get_ceo_agent
        
        metrics = get_production_metrics()
        ceo = get_ceo_agent()
        
        data = metrics._data
        
        # Get current metrics
        health = ceo.get_health_score()
        automation = ceo.get_automation_rate()
        workflow_rate = data["workflow"]["success_rate"]
        mttr = data["recovery"]["mttr"]
        total_crashes = data["recovery"]["total_crashes"]
        recovered = data["recovery"]["recovered"]
        
        # Update checklist file
        checklist = Path("tests/burn_in/CHECKLIST.md")
        if checklist.exists():
            content = checklist.read_text()
            
            # Update Day 1 entries
            content = content.replace(
                "- [ ] Burn-in monitor started",
                "- [x] Burn-in monitor started"
            )
            content = content.replace(
                "- [ ] Initial health score: 79/100",
                f"- [x] Initial health score: {health}/100"
            )
            content = content.replace(
                "- [ ] Automation rate: 75%",
                f"- [x] Automation rate: {automation}%"
            )
            content = content.replace(
                "- [ ] MTTR: 3.9s",
                f"- [x] MTTR: {mttr:.1f}s"
            )
            content = content.replace(
                "- [ ] No crashes yet",
                f"- [x] Crashes: {total_crashes}, Recovered: {recovered}"
            )
            
            # Update targets
            content = content.replace(
                "| Health Score | > 90 | 79 | ⏳ |",
                f"| Health Score | > 90 | {health} | {'✅' if health > 90 else '⏳'} |"
            )
            content = content.replace(
                "| Automation | > 85% | 75% | ⏳ |",
                f"| Automation | > 85% | {automation}% | {'✅' if automation > 85 else '⏳'} |"
            )
            content = content.replace(
                "| MTTR | < 5s | 3.9s | ✅ |",
                f"| MTTR | < 5s | {mttr:.1f}s | {'✅' if mttr < 5 else '⏳'} |"
            )
            content = content.replace(
                "| Workflow Success | > 95% | 75% | ⏳ |",
                f"| Workflow Success | > 95% | {workflow_rate:.1f}% | {'✅' if workflow_rate > 95 else '⏳'} |"
            )
            
            checklist.write_text(content)
            print("✅ Checklist updated automatically")
            
    except Exception as e:
        print(f"❌ Error updating checklist: {e}")

if __name__ == "__main__":
    update_checklist()
