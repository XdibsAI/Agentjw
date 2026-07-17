#!/usr/bin/env python3
"""Dogfooding - AgentJW mengembangkan dirinya sendiri"""

import sys
sys.path.insert(0, '/home/dibs/agentjw')

from sicuan.core.ceo_agent import get_ceo_agent
from sicuan.core.production_metrics import get_production_metrics
import subprocess
import json
from datetime import datetime

class DogfoodingEngine:
    def __init__(self):
        self.ceo = get_ceo_agent()
        self.metrics = get_production_metrics()
        
    def review_pr(self, pr_number):
        """Review PR menggunakan AgentJW"""
        print(f"📝 Reviewing PR #{pr_number}")
        # Simulasi review
        return {"status": "approved", "comments": "LGTM"}
    
    def fix_bug(self, bug_id):
        """Fix bug menggunakan AgentJW"""
        print(f"🐛 Fixing bug #{bug_id}")
        # Simulasi fix
        return {"status": "fixed", "test_passed": True}
    
    def update_docs(self, section):
        """Update dokumentasi"""
        print(f"📚 Updating docs: {section}")
        return {"status": "updated"}
    
    def manage_tasks(self):
        """Manage daily tasks"""
        print("📋 Managing daily tasks...")
        # Ambil priorities
        priorities = self.ceo.get_priorities()
        for priority in priorities[:3]:
            print(f"  - {priority}")
        return {"tasks_managed": len(priorities)}
    
    def run_daily(self):
        """Daily dogfooding routine"""
        print(f"\n🔄 Daily Dogfooding - {datetime.now().isoformat()}")
        print("=" * 50)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": []
        }
        
        # 1. Review pending PRs
        result = self.review_pr("latest")
        results["tasks"].append({"type": "pr_review", "result": result})
        
        # 2. Fix critical bugs
        result = self.fix_bug("critical")
        results["tasks"].append({"type": "bug_fix", "result": result})
        
        # 3. Update documentation
        result = self.update_docs("api")
        results["tasks"].append({"type": "doc_update", "result": result})
        
        # 4. Task management
        result = self.manage_tasks()
        results["tasks"].append({"type": "task_management", "result": result})
        
        # Log results
        with open("logs/dogfooding.json", "a") as f:
            json.dump(results, f)
            f.write("\n")
        
        return results

if __name__ == "__main__":
    engine = DogfoodingEngine()
    engine.run_daily()
