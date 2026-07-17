"""
Long-Term Memory — Simpan keputusan, solusi, bug, dan pelajaran
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class LongTermMemory:
    """Long-Term Memory — Belajar dari pengalaman"""

    def __init__(self):
        self.memory_file = Path("/home/dibs/agentjw/memory/long_term.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.memory_file.exists():
            try:
                return json.loads(self.memory_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "decisions": [],
            "solutions": [],
            "bugs": [],
            "lessons": [],
            "experiments": [],
            "preferences": {}
        }

    def _save(self):
        self.memory_file.write_text(json.dumps(self._data, indent=2))

    def add_decision(self, context: str, decision: str, reason: str, result: str = ""):
        """Simpan keputusan yang diambil"""
        self._data["decisions"].append({
            "id": f"DEC-{len(self._data['decisions'])+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "decision": decision,
            "reason": reason,
            "result": result
        })
        self._save()

    def add_solution(self, problem: str, solution: str, worked: bool, context: str = ""):
        """Simpan solusi yang berhasil/gagal"""
        if "solutions" not in self._data:
            self._data["solutions"] = []
        self._data["solutions"].append({
            "id": f"SOL-{len(self._data['solutions'])+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "problem": problem,
            "solution": solution,
            "worked": worked,
            "context": context
        })
        self._save()

    def add_bug(self, bug: str, cause: str, fix: str, project: str = ""):
        """Simpan bug dan perbaikannya"""
        if "bugs" not in self._data:
            self._data["bugs"] = []
        self._data["bugs"].append({
            "id": f"BUG-{len(self._data['bugs'])+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "bug": bug,
            "cause": cause,
            "fix": fix,
            "project": project,
            "resolved": True
        })
        self._save()

    def add_lesson(self, lesson: str, category: str = "general"):
        """Simpan pelajaran"""
        if "lessons" not in self._data:
            self._data["lessons"] = []
        self._data["lessons"].append({
            "id": f"LSN-{len(self._data['lessons'])+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "lesson": lesson,
            "category": category
        })
        self._save()

    def find_solution(self, problem: str) -> List[Dict]:
        """Cari solusi untuk masalah serupa"""
        results = []
        problem_lower = problem.lower()
        for sol in self._data["solutions"]:
            if problem_lower in sol["problem"].lower():
                results.append(sol)
        return results

    def find_bug(self, bug: str) -> List[Dict]:
        """Cari bug serupa"""
        results = []
        bug_lower = bug.lower()
        for b in self._data["bugs"]:
            if bug_lower in b["bug"].lower():
                results.append(b)
        return results

    def get_context(self, query: str) -> str:
        """Dapatkan konteks dari memory"""
        lines = []
        
        # Cari solusi
        solutions = self.find_solution(query)
        if solutions:
            lines.append("💡 **Solusi Sebelumnya:**")
            for sol in solutions[:3]:
                status = "✅" if sol["worked"] else "❌"
                lines.append(f"  {status} {sol['solution'][:100]}...")
        
        # Cari bug
        bugs = self.find_bug(query)
        if bugs:
            lines.append("\n🐛 **Bug Sebelumnya:**")
            for bug in bugs[:3]:
                lines.append(f"  - {bug['bug'][:100]} → {bug['fix'][:100]}")
        
        return "\n".join(lines) if lines else ""


_memory = None


def get_long_term_memory() -> LongTermMemory:
    global _memory
    if _memory is None:
        _memory = LongTermMemory()
    return _memory
