"""
Sales Agent — Menjelaskan produk, memberikan rekomendasi, follow-up
"""
from typing import Dict, List, Optional


class SalesAgent:
    """Sales Agent — Kelola penjualan dan rekomendasi"""

    def __init__(self):
        self.products = {
            "paket_a": {
                "name": "Paket A",
                "price": 500000,
                "description": "Paket dasar untuk pemula",
                "features": ["Fitur 1", "Fitur 2", "Fitur 3"]
            },
            "paket_b": {
                "name": "Paket B",
                "price": 1000000,
                "description": "Paket lanjutan untuk bisnis",
                "features": ["Fitur 1", "Fitur 2", "Fitur 3", "Fitur 4", "Fitur 5"]
            },
            "paket_c": {
                "name": "Paket C",
                "price": 2000000,
                "description": "Paket enterprise untuk korporasi",
                "features": ["Semua fitur Paket B", "Dedicated support", "Custom integration"]
            }
        }

    def get_products(self) -> List[Dict]:
        return list(self.products.values())

    def get_product(self, name: str) -> Optional[Dict]:
        for key, product in self.products.items():
            if key == name or product["name"].lower() == name.lower():
                return product
        return None

    def recommend(self, customer_segment: str) -> List[Dict]:
        """Rekomendasi produk berdasarkan segment customer"""
        if customer_segment == "new":
            return [self.products["paket_a"]]
        elif customer_segment == "active":
            return [self.products["paket_a"], self.products["paket_b"]]
        elif customer_segment == "loyal":
            return [self.products["paket_b"], self.products["paket_c"]]
        elif customer_segment == "vip":
            return [self.products["paket_c"]]
        return [self.products["paket_a"]]

    def format_product(self, product: Dict) -> str:
        lines = []
        lines.append(f"📦 **{product['name']}**")
        lines.append(f"💰 Rp {product['price']:,}")
        lines.append(f"📝 {product['description']}")
        lines.append("🔧 **Fitur:**")
        for f in product['features']:
            lines.append(f"  - {f}")
        return "\n".join(lines)


_sales = None


def get_sales_agent() -> SalesAgent:
    global _sales
    if _sales is None:
        _sales = SalesAgent()
    return _sales
