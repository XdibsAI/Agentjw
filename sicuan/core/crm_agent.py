"""
CRM Agent — Mengelola data pelanggan
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class CRMAgent:
    """CRM Agent — Kelola data pelanggan"""

    def __init__(self):
        self.crm_dir = Path("/home/dibs/agentjw/memory/crm")
        self.crm_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.crm_dir / "index.json"
        self._index = self._load_index()

    def _load_index(self) -> Dict:
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except:
                return {"customers": {}, "segments": {}}
        return {"customers": {}, "segments": {}}

    def _save_index(self):
        self.index_file.write_text(json.dumps(self._index, indent=2))

    def register_customer(self, customer_id: str, name: str = "", email: str = "", phone: str = "") -> Dict:
        """Daftarkan pelanggan baru"""
        if customer_id not in self._index["customers"]:
            self._index["customers"][customer_id] = {
                "id": customer_id,
                "name": name,
                "email": email,
                "phone": phone,
                "segment": "new",
                "first_seen": datetime.now().isoformat(),
                "last_seen": "",
                "total_spent": 0,
                "total_orders": 0,
                "preferences": {},
                "tags": [],
                "notes": []
            }
            self._save_index()
        return self._index["customers"][customer_id]

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        return self._index["customers"].get(customer_id)

    def update_customer(self, customer_id: str, data: Dict) -> Dict:
        if customer_id in self._index["customers"]:
            customer = self._index["customers"][customer_id]
            customer.update(data)
            customer["last_seen"] = datetime.now().isoformat()
            self._save_index()
            return customer
        return {}

    def add_purchase(self, customer_id: str, product: str, amount: float, order_id: str = "") -> Dict:
        customer = self.get_customer(customer_id)
        if customer:
            customer["total_spent"] += amount
            customer["total_orders"] += 1
            if customer["total_orders"] > 1:
                customer["segment"] = "loyal"
            elif customer["total_spent"] > 1000000:
                customer["segment"] = "vip"
            self._save_index()
            return {"success": True, "new_total": customer["total_spent"]}
        return {"success": False, "error": "Customer not found"}

    def get_customer_summary(self, customer_id: str) -> str:
        customer = self.get_customer(customer_id)
        if not customer:
            return "❌ Pelanggan tidak ditemukan"
        
        lines = []
        lines.append(f"👤 **{customer.get('name', 'Unknown')}**")
        lines.append(f"📧 {customer.get('email', 'No email')}")
        lines.append(f"📱 {customer.get('phone', 'No phone')}")
        lines.append(f"📊 Segment: {customer.get('segment', 'new')}")
        lines.append(f"💰 Total Belanja: Rp {customer.get('total_spent', 0):,}")
        lines.append(f"📦 Total Order: {customer.get('total_orders', 0)}")
        lines.append(f"🕐 Terakhir: {customer.get('last_seen', 'N/A')[:16]}")
        return "\n".join(lines)

    def search_customers(self, query: str) -> List[Dict]:
        results = []
        query_lower = query.lower()
        for cid, customer in self._index["customers"].items():
            name = customer.get("name", "").lower()
            email = customer.get("email", "").lower()
            if query_lower in name or query_lower in email:
                results.append(customer)
        return results


_crm = None


def get_crm_agent() -> CRMAgent:
    global _crm
    if _crm is None:
        _crm = CRMAgent()
    return _crm
