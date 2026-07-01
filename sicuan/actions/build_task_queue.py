"""
sicuan/actions/build_task_queue.py
====================================
Generate task queue dari goals, projects, reflection state.
Ditulis langsung tanpa dependency ExecutiveEngine.
"""

import json
from pathlib import Path


def execute(brain=None, **kwargs) -> str:
    root = Path(__file__).resolve().parents[2]
    memory = root / "memory"

    queue = []

    # Dari reflection state — problem driven
    reflection_path = memory / "reflection_state.json"
    if reflection_path.exists():
        try:
            reflection = json.loads(reflection_path.read_text(encoding="utf-8"))
            for problem in reflection.get("problems", []):
                p = problem.lower()
                if "scanner" in p:
                    queue.extend(["Analyze strategy.py", "Validate DexScreener filters"])
                elif "capabilit" in p:
                    queue.append("Repair capability detection")
                else:
                    queue.append(f"Investigate: {problem}")
        except Exception:
            pass

    # Dari project registry — project driven
    try:
        from memory.unified_projects import unified_projects
        projects = unified_projects.list_projects()
        if projects:
            name = projects[0]["name"]
            queue.extend([
                f"Review project {name}",
                f"Analyze {name}",
                f"Improve project {name}",
            ])
    except Exception:
        pass

    # Dari workspace — health check
    try:
        import os
        py_files = sum(
            len([f for f in files if f.endswith(".py")])
            for _, _, files in os.walk(root / "sicuan")
        )
        if py_files > 50:
            queue.append("Maintain codebase health")
    except Exception:
        pass

    # Deduplikasi
    seen = set()
    final_queue = []
    for task in queue:
        if task not in seen:
            final_queue.append(task)
            seen.add(task)

    if not final_queue:
        final_queue = ["Review codebase health", "Check project status"]

    # Simpan ke memory
    try:
        (memory / "task_queue.json").write_text(
            json.dumps(final_queue, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        state = {
            "current_focus": final_queue[0],
            "priority": final_queue,
            "next_action": final_queue[0],
        }
        (memory / "executive_state.json").write_text(
            json.dumps(state, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
    except Exception:
        pass

    focus = final_queue[0]
    n = len(final_queue)
    lines = [
        f"✅ Task queue diperbarui — {n} task dalam antrian.",
        f"",
        f"🎯 Fokus sekarang: **{focus}**",
        f"",
        f"📋 Top {min(5, n)} prioritas:",
    ]
    for i, task in enumerate(final_queue[:5], 1):
        lines.append(f"  {i}. {task}")
    if n > 5:
        lines.append(f"  ... dan {n - 5} task lainnya")

    return "\n".join(lines)
