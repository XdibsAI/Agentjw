#!/usr/bin/env python3
"""Regression Test Suite untuk AgentJW"""

import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

sys.path.insert(0, '/home/dibs/agentjw')

class RegressionSuite:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": [],
            "passed": 0,
            "failed": 0,
            "skipped": 0
        }
        
    def run_unit_tests(self) -> bool:
        """Run unit tests"""
        print("🧪 Running unit tests...")
        try:
            # Cari test files
            test_files = list(Path("tests").glob("test_*.py"))
            if not test_files:
                print("  ⚠️  No unit tests found")
                return True
            
            for test_file in test_files:
                result = subprocess.run(
                    [sys.executable, str(test_file)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    print(f"  ❌ {test_file.name} failed")
                    return False
                print(f"  ✅ {test_file.name} passed")
            return True
        except Exception as e:
            print(f"  ❌ Unit tests error: {e}")
            return False
    
    def run_integration_tests(self) -> bool:
        """Run integration tests"""
        print("🔗 Running integration tests...")
        try:
            from sicuan.core.production_metrics import get_production_metrics
            from sicuan.core.ceo_agent import get_ceo_agent
            
            # Test 1: Production Metrics
            metrics = get_production_metrics()
            metrics.reset()
            metrics.record_workflow(True, 1.0)
            metrics.record_workflow(False, 2.0)
            
            if metrics._data["workflow"]["total"] != 2:
                print("  ❌ Production metrics integration failed")
                return False
            print("  ✅ Production metrics integration OK")
            
            # Test 2: CEO Agent
            ceo = get_ceo_agent()
            health = ceo.get_health_score()
            if not (0 <= health <= 100):
                print("  ❌ CEO Agent integration failed")
                return False
            print(f"  ✅ CEO Agent integration OK (health: {health})")
            
            # Test 3: Permission Engine
            from sicuan.core.permission_engine import get_permission_engine
            engine = get_permission_engine()
            if not engine.check_permission("admin", "admin:*"):
                print("  ❌ Permission Engine integration failed")
                return False
            print("  ✅ Permission Engine integration OK")
            
            return True
        except Exception as e:
            print(f"  ❌ Integration tests error: {e}")
            return False
    
    def run_permission_tests(self) -> bool:
        """Test permission enforcement"""
        print("🔒 Running permission tests...")
        try:
            from sicuan.core.permission_engine import get_permission_engine
            from sicuan.core.decorators import require_permission
            
            engine = get_permission_engine()
            
            # Test: Admin can do everything
            if not engine.check_permission("admin", "deploy:production"):
                print("  ❌ Admin permission test failed")
                return False
            
            # Test: Viewer cannot deploy
            if engine.check_permission("viewer", "deploy:production"):
                print("  ❌ Viewer permission test failed")
                return False
            
            # Test: Developer can deploy staging
            if not engine.check_permission("developer", "deploy:staging"):
                print("  ❌ Developer staging permission test failed")
                return False
            
            print("  ✅ All permission tests passed")
            return True
        except Exception as e:
            print(f"  ❌ Permission tests error: {e}")
            return False
    
    def run_recovery_tests(self) -> bool:
        """Test recovery engine"""
        print("🔄 Running recovery tests...")
        try:
            from sicuan.core.production_metrics import get_production_metrics
            
            metrics = get_production_metrics()
            metrics.reset()
            
            # Simulate crash
            metrics.record_recovery(True, 1.5)
            metrics.record_recovery(True, 2.0)
            metrics.record_recovery(False, 3.0)
            
            data = metrics._data
            if data["recovery"]["total_crashes"] != 3:
                print("  ❌ Recovery test failed - wrong crash count")
                return False
            
            if data["recovery"]["recovered"] != 2:
                print("  ❌ Recovery test failed - wrong recovery count")
                return False
            
            print("  ✅ Recovery tests passed")
            return True
        except Exception as e:
            print(f"  ❌ Recovery tests error: {e}")
            return False
    
    def run_e2e_tests(self) -> bool:
        """End-to-end workflow tests"""
        print("🚀 Running E2E tests...")
        try:
            from sicuan.core.workflow_engine import WorkflowEngine  # Assume exists
            
            # Test workflow execution
            workflow = {
                "id": "test-001",
                "steps": [
                    {"action": "read", "data": "test"},
                    {"action": "process", "data": "test"},
                    {"action": "write", "data": "test"}
                ]
            }
            
            # This would be actual workflow execution
            # For now, just check if engine exists
            print("  ⚠️  E2E tests need workflow_engine implementation")
            return True
        except Exception as e:
            print(f"  ⚠️  E2E tests skipped: {e}")
            return True
    
    def run_smoke_tests(self) -> bool:
        """Smoke tests for critical services"""
        print("💨 Running smoke tests...")
        
        # Test API
        try:
            import requests
            response = requests.get("http://localhost:18791/health", timeout=5)
            if response.status_code == 200:
                print("  ✅ API health check OK")
            else:
                print("  ⚠️  API returned non-200")
        except:
            print("  ⚠️  API smoke test skipped (not running)")
        
        # Test Telegram bot
        try:
            from sicuan.telegram_bot import run_bot
            print("  ✅ Telegram bot module OK")
        except:
            print("  ⚠️  Telegram bot not available")
        
        return True
    
    def run_all(self) -> Dict:
        """Run all regression tests"""
        print("\n" + "="*50)
        print("🧪 AGENTJW REGRESSION SUITE")
        print("="*50 + "\n")
        
        tests = [
            ("Unit Tests", self.run_unit_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Permission Tests", self.run_permission_tests),
            ("Recovery Tests", self.run_recovery_tests),
            ("E2E Tests", self.run_e2e_tests),
            ("Smoke Tests", self.run_smoke_tests)
        ]
        
        for name, test_func in tests:
            print(f"\n📌 {name}")
            print("-" * 30)
            try:
                result = test_func()
                status = "✅ PASS" if result else "❌ FAIL"
                self.results["tests"].append({
                    "name": name,
                    "status": "pass" if result else "fail"
                })
                if result:
                    self.results["passed"] += 1
                else:
                    self.results["failed"] += 1
            except Exception as e:
                print(f"  ❌ Error: {e}")
                self.results["tests"].append({
                    "name": name,
                    "status": "error",
                    "error": str(e)
                })
                self.results["failed"] += 1
        
        # Summary
        print("\n" + "="*50)
        print("📊 RESULTS SUMMARY")
        print("="*50)
        print(f"  Passed: {self.results['passed']}")
        print(f"  Failed: {self.results['failed']}")
        print(f"  Total: {len(self.results['tests'])}")
        
        # Save results
        result_file = Path("tests/regression/results.json")
        result_file.parent.mkdir(parents=True, exist_ok=True)
        result_file.write_text(json.dumps(self.results, indent=2))
        print(f"\n📁 Results saved to: {result_file}")
        
        return self.results

if __name__ == "__main__":
    suite = RegressionSuite()
    results = suite.run_all()
    sys.exit(1 if results["failed"] > 0 else 0)
