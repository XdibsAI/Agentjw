"""
sicuan/actions/shadow_mode_report.py
=====================================
Tampilkan laporan Shadow Mode SiCuan dari memory/shadow_report.json
"""
import json
from pathlib import Path


def execute(brain=None, **kwargs) -> str:
    root = Path(__file__).resolve().parents[2]
    report_path = root / "memory" / "shadow_report.json"

    if not report_path.exists():
        return "⚠️ Shadow Mode report belum ada. Jalankan dulu beberapa action agar data terkumpul."

    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"❌ Gagal baca shadow report: {e}"

    total = data.get("total_comparisons", 0)
    match_rate = data.get("match_rate", 0)
    by_action = data.get("by_action", {})
    last_updated = data.get("last_updated", "")[:16]

    lines = [
        f"🔦 SHADOW MODE REPORT",
        f"",
        f"📊 Total comparisons: {total:,}",
        f"✅ Match rate: {match_rate:.1f}%",
        f"🕐 Last updated: {last_updated}",
        f"",
        f"📋 Per action:",
    ]

    for action, stats in sorted(by_action.items(),
                                 key=lambda x: x[1].get("total", 0),
                                 reverse=True)[:10]:
        total_a = stats.get("total", 0)
        match_a = stats.get("match_rate", 0)
        emoji = "✅" if match_a >= 80 else "⚠️" if match_a >= 60 else "❌"
        lines.append(f"  {emoji} {action}: {match_a:.0f}% ({total_a} comparisons)")

    return "\n".join(lines)
