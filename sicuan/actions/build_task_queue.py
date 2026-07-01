"""
sicuan/actions/build_task_queue.py
====================================
Action: build_task_queue

Jalankan ExecutiveEngine.run() untuk generate task queue
berbasis goals, project registry, dan reflection state.
ONE-SHOT — tidak ada loop otomatis.

Trigger: "buat task queue", "update prioritas", "apa fokus sekarang"
"""

from pathlib import Path
import json


def execute(brain=None, **kwargs) -> str:
    try:
        from sicuan.core.executive_engine import ExecutiveEngine
    except ImportError as e:
        return f"❌ Gagal import ExecutiveEngine: {e}"

    try:
        engine = ExecutiveEngine()
        engine.run()
    except Exception as e:
        return f"❌ ExecutiveEngine.run() gagal: {e}"

    root = Path(__file__).resolve().parents[2]
    state_path = root / "memory" / "executive_state.json"
    queue_path = root / "memory" / "task_queue.json"

    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
    except Exception as e:
        return f"⚠️ run() selesai tapi gagal baca hasil: {e}"

    focus = state.get("current_focus") or "idle"
    n = len(queue)
    top5 = queue[:5]

    lines = [
        f"✅ Task queue diperbarui — {n} task dalam antrian.",
        f"",
        f"🎯 Fokus sekarang: **{focus}**",
        f"",
        f"📋 Top {min(5, n)} prioritas:",
    ]
    for i, task in enumerate(top5, 1):
        lines.append(f"  {i}. {task}")
    if n > 5:
        lines.append(f"  ... dan {n - 5} task lainnya (lihat memory/task_queue.json)")

    return "\n".join(lines)
