"""
Approval Workflow — Multi-step approval sebelum aksi sensitif
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ApprovalWorkflow:
    """Approval Workflow — Approval multi-level untuk aksi sensitif"""

    def __init__(self):
        self.approval_file = Path("/home/dibs/agentjw/memory/approvals.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.approval_file.exists():
            try:
                return json.loads(self.approval_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "pending": [],
            "approved": [],
            "rejected": [],
            "history": []
        }

    def _save(self):
        self.approval_file.write_text(json.dumps(self._data, indent=2))

    def request_approval(self, agent: str, action: str, context: str, details: Dict = None) -> Dict:
        """Minta persetujuan untuk aksi sensitif"""
        approval = {
            "id": f"APR-{len(self._data['pending'])+len(self._data['approved'])+len(self._data['rejected'])+1:04d}",
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "context": context,
            "details": details or {},
            "status": "pending",
            "reviewer": None,
            "reviewed_at": None,
            "comment": None
        }
        self._data["pending"].append(approval)
        self._save()
        return approval

    def approve(self, approval_id: str, reviewer: str, comment: str = "") -> Dict:
        """Setujui permintaan"""
        for i, a in enumerate(self._data["pending"]):
            if a["id"] == approval_id:
                a["status"] = "approved"
                a["reviewer"] = reviewer
                a["reviewed_at"] = datetime.now().isoformat()
                a["comment"] = comment
                self._data["approved"].append(a)
                self._data["pending"].pop(i)
                self._data["history"].append(a)
                self._save()
                return a
        return {"error": "Approval not found"}

    def reject(self, approval_id: str, reviewer: str, reason: str) -> Dict:
        """Tolak permintaan"""
        for i, a in enumerate(self._data["pending"]):
            if a["id"] == approval_id:
                a["status"] = "rejected"
                a["reviewer"] = reviewer
                a["reviewed_at"] = datetime.now().isoformat()
                a["comment"] = reason
                self._data["rejected"].append(a)
                self._data["pending"].pop(i)
                self._data["history"].append(a)
                self._save()
                return a
        return {"error": "Approval not found"}

    def get_pending(self) -> List[Dict]:
        return self._data["pending"]

    def get_history(self, limit: int = 10) -> str:
        entries = self._data["history"][-limit:]
        if not entries:
            return "Belum ada history approval"
        
        lines = []
        lines.append("📋 **APPROVAL HISTORY**")
        lines.append("=" * 40)
        for e in entries:
            status_icon = "✅" if e["status"] == "approved" else "❌" if e["status"] == "rejected" else "⏳"
            lines.append(f"{status_icon} {e['timestamp'][:16]}")
            lines.append(f"  Agent: {e['agent']} → {e['action']}")
            lines.append(f"  Status: {e['status']}")
            if e.get("comment"):
                lines.append(f"  Comment: {e['comment']}")
            lines.append("")
        return "\n".join(lines)


_approval = None


def get_approval_workflow() -> ApprovalWorkflow:
    global _approval
    if _approval is None:
        _approval = ApprovalWorkflow()
    return _approval
