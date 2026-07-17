"""
Support Agent — Menjawab pertanyaan teknis, mengikuti SOP troubleshooting
"""
from typing import Dict, List, Optional


class SupportAgent:
    """Support Agent — Kelola tiket dan troubleshooting"""

    def __init__(self):
        self.tickets = []
        self.ticket_counter = 0
        self.sop = {
            "login_issue": [
                "Cek username dan password",
                "Reset password jika lupa",
                "Cek koneksi internet",
                "Coba browser lain",
                "Hubungi support jika masih gagal"
            ],
            "payment_failed": [
                "Cek saldo atau limit kartu",
                "Coba metode pembayaran lain",
                "Cek koneksi internet",
                "Tunggu 5 menit lalu coba lagi",
                "Hubungi bank penerbit"
            ],
            "product_issue": [
                "Cek dokumentasi produk",
                "Restart aplikasi",
                "Update ke versi terbaru",
                "Cek FAQ di website",
                "Buka tiket support"
            ]
        }

    def create_ticket(self, customer_id: str, issue: str, priority: str = "medium") -> Dict:
        self.ticket_counter += 1
        ticket = {
            "id": f"TICKET-{self.ticket_counter:04d}",
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority,
            "status": "open",
            "created_at": self._now(),
            "updated_at": self._now(),
            "history": []
        }
        self.tickets.append(ticket)
        return ticket

    def _now(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat()

    def get_ticket(self, ticket_id: str) -> Optional[Dict]:
        for t in self.tickets:
            if t["id"] == ticket_id:
                return t
        return None

    def get_troubleshooting(self, issue_type: str) -> List[str]:
        return self.sop.get(issue_type, ["Identifikasi masalah", "Cari solusi di dokumentasi", "Hubungi support"])

    def get_tickets_by_customer(self, customer_id: str) -> List[Dict]:
        return [t for t in self.tickets if t["customer_id"] == customer_id]

    def close_ticket(self, ticket_id: str, resolution: str) -> Dict:
        ticket = self.get_ticket(ticket_id)
        if ticket:
            ticket["status"] = "closed"
            ticket["resolution"] = resolution
            ticket["updated_at"] = self._now()
            return ticket
        return {}

    def format_ticket(self, ticket: Dict) -> str:
        lines = []
        lines.append(f"🎫 **{ticket['id']}**")
        lines.append(f"👤 Customer: {ticket['customer_id']}")
        lines.append(f"📝 Issue: {ticket['issue']}")
        lines.append(f"📊 Priority: {ticket['priority']}")
        lines.append(f"📌 Status: {ticket['status']}")
        lines.append(f"🕐 Created: {ticket['created_at'][:16]}")
        if ticket.get("resolution"):
            lines.append(f"✅ Resolution: {ticket['resolution']}")
        return "\n".join(lines)


_support = None


def get_support_agent() -> SupportAgent:
    global _support
    if _support is None:
        _support = SupportAgent()
    return _support
