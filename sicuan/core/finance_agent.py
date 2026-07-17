"""
Finance Agent — Pembayaran, invoice, tagihan, pemasukan
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class FinanceAgent:
    """Finance Agent — Kelola keuangan"""

    def __init__(self):
        self.invoices = []
        self.payments = []
        self.transactions = []
        self.invoice_counter = 0
        self._balance = 0

    def create_invoice(self, customer_id: str, amount: float, description: str, 
                       due_date: str = None) -> Dict:
        """Buat invoice baru"""
        self.invoice_counter += 1
        invoice = {
            "id": f"INV-{self.invoice_counter:04d}",
            "customer_id": customer_id,
            "amount": amount,
            "description": description,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "due_date": due_date or (datetime.now() + timedelta(days=14)).isoformat(),
            "paid_at": None
        }
        self.invoices.append(invoice)
        return invoice

    def record_payment(self, invoice_id: str, amount: float, method: str = "transfer") -> Dict:
        """Catat pembayaran"""
        invoice = self.get_invoice(invoice_id)
        if not invoice:
            return {"error": "Invoice not found"}
        
        payment = {
            "id": f"PAY-{len(self.payments)+1:04d}",
            "invoice_id": invoice_id,
            "amount": amount,
            "method": method,
            "status": "completed",
            "created_at": datetime.now().isoformat()
        }
        self.payments.append(payment)
        
        # Update invoice
        invoice["status"] = "paid"
        invoice["paid_at"] = datetime.now().isoformat()
        self._balance += amount
        
        return payment

    def get_invoice(self, invoice_id: str) -> Optional[Dict]:
        for inv in self.invoices:
            if inv["id"] == invoice_id:
                return inv
        return None

    def get_invoices_by_customer(self, customer_id: str) -> List[Dict]:
        return [inv for inv in self.invoices if inv["customer_id"] == customer_id]

    def get_pending_invoices(self) -> List[Dict]:
        return [inv for inv in self.invoices if inv["status"] == "pending"]

    def get_balance(self) -> Dict:
        return {
            "balance": self._balance,
            "pending_invoices": len(self.get_pending_invoices()),
            "total_invoices": len(self.invoices),
            "total_payments": len(self.payments)
        }

    def format_invoice(self, invoice: Dict) -> str:
        lines = []
        lines.append(f"🧾 **{invoice['id']}**")
        lines.append(f"👤 Customer: {invoice['customer_id']}")
        lines.append(f"💰 Amount: Rp {invoice['amount']:,}")
        lines.append(f"📝 {invoice['description']}")
        lines.append(f"📊 Status: {invoice['status']}")
        lines.append(f"📅 Due: {invoice['due_date'][:16]}")
        if invoice.get("paid_at"):
            lines.append(f"✅ Paid: {invoice['paid_at'][:16]}")
        return "\n".join(lines)


_finance = None


def get_finance_agent() -> FinanceAgent:
    global _finance
    if _finance is None:
        _finance = FinanceAgent()
    return _finance
