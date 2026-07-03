#!/usr/bin/env python3
"""
Executive Brain Dashboard - Live Status
"""

import json
from pathlib import Path
from datetime import datetime
import os
import time

class ExecutiveDashboard:
    def __init__(self):
        self.memory_dir = Path("memory")
        self.decisions_file = self.memory_dir / "executive_decisions_complete.json"
        self.workflow_file = self.memory_dir / "workflow_history.jsonl"
        
        self.decisions = 0
        self.workflows = 0
        self._load_data()
    
    def _load_data(self):
        """Load data"""
        if self.decisions_file.exists():
            try:
                data = json.loads(self.decisions_file.read_text())
                self.decisions = len(data.get("decisions", []))
            except:
                pass
        
        if self.workflow_file.exists():
            try:
                with open(self.workflow_file) as f:
                    self.workflows = sum(1 for _ in f)
            except:
                pass
    
    def print_dashboard(self):
        """Print live dashboard"""
        os.system('clear')
        
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 10 + "🧠 EXECUTIVE BRAIN DASHBOARD" + " " * 16 + "║")
        print("╠" + "═" * 58 + "╣")
        print(f"║  📊 Total Decisions  : {self.decisions:>6}                         ║")
        print(f"║  📋 Total Workflows  : {self.workflows:>6}                         ║")
        print("╠" + "═" * 58 + "╣")
        print("║  📈 Status:                                                      ║")
        
        # Status berdasarkan workflows
        if self.workflows == 0:
            print("║    ⏳ 0 workflows — belum mulai                              ║")
            progress = 0
        elif self.workflows < 100:
            print(f"║    🌱 {self.workflows}/100 workflows — masih awal              ║")
            progress = 20
        elif self.workflows < 500:
            print(f"║    🌿 {self.workflows}/500 workflows — mulai stabil           ║")
            progress = 40
        elif self.workflows < 2000:
            print(f"║    🌳 {self.workflows}/2000 workflows — mulai belajar         ║")
            progress = 60
        elif self.workflows < 10000:
            print(f"║    🌲 {self.workflows}/10000 workflows — berkembang           ║")
            progress = 80
        else:
            print(f"║    🚀 {self.workflows}+ workflows — mature!                  ║")
            progress = 100
        
        # Progress bar
        bar = "█" * (progress // 2) + "░" * (50 - progress // 2)
        print(f"║    Learning Progress: [{bar}] {progress}%                    ║")
        
        print("╠" + "═" * 58 + "╣")
        print("║  🎯 Next Milestone:                                              ║")
        
        if self.workflows < 100:
            print(f"║    Target: 100 workflows (need {100 - self.workflows} more)    ║")
        elif self.workflows < 500:
            print(f"║    Target: 500 workflows (need {500 - self.workflows} more)    ║")
        elif self.workflows < 2000:
            print(f"║    Target: 2000 workflows (need {2000 - self.workflows} more)   ║")
        elif self.workflows < 10000:
            print(f"║    Target: 10000 workflows (need {10000 - self.workflows} more)  ║")
        else:
            print("║    ✅ All milestones achieved!                               ║")
        
        print("╚" + "═" * 58 + "╝")
        print(f"  Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("")
        print("  Press Ctrl+C to exit")

if __name__ == "__main__":
    dashboard = ExecutiveDashboard()
    try:
        while True:
            dashboard.print_dashboard()
            time.sleep(5)
            dashboard._load_data()
    except KeyboardInterrupt:
        print("\n  👋 Dashboard stopped")
