"""
Hypothesis Engine - Generate dugaan penyebab berdasarkan data
"""

from typing import List, Dict, Any


class HypothesisEngine:
    """Generate hypothesis berdasarkan data trading"""

    def __init__(self, analytics_data: Dict):
        self.data = analytics_data

    def generate(self) -> List[Dict]:
        """Generate hypothesis berdasarkan data"""
        hypotheses = []
        
        summary = self.data.get("summary", {})
        loss_dist = self.data.get("loss_distribution", {})
        score_perf = self.data.get("by_score", {})
        
        total = summary.get("total", 0)
        wins = summary.get("wins", 0)
        losses = summary.get("losses", 0)
        winrate = (wins / total * 100) if total > 0 else 0
        
        # H1: Entry terlalu lambat / terlalu agresif
        if winrate < 50:
            hypotheses.append({
                "id": "H1",
                "title": "Entry terlalu lambat atau terlalu agresif",
                "evidence": f"Win rate {winrate:.1f}% di bawah 50%",
                "confidence": 0.7,
                "suggested_action": "Turunkan score threshold atau periksa filter momentum"
            })
        
        # H2: Slippage/fee makan profit
        tiny_losses = loss_dist.get("tiny", {}).get("count", 0)
        if tiny_losses > 0:
            hypotheses.append({
                "id": "H2",
                "title": "Slippage/fee terlalu besar",
                "evidence": f"{tiny_losses} loss kecil (-0.003 SOL)",
                "confidence": 0.6,
                "suggested_action": "Cek slippage tolerance dan fee structure"
            })
        
        # H3: Score threshold terlalu tinggi
        if score_perf:
            scores = list(score_perf.keys())
            if scores:
                best_score = max(score_perf.items(), key=lambda x: x[1].get("win_rate", 0))
                worst_score = min(score_perf.items(), key=lambda x: x[1].get("win_rate", 0))
                
                if worst_score[0] < 10:
                    hypotheses.append({
                        "id": "H3",
                        "title": "Score threshold terlalu tinggi",
                        "evidence": f"Score {worst_score[0]} win rate {worst_score[1].get('win_rate', 0):.1f}%",
                        "confidence": 0.8,
                        "suggested_action": f"Turunkan threshold ke {worst_score[0] + 1}"
                    })
        
        # H4: Hold time terlalu pendek/panjang
        # (akan diisi saat ada data hold time)
        
        # H5: Strategy overfit
        if winrate < 30 and len(score_perf) > 3:
            hypotheses.append({
                "id": "H5",
                "title": "Strategy overfit ke kondisi tertentu",
                "evidence": f"Win rate {winrate:.1f}% dengan {len(score_perf)} score variants",
                "confidence": 0.5,
                "suggested_action": "Simplify strategy atau tambah data training"
            })
        
        # Prioritaskan
        hypotheses.sort(key=lambda x: x["confidence"], reverse=True)
        
        return hypotheses

    def print_hypotheses(self, hypotheses: List[Dict] = None):
        """Print hypotheses ke console"""
        if hypotheses is None:
            hypotheses = self.generate()
        
        print("\n" + "=" * 60)
        print("🔍 HYPOTHESES")
        print("=" * 60)
        
        for h in hypotheses:
            confidence_icon = "🟢" if h["confidence"] >= 0.7 else "🟡" if h["confidence"] >= 0.5 else "🔴"
            print(f"\n{confidence_icon} {h['id']}: {h['title']}")
            print(f"   Evidence: {h['evidence']}")
            print(f"   Confidence: {h['confidence']:.0%}")
            print(f"   Action: {h['suggested_action']}")
        
        print("=" * 60)
