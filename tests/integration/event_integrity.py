#!/usr/bin/env python3
"""
Event Integrity Test - Memverifikasi konsistensi melalui event bus
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.brain import SiCuanBrain
from sicuan.core.execution_event_bus import ExecutionEventBus


class EventIntegrityTest:
    def __init__(self):
        self.brain = SiCuanBrain()
        self.event_bus = ExecutionEventBus()
        self.results = []

    def test_planner_vs_executor(self):
        """Test: Planner dan executor harus konsisten"""
        print("\n📌 Test: Planner vs Executor")
        print("-" * 40)

        self.event_bus.clear()
        
        user_message = "buat fitur baru di godmeme_bot"
        result = self.brain.think_and_respond(user_message, [])
        
        # Verifikasi konsistensi
        consistency = self.event_bus.verify_consistency()
        
        if consistency["consistent"]:
            print(f"  ✅ PASS: Planner dan executor konsisten")
            print(f"     Planned: {consistency['planned']}")
            print(f"     Executed: {consistency['executed']}")
            return True
        else:
            print(f"  ❌ FAIL: Planner dan executor tidak konsisten")
            print(f"     Planned: {consistency['planned']}")
            print(f"     Executed: {consistency['executed']}")
            print(f"     Missing: {consistency['missing']}")
            print(f"     Extra: {consistency['extra']}")
            return False

    def test_no_code_change(self):
        """Test: User berkata 'jangan ubah kode', tidak boleh ada modify_logic"""
        print("\n📌 Test: No Code Change")
        print("-" * 40)

        self.event_bus.clear()
        
        user_message = "jangan ubah kode, analisa performa godmeme_bot"
        result = self.brain.think_and_respond(user_message, [])
        
        actions = self.event_bus.get_actions()
        has_modify = "modify_logic" in actions
        
        if not has_modify:
            print(f"  ✅ PASS: Tidak ada modify_logic")
            print(f"     Actions: {actions}")
            return True
        else:
            print(f"  ❌ FAIL: Ada modify_logic padahal dilarang")
            print(f"     Actions: {actions}")
            return False

    def run(self):
        print("=" * 60)
        print("🧪 EVENT INTEGRITY TEST")
        print("=" * 60)

        results = [
            self.test_planner_vs_executor(),
            self.test_no_code_change()
        ]

        passed = sum(results)
        failed = len(results) - passed

        print("\n" + "=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        if len(results) > 0:
            print(f"📊 Pass Rate: {passed/len(results)*100:.1f}%")
        print("=" * 60)


if __name__ == "__main__":
    test = EventIntegrityTest()
    test.run()
