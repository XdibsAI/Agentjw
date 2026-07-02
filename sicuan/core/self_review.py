"""Self-review berbasis data - file terpisah"""

from sicuan.core.self_review_data import get_self_review

def get_self_review_report() -> str:
    """Generate self-review report"""
    try:
        review = get_self_review()
        report = review.generate()
        
        lines = [
            "📊 **Self-Review SiCuan - Berbasis Data**",
            "",
            "📈 **Metrik:**",
        ]
        for key, value in report['metrics'].items():
            lines.append(f"  • {key}: {value}")
        
        if report['issues']:
            lines.append("")
            lines.append("⚠️ **Issues Terdeteksi:**")
            for issue in report['issues']:
                lines.append(f"  • {issue}")
        
        if report['recommendations']:
            lines.append("")
            lines.append("💡 **Rekomendasi:**")
            for rec in report['recommendations']:
                lines.append(f"  • {rec}")
        
        lines.append("")
        lines.append(f"📝 **Summary:** {report['summary']}")
        
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error generating self-review: {e}"
