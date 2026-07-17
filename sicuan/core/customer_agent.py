"""
Customer Agent — Reception, Sales, Support, CRM
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class CustomerAgent:
    """Agent untuk melayani customer"""

    def __init__(self, customer_id: str):
        self.customer_id = customer_id
        self.customer_dir = Path("/home/dibs/agentjw/memory/customers")
        self.customer_dir.mkdir(parents=True, exist_ok=True)
        self.profile_file = self.customer_dir / f"{customer_id}.json"
        self._profile = self._load()

    def _load(self) -> Dict:
        if self.profile_file.exists():
            try:
                return json.loads(self.profile_file.read_text())
            except:
                return self._default_profile()
        return self._default_profile()

    def _default_profile(self) -> Dict:
        return {
            "customer_id": self.customer_id,
            "first_seen": datetime.now().isoformat(),
            "last_seen": "",
            "name": "",
            "email": "",
            "phone": "",
            "segment": "new",  # new, active, loyal, churned
            "total_spent": 0,
            "last_purchase": "",
            "preferences": {},
            "history": [],
            "tickets": [],
            "notes": []
        }

    def save(self):
        self._profile["last_seen"] = datetime.now().isoformat()
        self.profile_file.write_text(json.dumps(self._profile, indent=2))

    def set_name(self, name: str):
        self._profile["name"] = name
        self.save()

    def add_interaction(self, interaction_type: str, summary: str):
        self._profile["history"].append({
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type,
            "summary": summary
        })
        self.save()

    def get_summary(self) -> str:
        name = self._profile.get("name", "Pelanggan")
        segment = self._profile.get("segment", "new")
        total_spent = self._profile.get("total_spent", 0)
        last_seen = self._profile.get("last_seen", "")
        
        lines = []
        lines.append(f"👤 Pelanggan: {name}")
        lines.append(f"📊 Segment: {segment}")
        lines.append(f"💰 Total Belanja: {total_spent}")
        if last_seen:
            lines.append(f"🕐 Terakhir: {last_seen[:16]}")
        return "\n".join(lines)


_customers = {}


def get_customer_agent(customer_id: str) -> CustomerAgent:
    global _customers
    if customer_id not in _customers:
        _customers[customer_id] = CustomerAgent(customer_id)
    return _customers[customer_id]
