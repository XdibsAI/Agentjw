#!/usr/bin/env python3
"""Enhanced Monitoring Dashboard - v2"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/dibs/agentjw')

class BurnInDashboard:
    def __init__(self):
        self.metrics_file = Path("memory/production_metrics.json")
        
    def get_metrics(self):
        """Get metrics from file directly for consistency"""
        if self.metrics_file.exists():
            try:
                return json.loads(self.metrics_file.read_text())
            except:
                pass
        return None
    
    def get_ceo_scores(self):
        """Get CEO scores from CEO Agent"""
        try:
            from sicuan.core.ceo_agent import get_ceo_agent
            ceo = get_ceo_agent()
            return {
                "health": ceo.get_health_score(),
                "automation": ceo.get_automation_rate()
            }
        except:
            return {"health": 0, "automation": 0}
    
    def print_dashboard(self):
        """Print dashboard"""
        metrics = self.get_metrics()
        ceo = self.get_ceo_scores()
        
        print("\n" + "="*70)
        print("📊 AGENTJW BURN-IN DASHBOARD")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        if metrics:
            workflow = metrics.get("workflow", {})
            recovery = metrics.get("recovery", {})
            
            total = workflow.get("total", 0)
            success = workflow.get("success", 0)
            success_rate = workflow.get("success_rate", 0)
            
            crashes = recovery.get("total_crashes", 0)
            recovered = recovery.get("recovered", 0)
            recovery_rate = (recovered / max(crashes, 1)) * 100
            
            print(f"\n📈 METRICS:")
            print(f"  Health Score:        {ceo.get('health', 0)}/100")
            print(f"  Automation Rate:     {ceo.get('automation', 0)}%")
            print(f"  Workflow Success:    {success_rate:.1f}%")
            print(f"  Total Workflows:     {total}")
            print(f"  MTTR:                {recovery.get('mttr', 0):.1f}s")
            print(f"  MTBF:                {recovery.get('mtbf', 0):.1f}s")
            
            print(f"\n🔄 RECOVERY:")
            print(f"  Total Crashes:       {crashes}")
            print(f"  Recovered:           {recovered}")
            print(f"  Recovery Rate:       {recovery_rate:.1f}%")
            
            # Critical issues
            critical = 0
            if ceo.get('health', 0) < 85:
                critical += 1
            if success_rate < 90:
                critical += 1
            if recovery_rate < 90:
                critical += 1
                
            print(f"\n⚠️  CRITICAL ISSUES: {critical}")
            
            # Targets
            print("\n🎯 TARGETS:")
            targets = [
                ("Health Score > 90", ceo.get('health', 0) > 90),
                ("Automation > 85%", ceo.get('automation', 0) > 85),
                ("MTTR < 5s", recovery.get('mttr', 10) < 5),
                ("Workflow Success > 95%", success_rate > 95),
                ("Recovery Rate > 95%", recovery_rate > 95)
            ]
            
            for target, achieved in targets:
                icon = "✅" if achieved else "⏳"
                print(f"  {icon} {target}")
                
            # Overall status
            if ceo.get('health', 0) >= 85 and recovery_rate >= 90:
                status = "🟢 STABLE"
            elif ceo.get('health', 0) >= 70 and recovery_rate >= 70:
                status = "🟡 DEGRADED"
            else:
                status = "🔴 UNSTABLE"
            
            print(f"\n📊 OVERALL STATUS: {status}")
            
        else:
            print("\n❌ No metrics data found!")
        
        print("\n" + "="*70)

if __name__ == "__main__":
    dashboard = BurnInDashboard()
    dashboard.print_dashboard()
