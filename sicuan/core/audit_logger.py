"""
Audit Logger — Catat semua keputusan dan aksi agent
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class AuditLogger:
    """Audit Logger — Track semua keputusan agent"""

    def __init__(self):
        self.audit_file = Path("/home/dibs/agentjw/memory/audit.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.audit_file.exists():
            try:
                return json.loads(self.audit_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "entries": [],
            "total": 0,
            "last_updated": None
        }

    def _save(self):
        self._data["last_updated"] = datetime.now().isoformat()
        self.audit_file.write_text(json.dumps(self._data, indent=2))

    def log(self, action: str, agent: str, context: str, result: str, data: Dict = None):
        entry = {
            "id": f"AUD-{self._data['total']+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "agent": agent,
            "context": context,
            "result": result,
            "data": data or {}
        }
        self._data["entries"].append(entry)
        self._data["total"] += 1
        if len(self._data["entries"]) > 1000:
            self._data["entries"] = self._data["entries"][-500:]
        self._save()
        return entry

    def get_recent(self, limit: int = 10) -> str:
        entries = self._data["entries"][-limit:]
        if not entries:
            return "Belum ada audit log"
        
        lines = []
        lines.append("📋 **AUDIT LOG**")
        lines.append("=" * 40)
        for e in entries:
            lines.append(f"🕐 {e['timestamp'][:16]}")
            lines.append(f"  Agent: {e['agent']}")
            lines.append(f"  Action: {e['action']}")
            lines.append(f"  Result: {e['result']}")
            lines.append("")
        return "\n".join(lines)

    def get_summary(self) -> Dict:
        return {
            "total": self._data["total"],
            "last_updated": self._data["last_updated"]
        }


_audit = None


def get_audit_logger() -> AuditLogger:
    global _audit
    if _audit is None:
        _audit = AuditLogger()
    return _audit
