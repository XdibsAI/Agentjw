#!/usr/bin/env python3
"""
Regression Suite - Otomatis test semua core action
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Tambahkan path project
sys.path.insert(0, str(Path(__file__).parent.parent))

from sicuan.brain import SiCuanBrain


class RegressionSuite:
    def __init__(self):
        self.brain = SiCuanBrain()
        self.results = []
        
    def run(self):
        tests = [
            ("scan_project", "godmeme_bot", "Scan project"),
            ("analyze_project", "godmeme_bot", "Analyze project"),
            ("trace_code", "_should_buy", "Trace function"),
            ("get_file", "godmeme_bot: config.py", "Get file"),
            ("list_projects", "", "List projects"),
            ("project_summary", "", "Project summary"),
            ("godmeme_status", "", "GodMeme status"),
            ("show_log", "godmeme", "Show log"),
            ("modify_logic", "godmeme_bot: add debug log", "Add debug log"),
            ("run_bot", "godmeme_bot", "Run bot"),
        ]
        
        print("=" * 60)
        print("🧪 REGRESSION SUITE")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        passed = 0
        failed = 0
        results = []
        
        for action, target, request in tests:
            try:
                result = self.brain.execute_action(action, target, request, "regression")
                success = bool(result) and "gagal" not in str(result).lower() and "error" not in str(result).lower()
                
                if success:
                    passed += 1
                    status = "✅"
                else:
                    failed += 1
                    status = "❌"
                
                print(f"{status} {action}: {str(result)[:80] if result else 'None'}")
                results.append({"action": action, "status": "pass" if success else "fail", "result": str(result)[:200]})
                
            except Exception as e:
                failed += 1
                print(f"❌ {action}: Exception - {e}")
                results.append({"action": action, "status": "fail", "error": str(e)})
        
        print("\n" + "=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        total = passed + failed
        if total > 0:
            print(f"📊 Pass Rate: {passed/total*100:.1f}%")
        print("=" * 60)
        
        return results


if __name__ == "__main__":
    suite = RegressionSuite()
    results = suite.run()
    
    # Simpan hasil
    report_file = Path("reports/regression_latest.json")
    report_file.parent.mkdir(exist_ok=True)
    with open(report_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results
        }, f, indent=2)
    
    print(f"\n📄 Report saved to {report_file}")
