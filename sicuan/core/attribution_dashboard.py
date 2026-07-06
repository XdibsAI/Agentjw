"""
Attribution Dashboard - Visualisasi attribution data
"""

from sicuan.core.attribution_learner import get_attribution_learner
from sicuan.core.trade_attribution import TradeAttributionEngine


class AttributionDashboard:
    """Dashboard untuk attribution data"""

    def __init__(self):
        self.learner = get_attribution_learner()
        self.engine = TradeAttributionEngine()

    def show(self):
        """Tampilkan dashboard"""
        print("\n" + "=" * 60)
        print("📊 ATTRIBUTION DASHBOARD")
        print("=" * 60)
        
        # 1. Attribution stats
        print("\n📈 Attribution Stats:")
        stats = self.engine.get_stats()
        print(f"  Total Trades  : {stats.get('total', 0)}")
        print(f"  Win Rate      : {stats.get('win_rate', 0):.1f}%")
        
        # 2. Top reasons
        top_reasons = stats.get('top_reasons', [])
        if top_reasons:
            print("\n🔍 Top Reasons:")
            for reason, count in top_reasons[:5]:
                wr = stats.get('reason_win_rate', {}).get(reason, 0)
                icon = "✅" if wr > 50 else "❌" if wr < 30 else "⚠️"
                print(f"  {icon} {reason}: {count} trades (WR: {wr:.1f}%)")
        
        # 3. Top patterns
        top_patterns = stats.get('top_patterns', [])
        if top_patterns:
            print("\n📈 Top Patterns:")
            for pattern, count in top_patterns[:5]:
                print(f"  {pattern}: {count} trades")
        
        # 4. Learnings summary
        print("\n💡 Learning Insights:")
        print(self.learner.get_summary())
        
        print("\n" + "=" * 60)


def show_attribution_dashboard():
    """Show attribution dashboard"""
    dashboard = AttributionDashboard()
    dashboard.show()
