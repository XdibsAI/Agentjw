#!/bin/bash
# ============================================================
# SiCuan Business Brain Setup
# Tanpa mengubah flow lama
# Jalankan: bash setup_business_brain.sh
# ============================================================

set -e
ROOT="/home/dibs/agentjw"
KNOWLEDGE="$ROOT/sicuan/knowledge"
CORE="$ROOT/sicuan/core"

echo "======================================"
echo " SiCuan Business Brain Setup"
echo "======================================"

# ─────────────────────────────────────────
# 1. JSON KNOWLEDGE FILES
# ─────────────────────────────────────────

echo "[1/4] Membuat knowledge JSON files..."

cat > "$KNOWLEDGE/core_strategy.json" << 'EOF'
{
  "vision": "Membangun bisnis digital yang menghasilkan income pasif dan aktif",
  "mission": "Otomasi, project, dan monetisasi dengan bantuan AI",
  "pillars": [
    "Automasi proses bisnis",
    "Trading bot & DeFi",
    "Konten & personal branding",
    "SaaS & tool development"
  ],
  "current_focus": "godmeme_bot",
  "quarterly_targets": {
    "Q3_2026": "Godmeme bot live trading + 1 SaaS MVP"
  },
  "principles": [
    "Ship fast, iterate faster",
    "Revenue before perfection",
    "Automate what repeats"
  ]
}
EOF

cat > "$KNOWLEDGE/curriculum.json" << 'EOF'
{
  "current_skills": [
    "Python", "FastAPI", "Telegram Bot", "Solana/DeFi", "LLM Integration"
  ],
  "learning_queue": [
    {
      "topic": "DeFi MEV & sandwich strategy",
      "priority": "high",
      "status": "in_progress",
      "resource": "internal - godmeme_bot codebase"
    },
    {
      "topic": "Marketing funnel automation",
      "priority": "medium",
      "status": "pending",
      "resource": "tbd"
    },
    {
      "topic": "LLM fine-tuning untuk trading signal",
      "priority": "medium",
      "status": "pending",
      "resource": "tbd"
    }
  ],
  "completed": [],
  "weekly_learning_hours": 5
}
EOF

cat > "$KNOWLEDGE/sop.json" << 'EOF'
{
  "project_start": [
    "Buat folder di projects/",
    "Init requirements.txt",
    "Buat README.md dengan goal & status",
    "Daftarkan ke memory/project_state.json"
  ],
  "deploy_checklist": [
    "Cek semua env variable tersedia",
    "Test di mode dry_run dulu",
    "Backup config lama sebelum replace",
    "Log output ke logs/"
  ],
  "bug_handling": [
    "Reproduksi error dulu",
    "Buat .bak sebelum edit",
    "Fix satu hal per commit",
    "Verifikasi dengan syntax check"
  ],
  "daily_routine": [
    "Review logs kemarin",
    "Cek task_queue",
    "Eksekusi 1-3 task prioritas tinggi",
    "Update executive_state.json"
  ]
}
EOF

cat > "$KNOWLEDGE/branding.json" << 'EOF'
{
  "brand_name": "SiCuan / AgentJW",
  "tone": {
    "formal": "profesional, lugas, percaya diri",
    "casual": "santai, friendly, sedikit humor",
    "technical": "presisi, pakai istilah yang tepat"
  },
  "target_audience": [
    "Developer Indonesia yang ingin otomasi",
    "Trader crypto yang butuh tools",
    "Builder yang ingin leverage AI"
  ],
  "content_pillars": [
    "Tutorial & how-to",
    "Behind the scenes building",
    "Income report & transparency",
    "AI x bisnis lokal"
  ],
  "platforms": {
    "primary": "Telegram",
    "secondary": ["Twitter/X", "YouTube"],
    "future": ["TikTok", "Newsletter"]
  },
  "tagline": "AI yang kerja, bukan cuma ngobrol"
}
EOF

cat > "$KNOWLEDGE/finance.json" << 'EOF'
{
  "monthly_budget": {
    "server": 20,
    "api_llm": 30,
    "tools_subscriptions": 10,
    "total_opex": 60,
    "currency": "USD"
  },
  "income_streams": [
    {
      "source": "godmeme_bot trading",
      "status": "development",
      "target_monthly": 500,
      "currency": "USD"
    },
    {
      "source": "SaaS / tools",
      "status": "planned",
      "target_monthly": 200,
      "currency": "USD"
    }
  ],
  "alerts": {
    "llm_cost_daily_limit_usd": 5,
    "notify_if_exceeded": true
  },
  "tracking_file": "logs/cost_tracker.json"
}
EOF

cat > "$KNOWLEDGE/hr_culture.json" << 'EOF'
{
  "values": [
    "Ownership — selesaikan apa yang dimulai",
    "Transparansi — lapor progress & masalah jujur",
    "Iterasi cepat — jangan nunggu sempurna",
    "Belajar terus — tiap error adalah pelajaran"
  ],
  "working_style": {
    "hours": "async, kapanpun produktif",
    "communication": "Telegram untuk update penting",
    "review_cycle": "daily self-review via SiCuan"
  },
  "ai_agent_rules": [
    "Jangan hapus file tanpa backup",
    "Jangan deploy ke production tanpa dry_run",
    "Selalu log apa yang dikerjakan",
    "Minta konfirmasi untuk aksi irreversible"
  ],
  "culture_notes": "Ini bukan kerjaan 9-5. Ini membangun sesuatu. Tiap baris code adalah investasi."
}
EOF

echo "    ✓ 6 knowledge files dibuat"

# ─────────────────────────────────────────
# 2. KnowledgeEngine
# ─────────────────────────────────────────

echo "[2/4] Membuat KnowledgeEngine..."

cat > "$CORE/knowledge_engine.py" << 'EOF'
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
EOF

echo "    ✓ knowledge_engine.py dibuat"

# ─────────────────────────────────────────
# 3. StrategyExecutor
# ─────────────────────────────────────────

echo "[3/4] Membuat StrategyExecutor..."

cat > "$CORE/strategy_executor.py" << 'EOF'
import json
from pathlib import Path
from sicuan.core.knowledge_engine import KnowledgeEngine

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "memory"


class StrategyExecutor:
    """
    Menggabungkan semua modul knowledge untuk
    memutuskan prioritas task berikutnya.
    Dipanggil setelah KnowledgeEngine.load_all().
    Tidak menggantikan TaskExecutor — hanya memberi arahan.
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
        Gabungkan knowledge + memory → hasilkan arahan
        untuk TaskExecutor.
        """
        knowledge = self.ke.load_all()
        exec_state = self._load_json(
            MEMORY / "executive_state.json", {}
        )
        task_queue = self._load_json(
            MEMORY / "task_queue.json", {"tasks": []}
        )

        strategy = knowledge.get("core_strategy", {})
        sop = knowledge.get("sop", {})
        finance = knowledge.get("finance", {})
        curriculum = knowledge.get("curriculum", {})

        # ── Tentukan fokus proyek ──
        focus = (
            exec_state.get("current_focus")
            or strategy.get("current_focus")
            or "unknown"
        )

        # ── Cek apakah ada task di queue ──
        pending_tasks = [
            t for t in task_queue.get("tasks", [])
            if t.get("status") == "pending"
        ]

        # ── Cek budget alert ──
        budget_ok = True
        daily_limit = (
            finance.get("alerts", {})
            .get("llm_cost_daily_limit_usd", 99)
        )
        # (cost check bisa dikembangkan ke cost_tracker.json)

        # ── Generate rekomendasi ──
        recommendations = []

        if not pending_tasks:
            # Tidak ada task → generate berdasarkan strategi
            recommendations.append({
                "type": "strategy_task",
                "project": focus,
                "action": f"Review & lanjutkan progress {focus}",
                "sop": sop.get("daily_routine", []),
                "priority": "high"
            })

            # Tambah learning task jika ada
            learning_queue = curriculum.get("learning_queue", [])
            next_learn = next(
                (t for t in learning_queue
                 if t.get("status") == "pending"),
                None
            )
            if next_learn:
                recommendations.append({
                    "type": "learning_task",
                    "topic": next_learn["topic"],
                    "action": f"Pelajari: {next_learn['topic']}",
                    "priority": "medium"
                })
        else:
            # Ada task di queue → prioritaskan
            for t in pending_tasks[:3]:
                recommendations.append({
                    "type": "queued_task",
                    "action": t.get("description", str(t)),
                    "priority": t.get("priority", "medium")
                })

        decision = {
            "focus": focus,
            "budget_ok": budget_ok,
            "recommendations": recommendations,
            "knowledge_summary": self.ke.summary()
        }

        # Simpan decision ke memory
        self._save_json(
            MEMORY / "strategy_decision.json",
            decision
        )

        return decision
EOF

echo "    ✓ strategy_executor.py dibuat"

# ─────────────────────────────────────────
# 4. Patch AutonomousLoop (tanpa ubah flow lama)
# ─────────────────────────────────────────

echo "[4/4] Patching autonomous_loop.py..."

cat > "$CORE/autonomous_loop.py" << 'EOF'
from sicuan.core.task_executor import TaskExecutor
from sicuan.core.auto_scheduler import AutoScheduler
from sicuan.core.self_review_loop import SelfReviewLoop
from sicuan.core.knowledge_engine import KnowledgeEngine
from sicuan.core.strategy_executor import StrategyExecutor


class AutonomousLoop:

    def run(self):

        # ── Flow lama (tidak diubah) ──
        scheduler = AutoScheduler()
        executor = TaskExecutor()
        review = SelfReviewLoop()

        scheduler.run()

        # ── Tambahan: Business Brain Layer ──
        ke = KnowledgeEngine()
        knowledge = ke.load_all()          # load semua modul

        se = StrategyExecutor()
        decision = se.decide()             # gabungkan → arahan

        # ── Eksekusi task (flow lama) ──
        executed = executor.execute_next()

        review_data = review.run()

        return {
            "executed": executed,
            "review": review_data,
            # context tambahan dari business brain
            "knowledge_focus": decision.get("focus"),
            "recommendations": decision.get("recommendations", []),
            "knowledge_summary": decision.get("knowledge_summary", {})
        }
EOF

echo "    ✓ autonomous_loop.py di-patch"

# ─────────────────────────────────────────
# 5. Buat memory/strategy_decision.json kosong
# ─────────────────────────────────────────

cat > "$ROOT/memory/strategy_decision.json" << 'EOF'
{
  "focus": "",
  "budget_ok": true,
  "recommendations": [],
  "knowledge_summary": {}
}
EOF

# ─────────────────────────────────────────
# 6. Syntax check semua file baru
# ─────────────────────────────────────────

echo ""
echo "=== Syntax Check ==="
cd "$ROOT" && source venv/bin/activate

python3 << 'PYEOF'
import ast
from pathlib import Path

files = [
    "sicuan/core/knowledge_engine.py",
    "sicuan/core/strategy_executor.py",
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
else:
    print("\n❌ Ada error — cek file di atas")
PYEOF

echo ""
echo "======================================"
echo " Setup selesai!"
echo ""
echo " Flow baru:"
echo "   AutoScheduler"
echo "       ↓"
echo "   KnowledgeEngine.load_all()"
echo "       ↓"
echo "   StrategyExecutor.decide()"
echo "       ↓"
echo "   TaskExecutor.execute_next()   ← flow lama tetap jalan"
echo ""
echo " File baru:"
echo "   sicuan/knowledge/core_strategy.json"
echo "   sicuan/knowledge/curriculum.json"
echo "   sicuan/knowledge/sop.json"
echo "   sicuan/knowledge/branding.json"
echo "   sicuan/knowledge/finance.json"
echo "   sicuan/knowledge/hr_culture.json"
echo "   sicuan/core/knowledge_engine.py"
echo "   sicuan/core/strategy_executor.py"
echo "   sicuan/core/autonomous_loop.py  (patched)"
echo "   memory/strategy_decision.json"
echo "======================================"
