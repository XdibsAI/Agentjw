#!/usr/bin/env python3
"""Enhanced Monitoring Dashboard untuk burn-in test"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/dibs/agentjw')

class BurnInDashboard:
    def __init__(self):
        self.log_dir = Path("logs/burn_in")
        self.metrics_file = self.log_dir / "burn_in_metrics.json"
        
    def get_current_status(self):
        """Get current system status from CEO Agent"""
        try:
            from sicuan.core.production_metrics import get_production_metrics
            from sicuan.core.ceo_agent import get_ceo_agent
            
            metrics = get_production_metrics()
            ceo = get_ceo_agent()
            
            # Get CEO scores
            health_score = ceo.get_health_score()
            automation_rate = ceo.get_automation_rate()
            
            data = metrics._data
            
            # Calculate recovery rate
            total_crashes = data["recovery"]["total_crashes"]
            recovered = data["recovery"]["recovered"]
            recovery_rate = (recovered / max(total_crashes, 1)) * 100
            
            return {
                "health_score": health_score,
                "automation_rate": automation_rate,
                "workflow_success_rate": data["workflow"]["success_rate"],
                "mtbf": data["recovery"]["mtbf"],
                "mttr": data["recovery"]["mttr"],
                "total_workflows": data["workflow"]["total"],
                "total_llm_calls": data["llm"]["total_calls"],
                "total_crashes": total_crashes,
                "recovered": recovered,
                "recovery_rate": recovery_rate,
                "failed_recoveries": data["recovery"]["failed_recoveries"]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_overall_status(self, status):
        """Determine overall status"""
        if "error" in status:
            return "🔴 ERROR"
        
        health = status.get("health_score", 0)
        recovery = status.get("recovery_rate", 0)
        
        if health >= 85 and recovery >= 90:
            return "🟢 STABLE"
        elif health >= 70 and recovery >= 70:
            return "🟡 DEGRADED"
        else:
            return "🔴 UNSTABLE"
    
    def print_dashboard(self):
        """Print enhanced dashboard"""
        status = self.get_current_status()
        
        print("\n" + "="*70)
        print("📊 AGENTJW BURN-IN DASHBOARD")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        if "error" not in status:
            overall = self.get_overall_status(status)
            print(f"\n📈 OVERALL STATUS: {overall}")
            print("-" * 70)
            
            print(f"\n📊 METRICS (from CEO Agent):")
            print(f"  Health Score:        {status['health_score']}/100")
            print(f"  Automation Rate:     {status['automation_rate']}%")
            print(f"  Workflow Success:    {status['workflow_success_rate']:.1f}%")
            print(f"  MTBF:                {status['mtbf']:.1f}s")
            print(f"  MTTR:                {status['mttr']:.1f}s")
            
            print(f"\n🔄 RECOVERY:")
            print(f"  Total Crashes:       {status['total_crashes']}")
            print(f"  Recovered:           {status['recovered']}")
            print(f"  Failed Recoveries:   {status['failed_recoveries']}")
            print(f"  Recovery Rate:       {status['recovery_rate']:.1f}%")
            
            print(f"\n📈 WORKLOADS:")
            print(f"  Total Workflows:     {status['total_workflows']}")
            print(f"  Total LLM Calls:     {status['total_llm_calls']}")
            
            # Critical issues
            critical_issues = 0
            if status['recovery_rate'] < 90:
                critical_issues += 1
            if status['health_score'] < 85:
                critical_issues += 1
            if status['workflow_success_rate'] < 90:
                critical_issues += 1
                
            print(f"\n⚠️  CRITICAL ISSUES: {critical_issues}")
            
            # Targets status
            print("\n🎯 TARGETS:")
            targets = [
                ("Health Score > 90", status['health_score'] > 90),
                ("Automation > 85%", status['automation_rate'] > 85),
                ("MTTR < 5s", status['mttr'] < 5),
                ("Workflow Success > 95%", status['workflow_success_rate'] > 95),
                ("Recovery Rate > 95%", status['recovery_rate'] > 95)
            ]
            
            for target, achieved in targets:
                icon = "✅" if achieved else "⏳"
                print(f"  {icon} {target}")
            
        else:
            print(f"\n❌ Error: {status['error']}")
        
        print("\n" + "="*70)

if __name__ == "__main__":
    dashboard = BurnInDashboard()
    dashboard.print_dashboard()
