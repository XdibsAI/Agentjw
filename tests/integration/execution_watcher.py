#!/usr/bin/env python3
"""
Execution Watcher - Memantau eksekusi tanpa mengubah brain.py
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sicuan.brain import SiCuanBrain


class ExecutionWatcher:
    """Memantau eksekusi dan memverifikasi konsistensi"""
    
    def __init__(self):
        self.brain = SiCuanBrain()
        self.results = []
    
    def watch(self, user_message: str) -> Dict:
        """Jalankan dan pantau eksekusi"""
        
        # 1. Snapshot sebelum
        before_files = self._get_file_snapshot()
        
        # 2. Jalankan AI
        result = self.brain.think_and_respond(user_message, [])
        plan = result.get("plan", [])
        self._last_plan = plan  # Simpan untuk fallback
        response = result.get("response", "")
        
        # 3. Snapshot sesudah
        after_files = self._get_file_snapshot()
        
        # 4. Analisis perubahan
        changes = self._diff_snapshots(before_files, after_files)
        
        # 5. Verifikasi konsistensi
        planned_actions = [step.get("action") for step in plan]
        executed_actions = self._extract_executed_actions(response)
        
        return {
            "user_message": user_message,
            "plan": plan,
            "response": response[:200],
            "planned_actions": planned_actions,
            "executed_actions": executed_actions,
            "files_changed": changes,
            "consistent": self._verify_consistency(planned_actions, executed_actions, changes)
        }
    
    def _get_file_snapshot(self) -> Dict[str, str]:
        """Ambil snapshot filesystem"""
        snapshot = {}
        # Scan semua project
        projects_dir = Path("/home/dibs/agentjw/projects")
        if projects_dir.exists():
            for project in projects_dir.iterdir():
                if project.is_dir():
                    for f in project.glob("*.py"):
                        try:
                            snapshot[str(f)] = f.read_text()
                        except:
                            pass
        # Juga scan sicuan actions
        actions_dir = Path("/home/dibs/agentjw/sicuan/actions")
        if actions_dir.exists():
            for f in actions_dir.glob("*.py"):
                try:
                    snapshot[str(f)] = f.read_text()
                except:
                    pass
        return snapshot
    
    def _diff_snapshots(self, before: Dict, after: Dict) -> List[str]:
        """Bandingkan snapshot"""
        changed = []
        all_files = set(before.keys()) | set(after.keys())
        for f in all_files:
            if before.get(f) != after.get(f):
                changed.append(f)
        return changed
    
    def _extract_executed_actions(self, response: str) -> List[str]:
        """Ekstrak action dari response - fallback ke plan jika tidak terdeteksi"""
        actions = []
        # Cek berdasarkan kata kunci yang lebih spesifik
        if "modify" in response.lower() or "perubahan" in response.lower() or "edit" in response.lower():
            actions.append("modify_logic")
        if "repair" in response.lower() or "perbaiki" in response.lower():
            actions.append("repair_project")
        if "scan" in response.lower():
            actions.append("scan_project")
        if "analyze" in response.lower() or "analisa" in response.lower():
            actions.append("analyze_project")
        if "trace" in response.lower():
            actions.append("trace_code")
        if "build" in response.lower() or "bangun" in response.lower():
            actions.append("build_project")
        if "run" in response.lower() or "jalankan" in response.lower():
            actions.append("run_bot")
        
        # Jika tidak ada action terdeteksi dari response, gunakan plan sebagai fallback
        if not actions:
            # Ambil dari plan yang disimpan di watch()
            if hasattr(self, '_last_plan'):
                for step in self._last_plan:
                    action = step.get("action")
                    if action and action not in actions:
                        actions.append(action)
        return actions
    
    def _verify_consistency(self, planned: List[str], executed: List[str], changes: List[str]) -> bool:
        """Verifikasi konsistensi"""
        # Jika planned mengandung modify_logic, harus ada perubahan file
        if "modify_logic" in planned:
            if not changes:
                return False
        # Jika planned tidak mengandung modify_logic, tidak boleh ada perubahan file
        else:
            if changes:
                return False
        return True


def test_execution_integrity():
    """Test execution integrity"""
    watcher = ExecutionWatcher()
    
    print("=" * 60)
    print("🧪 EXECUTION INTEGRITY TEST")
    print("=" * 60)
    
    tests = [
        ("jangan ubah kode, analisa performa godmeme_bot", False),
        ("buat fitur baru di godmeme_bot", True),
    ]
    
    for user_message, should_change in tests:
        print(f"\n📌 User: {user_message[:50]}...")
        result = watcher.watch(user_message)
        
        if result["consistent"]:
            print(f"  ✅ PASS: Konsisten")
        else:
            print(f"  ❌ FAIL: Tidak konsisten")
            print(f"     Planned: {result['planned_actions']}")
            print(f"     Executed: {result['executed_actions']}")
            print(f"     Files changed: {result['files_changed']}")


if __name__ == "__main__":
    test_execution_integrity()
