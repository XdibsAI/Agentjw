"""
sicuan/actions/build_task_queue.py
====================================
Generate task queue dari goals, projects, reflection state.
Pakai ExecutiveEngine jika tersedia, fallback ke inline logic.
"""

import json
from pathlib import Path


def execute(brain=None, **kwargs) -> str:
    root = Path(__file__).resolve().parents[2]
    memory = root / "memory"

    # Coba pakai ExecutiveEngine dulu
    try:
        from sicuan.core.executive_engine import ExecutiveEngine
        engine = ExecutiveEngine()
        engine.run()
        # Baca hasil dari disk
        state = json.loads((memory / "executive_state.json").read_text(encoding="utf-8"))
        queue = json.loads((memory / "task_queue.json").read_text(encoding="utf-8"))
    except Exception:
        # Fallback: inline logic
        queue = _build_queue_inline(root, memory)
        state = {
            "current_focus": queue[0] if queue else "idle",
            "priority": queue,
        }
        try:
            (memory / "task_queue.json").write_text(
                json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            (memory / "executive_state.json").write_text(
                json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        except Exception:
            pass

    focus = state.get("current_focus") or "idle"
    n = len(queue)

    lines = [
        f"✅ Task queue diperbarui — {n} task dalam antrian.",
        "",
        f"🎯 Fokus sekarang: **{focus}**",
        "",
        f"📋 Top {min(5, n)} prioritas:",
    ]
    for i, task in enumerate(queue[:5], 1):
        lines.append(f"  {i}. {task}")
    if n > 5:
        lines.append(f"  ... dan {n - 5} task lainnya")

    return "\n".join(lines)


def _build_queue_inline(root, memory):
    """Inline fallback kalau ExecutiveEngine tidak tersedia."""
    queue = []

    # Goals driven
    try:
        goals_path = memory / "goals.json"
        if goals_path.exists():
            goals = json.loads(goals_path.read_text(encoding="utf-8"))
            primary = goals.get("primary_goal", "")
            if primary:
                queue.append(f"Pursue: {primary}")
            for g in goals.get("long_term_goals", [])[:2]:
                queue.append(f"Work toward: {g}")
    except Exception:
        pass

    # Reflection driven
    try:
        ref_path = memory / "reflection_state.json"
        if ref_path.exists():
            reflection = json.loads(ref_path.read_text(encoding="utf-8"))
            for problem in reflection.get("problems", [])[:3]:
                queue.append(f"Investigate: {problem}")
    except Exception:
        pass

    # Project driven
    try:
        from memory.unified_projects import unified_projects
        projects = unified_projects.list_projects()
        if projects:
            name = projects[0]["name"]
            queue.extend([f"Review project {name}", f"Improve {name}"])
    except Exception:
        pass

    # Health check
    try:
        import os
        py_count = sum(
            len([f for f in files if f.endswith(".py")])
            for _, _, files in os.walk(root / "sicuan")
        )
        if py_count > 50:
            queue.append("Maintain codebase health")
    except Exception:
        pass

    # Deduplicate
    seen = set()
    final = []
    for t in queue:
        if t not in seen:
            final.append(t)
            seen.add(t)

    return final if final else ["Review codebase health", "Check project status"]
