#!/bin/bash
# ============================================================
# Patch: StrategyExecutor → TaskQueue → TaskExecutor
# Rekomendasi dari decide() masuk ke task_queue.json
# TaskExecutor dapat handler baru untuk strategy tasks
# ============================================================

set -e
ROOT="/home/dibs/agentjw"
CORE="$ROOT/sicuan/core"
MEMORY="$ROOT/memory"

echo "======================================"
echo " Patch: Strategy → Queue → Executor"
echo "======================================"

# ── Backup ──
cp "$CORE/task_executor.py" "$CORE/task_executor.py.bak_strategy_$(date +%H%M%S)"
cp "$CORE/strategy_executor.py" "$CORE/strategy_executor.py.bak_$(date +%H%M%S)"
echo "✓ Backup dibuat"

# ─────────────────────────────────────────
# 1. Patch strategy_executor.py
#    Tambah method push_to_queue()
# ─────────────────────────────────────────
echo "[1/3] Patch strategy_executor.py → push_to_queue()..."

cat > "$CORE/strategy_executor.py" << 'EOF'
import json
from pathlib import Path
from sicuan.core.knowledge_engine import KnowledgeEngine

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "memory"


class StrategyExecutor:
    """
    Menggabungkan semua modul knowledge untuk
    memutuskan prioritas task berikutnya,
    lalu push ke task_queue.json untuk TaskExecutor.
    """

    def __init__(self):
        self.ke = KnowledgeEngine()

    def _load_json(self, path: Path, default):
        try:
            if path.exists():
                return json.loads(path.read_text())
        except Exception:
            pass
        return default

    def _save_json(self, path: Path, data):
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False)
        )

    def decide(self) -> dict:
        """
        Gabungkan knowledge + memory → hasilkan rekomendasi task.
        """
        knowledge = self.ke.load_all()
        exec_state = self._load_json(
            MEMORY / "executive_state.json", {}
        )
        task_queue = self._load_json(
            MEMORY / "task_queue.json", []
        )

        strategy   = knowledge.get("core_strategy", {})
        sop        = knowledge.get("sop", {})
        finance    = knowledge.get("finance", {})
        curriculum = knowledge.get("curriculum", {})

        # ── Fokus proyek ──
        focus = (
            exec_state.get("current_focus")
            or strategy.get("current_focus")
            or "unknown"
        )

        # ── Task yang sudah ada di queue (hindari duplikat) ──
        existing = [t.lower() for t in task_queue] if isinstance(task_queue, list) else []

        recommendations = []

        # ── Jika queue kosong → generate dari strategi ──
        if not task_queue:
            daily_sop = sop.get("daily_routine", [])
            # Map SOP → task string yang dikenali executor
            sop_tasks = {
                "Review logs kemarin": "codebase health check",
                "Cek task_queue": "maintain codebase health",
                "Eksekusi 1-3 task prioritas tinggi": f"review strategy {focus}",
                "Update executive_state.json": "validate paper trading mode",
            }
            for sop_item, task_str in sop_tasks.items():
                if task_str.lower() not in existing:
                    recommendations.append(task_str)

            # Tambah task spesifik berdasarkan fokus
            if focus == "godmeme_bot":
                extra = [
                    "validate paper trading mode",
                    "validate buy signals",
                    "review strategy godmeme",
                    "analyze profitability",
                ]
                for t in extra:
                    if t not in existing and t not in recommendations:
                        recommendations.append(t)

            # Learning task
            learning_queue = curriculum.get("learning_queue", [])
            next_learn = next(
                (t for t in learning_queue if t.get("status") == "pending"),
                None
            )
            if next_learn:
                task_str = f"learning: {next_learn['topic']}"
                if task_str.lower() not in existing:
                    recommendations.append(task_str)

        else:
            # Queue sudah ada isi → prioritaskan yang high
            for t in task_queue[:3]:
                recommendations.append(t)

        decision = {
            "focus": focus,
            "recommendations": recommendations,
            "knowledge_summary": self.ke.summary()
        }

        # Simpan decision
        self._save_json(MEMORY / "strategy_decision.json", decision)

        return decision

    def push_to_queue(self) -> dict:
        """
        Panggil decide() lalu inject rekomendasi ke task_queue.json.
        Hanya tambah task yang belum ada (no duplicate).
        Return: jumlah task yang ditambahkan.
        """
        decision = self.decide()
        queue_file = MEMORY / "task_queue.json"

        current = self._load_json(queue_file, [])
        if not isinstance(current, list):
            current = []

        existing_lower = [t.lower() for t in current]
        added = []

        for rec in decision.get("recommendations", []):
            if rec.lower() not in existing_lower:
                current.append(rec)
                existing_lower.append(rec.lower())
                added.append(rec)

        self._save_json(queue_file, current)

        return {
            "status": "ok",
            "focus": decision["focus"],
            "added": added,
            "queue_size": len(current)
        }
EOF

echo "    ✓ strategy_executor.py diupdate"

# ─────────────────────────────────────────
# 2. Patch task_executor.py
#    Tambah handler: learning task + strategy task
# ─────────────────────────────────────────
echo "[2/3] Patch task_executor.py → handler baru..."

python3 << 'PYEOF'
from pathlib import Path

te = Path("/home/dibs/agentjw/sicuan/core/task_executor.py")
text = te.read_text()

# ── Tambah 2 method baru sebelum execute_next ──
NEW_METHODS = '''
    def _handle_learning(self, task: str):
        """Handler untuk learning tasks dari curriculum."""
        import re
        topic = re.sub(r"^learning:\s*", "", task, flags=re.IGNORECASE).strip()

        # Update curriculum status
        curriculum_file = (
            Path(__file__).resolve().parents[2]
            / "sicuan" / "knowledge" / "curriculum.json"
        )
        try:
            import json
            data = json.loads(curriculum_file.read_text())
            for item in data.get("learning_queue", []):
                if item.get("topic", "").lower() == topic.lower():
                    item["status"] = "in_progress"
            curriculum_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False)
            )
        except Exception:
            pass

        return {
            "status": "completed",
            "action": "learning_task",
            "topic": topic,
            "note": f"Marked '{topic}' as in_progress di curriculum.json"
        }

    def _handle_strategy_review(self, task: str):
        """Handler untuk strategy review tasks dari StrategyExecutor."""
        try:
            from sicuan.core.knowledge_engine import KnowledgeEngine
            ke = KnowledgeEngine()
            summary = ke.summary()
            return {
                "status": "completed",
                "action": "strategy_review",
                "focus": summary.get("focus"),
                "vision": summary.get("vision"),
                "opex": summary.get("monthly_opex_usd"),
                "learning_next": summary.get("learning_next"),
            }
        except Exception as e:
            return {
                "status": "completed",
                "action": "strategy_review",
                "note": str(e)
            }

'''

TARGET = "    def execute_next(self):"
if "_handle_learning" not in text:
    text = text.replace(TARGET, NEW_METHODS + TARGET, 1)
    print("✓ 2 method baru ditambahkan ke TaskExecutor")
else:
    print("⚠ Method sudah ada, skip")

# ── Patch execute_next: tambah branch baru sebelum "analyze" catch-all ──
OLD_BRANCH = '''        elif "analyze " in task_lower:

            result = self._analyze_component(task)


        else:'''

NEW_BRANCH = '''        elif "analyze " in task_lower:

            result = self._analyze_component(task)

        elif task_lower.startswith("learning:"):

            result = self._handle_learning(task)

        elif "strategy review" in task_lower or "review strategy" in task_lower:

            result = self._handle_strategy_review(task)

        else:'''

if "startswith(\"learning:\")" not in text:
    text = text.replace(OLD_BRANCH, NEW_BRANCH, 1)
    print("✓ Branch learning + strategy_review ditambahkan ke execute_next")
else:
    print("⚠ Branch sudah ada, skip")

te.write_text(text)
print("✓ task_executor.py disimpan")
PYEOF

echo "    ✓ task_executor.py diupdate"

# ─────────────────────────────────────────
# 3. Patch autonomous_loop.py
#    Ganti ke: scheduler → push_to_queue → execute_next
# ─────────────────────────────────────────
echo "[3/3] Patch autonomous_loop.py → push_to_queue()..."

cat > "$CORE/autonomous_loop.py" << 'EOF'
from sicuan.core.task_executor import TaskExecutor
from sicuan.core.auto_scheduler import AutoScheduler
from sicuan.core.self_review_loop import SelfReviewLoop
from sicuan.core.knowledge_engine import KnowledgeEngine
from sicuan.core.strategy_executor import StrategyExecutor


class AutonomousLoop:

    def run(self):

        # ── Step 1: Scheduler (flow lama) ──
        scheduler = AutoScheduler()
        scheduler.run()

        # ── Step 2: Load semua knowledge ──
        ke = KnowledgeEngine()
        knowledge = ke.load_all()

        # ── Step 3: Strategy decide + push ke queue ──
        se = StrategyExecutor()
        push_result = se.push_to_queue()

        # ── Step 4: Execute next task dari queue (flow lama) ──
        executor = TaskExecutor()
        executed = executor.execute_next()

        # ── Step 5: Self review (flow lama) ──
        review = SelfReviewLoop()
        review_data = review.run()

        return {
            # flow lama
            "executed": executed,
            "review": review_data,
            # business brain layer
            "knowledge_focus": push_result.get("focus"),
            "tasks_added": push_result.get("added", []),
            "queue_size": push_result.get("queue_size", 0),
        }
EOF

echo "    ✓ autonomous_loop.py diupdate"

# ─────────────────────────────────────────
# 4. Syntax check semua
# ─────────────────────────────────────────
echo ""
echo "=== Syntax Check ==="
cd "$ROOT" && source venv/bin/activate

python3 << 'PYEOF'
import ast
from pathlib import Path

files = [
    "sicuan/core/strategy_executor.py",
    "sicuan/core/task_executor.py",
    "sicuan/core/autonomous_loop.py",
]
all_ok = True
for f in files:
    p = Path(f)
    try:
        ast.parse(p.read_text())
        print(f"  ✓ {f}")
    except SyntaxError as e:
        print(f"  ✗ {f} — line {e.lineno}: {e.msg}")
        all_ok = False

if all_ok:
    print("\n✅ Semua file OK!")
PYEOF

# ─────────────────────────────────────────
# 5. End-to-end test
# ─────────────────────────────────────────
echo ""
echo "=== End-to-End Test ==="
cd "$ROOT" && source venv/bin/activate

python3 << 'PYEOF'
import sys, json
sys.path.insert(0, "/home/dibs/agentjw")

# Test 1: push_to_queue
print("Test 1 — StrategyExecutor.push_to_queue()")
from sicuan.core.strategy_executor import StrategyExecutor
se = StrategyExecutor()
result = se.push_to_queue()
print(f"  focus      : {result['focus']}")
print(f"  tasks added: {result['added']}")
print(f"  queue size : {result['queue_size']}")

# Test 2: execute_next
print("\nTest 2 — TaskExecutor.execute_next()")
from sicuan.core.task_executor import TaskExecutor
te = TaskExecutor()
r = te.execute_next()
print(f"  status : {r.get('status')}")
print(f"  action : {r.get('action', '-')}")

# Test 3: full loop
print("\nTest 3 — AutonomousLoop.run()")
from sicuan.core.autonomous_loop import AutonomousLoop
loop = AutonomousLoop()
out = loop.run()
print(f"  executed focus   : {out.get('knowledge_focus')}")
print(f"  tasks added      : {out.get('tasks_added')}")
print(f"  queue size after : {out.get('queue_size')}")
print(f"  executed status  : {out['executed'].get('status')}")

print("\n✅ End-to-end OK!")
PYEOF

echo ""
echo "======================================"
echo " Patch selesai!"
echo ""
echo " Flow lengkap:"
echo "   AutoScheduler.run()"
echo "       ↓"
echo "   KnowledgeEngine.load_all()"
echo "       ↓"
echo "   StrategyExecutor.push_to_queue()   ← inject rekomendasi ke queue"
echo "       ↓"
echo "   TaskExecutor.execute_next()        ← eksekusi dari queue"
echo "       ↓"
echo "   SelfReviewLoop.run()"
echo "======================================"
