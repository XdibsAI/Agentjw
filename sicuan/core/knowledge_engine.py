import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "sicuan" / "knowledge"


class KnowledgeEngine:
    """
    Membaca semua modul knowledge bisnis.
    Tidak mengubah flow lama — hanya menambah konteks.
    """

    MODULES = [
        "core_strategy",
        "curriculum",
        "sop",
        "branding",
        "finance",
        "hr_culture",
        # existing knowledge
        "capabilities",
        "identity",
        "trading",
    ]

    def load(self, module: str) -> dict:
        f = KNOWLEDGE / f"{module}.json"
        if not f.exists():
            return {}
        try:
            return json.loads(f.read_text())
        except Exception:
            return {}

    def load_all(self) -> dict:
        result = {}
        for module in self.MODULES:
            result[module] = self.load(module)
        return result

    def get_focus(self) -> str:
        """Ambil current_focus dari core_strategy."""
        strategy = self.load("core_strategy")
        return strategy.get("current_focus", "")

    def get_budget_alert(self) -> dict | None:
        """Cek apakah ada alert finansial."""
        finance = self.load("finance")
        alerts = finance.get("alerts", {})
        if alerts.get("notify_if_exceeded"):
            return {
                "daily_limit_usd": alerts.get("llm_cost_daily_limit_usd", 5),
                "tracking_file": finance.get("tracking_file", "")
            }
        return None

    def get_active_sop(self, context: str) -> list:
        """Ambil SOP yang relevan berdasarkan konteks."""
        sop = self.load("sop")
        return sop.get(context, [])

    def summary(self) -> dict:
        """Ringkasan singkat untuk dipakai saat chat."""
        strategy = self.load("core_strategy")
        finance = self.load("finance")
        curriculum = self.load("curriculum")

        return {
            "focus": strategy.get("current_focus", "-"),
            "vision": strategy.get("vision", "-"),
            "quarterly_target": strategy.get(
                "quarterly_targets", {}
            ),
            "learning_next": [
                t["topic"]
                for t in curriculum.get("learning_queue", [])
                if t.get("status") == "pending"
            ][:2],
            "monthly_opex_usd": finance.get(
                "monthly_budget", {}
            ).get("total_opex", 0),
        }
