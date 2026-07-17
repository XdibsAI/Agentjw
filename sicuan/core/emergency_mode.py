"""
Emergency Mode — Safemode saat sistem overload atau error tinggi
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class EmergencyMode:
    """Emergency Mode — Safemode saat overload"""

    def __init__(self):
        self.status_file = Path("/home/dibs/agentjw/memory/emergency.json")
        self._data = self._load()

    def _load(self) -> Dict:
        if self.status_file.exists():
            try:
                return json.loads(self.status_file.read_text())
            except:
                return self._default()
        return self._default()

    def _default(self) -> Dict:
        return {
            "mode": "normal",  # normal, safe, emergency
            "activated_at": None,
            "deactivated_at": None,
            "triggers": [],
            "metrics": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "error_rate": 0,
                "response_time": 0
            },
            "history": []
        }

    def _save(self):
        self.status_file.write_text(json.dumps(self._data, indent=2))

    def check_conditions(self, cpu: float = None, memory: float = None, 
                         error_rate: float = None, response_time: float = None) -> str:
        """Cek kondisi dan tentukan mode"""
        if cpu is not None:
            self._data["metrics"]["cpu_usage"] = cpu
        if memory is not None:
            self._data["metrics"]["memory_usage"] = memory
        if error_rate is not None:
            self._data["metrics"]["error_rate"] = error_rate
        if response_time is not None:
            self._data["metrics"]["response_time"] = response_time
        
        # Threshold
        if cpu and cpu > 85:
            self._activate_emergency("CPU overload", {"cpu": cpu})
            return "emergency"
        elif memory and memory > 90:
            self._activate_emergency("Memory overload", {"memory": memory})
            return "emergency"
        elif error_rate and error_rate > 0.3:
            self._activate_emergency("High error rate", {"error_rate": error_rate})
            return "emergency"
        elif response_time and response_time > 10:
            self._activate_emergency("Slow response", {"response_time": response_time})
            return "emergency"
        elif cpu and cpu > 70:
            self._activate_safe("High CPU load", {"cpu": cpu})
            return "safe"
        elif memory and memory > 75:
            self._activate_safe("High memory usage", {"memory": memory})
            return "safe"
        
        # Kembali normal jika sudah aman
        if self._data["mode"] != "normal":
            self._deactivate()
        
        return self._data["mode"]

    def _activate_emergency(self, reason: str, data: Dict):
        if self._data["mode"] != "emergency":
            self._data["mode"] = "emergency"
            self._data["activated_at"] = datetime.now().isoformat()
            self._data["triggers"].append({
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "data": data,
                "type": "emergency"
            })
            self._save()
            print(f"🚨 EMERGENCY MODE ACTIVATED: {reason}")

    def _activate_safe(self, reason: str, data: Dict):
        if self._data["mode"] == "normal":
            self._data["mode"] = "safe"
            self._data["activated_at"] = datetime.now().isoformat()
            self._data["triggers"].append({
                "timestamp": datetime.now().isoformat(),
                "reason": reason,
                "data": data,
                "type": "safe"
            })
            self._save()
            print(f"🟡 SAFE MODE ACTIVATED: {reason}")

    def _deactivate(self):
        if self._data["mode"] != "normal":
            self._data["mode"] = "normal"
            self._data["deactivated_at"] = datetime.now().isoformat()
            self._data["history"].append({
                "activated": self._data["activated_at"],
                "deactivated": self._data["deactivated_at"],
                "mode": self._data["mode"],
                "triggers": self._data["triggers"][-3:]
            })
            self._save()
            print("🟢 NORMAL MODE RESTORED")

    def get_status(self) -> str:
        lines = []
        mode_icon = "🟢" if self._data["mode"] == "normal" else "🟡" if self._data["mode"] == "safe" else "🔴"
        lines.append(f"{mode_icon} **Mode:** {self._data['mode'].upper()}")
        if self._data["activated_at"]:
            lines.append(f"🕐 Activated: {self._data['activated_at'][:16]}")
        lines.append("")
        lines.append("📊 **Metrics:**")
        for key, value in self._data["metrics"].items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        return "\n".join(lines)


_emergency = None


def get_emergency_mode() -> EmergencyMode:
    global _emergency
    if _emergency is None:
        _emergency = EmergencyMode()
    return _emergency
