#!/usr/bin/env python3
"""
E2E Regression — Test end-to-end scenarios
"""

import sys
import time
from typing import Dict, Any

sys.path.insert(0, '/home/dibs/agentjw')

from sicuan.core.capability_router import get_capability_router
from sicuan.core.execution_manager import get_execution_manager
from sicuan.core.observability import get_observability, ExecutionRecord

class E2ERegression:
    """End-to-end regression testing"""
    
    def __init__(self):
        self.router = get_capability_router()
        self.executor = get_execution_manager()
        self.observability = get_observability()
        self.scenarios = [
            self.test_send_message,
            self.test_search,
            self.test_browser,
            self.test_file_operation
        ]
    
    def test_send_message(self) -> Dict:
        """Test send_message capability"""
        print("  📤 Testing send_message...")
        params = {
            "platform": "telegram",
            "target": "@test",
            "message": "E2E Test Message"
        }
        result = self.router.route("send_message", params)
        return {
            "name": "send_message",
            "success": result.get("status") == "success",
            "result": result
        }
    
    def test_search(self) -> Dict:
        """Test search capability"""
        print("  🔍 Testing search...")
        params = {"query": "AgentJW testing"}
        
        # Mock executor for testing
        def mock_executor(params):
            return {"results": ["result1", "result2"]}
        
        result = self.executor.execute(
            tool="search",
            provider="tavily",
            executor=mock_executor,
            params=params,
            timeout=10,
            retries=2
        )
        return {
            "name": "search",
            "success": result.get("status") == "success",
            "result": result
        }
    
    def test_browser(self) -> Dict:
        """Test browser capability"""
        print("  🌐 Testing browser...")
        params = {"url": "https://example.com"}
        result = self.router.route("browser", params)
        return {
            "name": "browser",
            "success": result.get("status") == "success",
            "result": result
        }
    
    def test_file_operation(self) -> Dict:
        """Test file operation"""
        print("  📁 Testing file operation...")
        params = {
            "operation": "read",
            "path": "README.md"
        }
        result = self.router.route("file", params)
        return {
            "name": "file",
            "success": result.get("status") == "success",
            "result": result
        }
    
    def run_all(self) -> Dict:
        """Run all regression scenarios"""
        print("\n" + "=" * 60)
        print("🧪 E2E REGRESSION TEST")
        print("=" * 60)
        
        results = []
        passed = 0
        failed = 0
        
        for test in self.scenarios:
            result = test()
            results.append(result)
            if result["success"]:
                passed += 1
                print(f"    ✅ PASS")
            else:
                failed += 1
                print(f"    ❌ FAIL: {result['result']}")
        
        print("\n" + "=" * 60)
        print("📊 E2E REGRESSION RESULTS")
        print("=" * 60)
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Total: {len(results)}")
        
        return {
            "passed": passed,
            "failed": failed,
            "total": len(results),
            "results": results
        }

if __name__ == "__main__":
    regression = E2ERegression()
    regression.run_all()
