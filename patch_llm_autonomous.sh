#!/bin/bash
# ============================================================
# Patch: LLM-Driven AutonomousLoop
# Hapus keyword parsing — LLM yang decide & execute
# ============================================================

set -e
ROOT="/home/dibs/agentjw"
CORE="$ROOT/sicuan/core"

echo "======================================"
echo " Patch: LLM-Driven Autonomous Loop"
echo "======================================"

# Backup
cp "$CORE/autonomous_loop.py" "$CORE/autonomous_loop.py.bak_llm_$(date +%H%M%S)"
echo "✓ Backup dibuat"

# ─────────────────────────────────────────
# 1. LLM-Driven TaskExecutor (ganti keyword parsing)
# ─────────────────────────────────────────
echo "[1/2] Membuat llm_task_executor.py..."

cat > "$CORE/llm_task_executor.py" << 'EOF'
"""
LLM-Driven Task Executor
Tidak ada keyword parsing — LLM yang baca context, decide, dan execute.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[2]
MEMORY = ROOT / "memory"
sys.path.insert(0, str(ROOT))


class LLMTaskExecutor:

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from core.llm_client import llm
            self._llm = llm
        return self._llm

    # ── Tools yang tersedia untuk LLM ──

    def _tool_read_file(self, path: str) -> str:
        from mcp.tools.filesystem_tool import filesystem_tool
        r = filesystem_tool.read_file(path)
        return r.get("content", str(r))[:2000]

    def _tool_list_dir(self, path: str) -> str:
        from mcp.tools.filesystem_tool import filesystem_tool
        r = filesystem_tool.list_dir(path)
        return json.dumps(r, ensure_ascii=False)[:1000]

    def _tool_read_log(self, project_dir: str, lines: int = 30) -> str:
        from mcp.tools.filesystem_tool import filesystem_tool
        r = filesystem_tool.read_log(project_dir, lines)
        return str(r)[:2000]

    def _tool_scan_project(self, project_dir: str) -> str:
        from mcp.tools.filesystem_tool import filesystem_tool
        r = filesystem_tool.scan_project(project_dir)
        return json.dumps(r, ensure_ascii=False)[:2000]

    def _tool_check_syntax(self, path: str) -> str:
        from mcp.tools.filesystem_tool import filesystem_tool
        r = filesystem_tool.check_syntax(path)
        return json.dumps(r)

    def _tool_send_message(self, message: str) -> str:
        from mcp.tools.openclaw_tool import send_message
        ok = send_message(message)
        return "sent" if ok else "failed"

    def _tool_write_file(self, path: str, content: str) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"written: {path}"

    def _tool_run_script(self, project_dir: str, script: str = "main.py") -> str:
        from mcp.tools.filesystem_tool import filesystem_tool
        r = filesystem_tool.run_and_capture(project_dir, script)
        out = str(r.get("stdout", ""))[:1000]
        err = str(r.get("stderr", ""))[:500]
        return f"stdout: {out}\nstderr: {err}"

    # ── Tool registry ──

    TOOLS = {
        "read_file": {
            "desc": "Baca isi file. Args: path (str)",
            "fn": "_tool_read_file"
        },
        "list_dir": {
            "desc": "List isi folder. Args: path (str)",
            "fn": "_tool_list_dir"
        },
        "read_log": {
            "desc": "Baca log project. Args: project_dir (str), lines (int, optional)",
            "fn": "_tool_read_log"
        },
        "scan_project": {
            "desc": "Scan seluruh project — struktur, file, issues. Args: project_dir (str)",
            "fn": "_tool_scan_project"
        },
        "check_syntax": {
            "desc": "Cek syntax Python file. Args: path (str)",
            "fn": "_tool_check_syntax"
        },
        "send_message": {
            "desc": "Kirim pesan ke Telegram owner. Args: message (str)",
            "fn": "_tool_send_message"
        },
        "write_file": {
            "desc": "Tulis/update file. Args: path (str), content (str)",
            "fn": "_tool_write_file"
        },
        "run_script": {
            "desc": "Jalankan script Python di project. Args: project_dir (str), script (str)",
            "fn": "_tool_run_script"
        },
    }

    def _load_context(self) -> dict:
        """Kumpulkan semua context nyata untuk dikirim ke LLM."""

        def _read(f, default):
            try:
                return json.loads(Path(f).read_text()) if Path(f).exists() else default
            except Exception:
                return default

        # Knowledge
        ke_summary = {}
        try:
            from sicuan.core.knowledge_engine import KnowledgeEngine
            ke_summary = KnowledgeEngine().summary()
        except Exception:
            pass

        return {
            "datetime": datetime.now().strftime("%Y-%m-%d %H:%M WIB"),
            "knowledge": ke_summary,
            "executive_state": _read(MEMORY / "executive_state.json", {}),
            "task_queue": _read(MEMORY / "task_queue.json", []),
            "recent_execution": _read(MEMORY / "execution_history.json", [])[-3:],
            "self_review": _read(MEMORY / "self_review.json", {}),
            "strategy_decision": _read(MEMORY / "strategy_decision.json", {}),
            "workspace": str(ROOT),
            "projects": [p.name for p in (ROOT / "projects").iterdir() if p.is_dir()]
                if (ROOT / "projects").exists() else [],
        }

    def _build_system_prompt(self) -> str:
        tools_desc = "\n".join(
            f"  - {name}: {info['desc']}"
            for name, info in self.TOOLS.items()
        )
        return f"""Kamu adalah SiCuan — autonomous AI agent yang benar-benar bekerja, bukan cuma ngobrol.

TUGASMU:
Setiap siklus, kamu harus memutuskan 1 aksi konkret berdasarkan context yang diberikan,
lalu eksekusi menggunakan tools yang tersedia.

TOOLS YANG KAMU PUNYA:
{tools_desc}

CARA RESPOND:
Kamu HARUS respond dalam format JSON berikut — tidak ada teks lain di luar JSON:

{{
  "thinking": "reasoning singkat kenapa pilih aksi ini",
  "action": "nama_tool atau 'none'",
  "args": {{"arg1": "val1"}},
  "summary": "1 kalimat apa yang kamu lakukan",
  "notify_owner": true/false,
  "notify_message": "pesan ke owner kalau notify_owner true"
}}

PRINSIP:
- Pilih aksi yang paling bernilai untuk bisnis saat ini
- Kalau queue kosong: scan project aktif, cek log, atau review health
- Kalau ada masalah nyata: notify owner via send_message
- Kalau tidak ada yang perlu dilakukan: action = "none"
- JANGAN buat task fiktif — selalu berdasarkan data nyata
- Maksimal 1 tool call per siklus"""

    def _execute_tool(self, action: str, args: dict) -> str:
        if action not in self.TOOLS:
            return f"unknown tool: {action}"
        fn_name = self.TOOLS[action]["fn"]
        fn = getattr(self, fn_name)
        try:
            return fn(**args)
        except Exception as e:
            return f"error: {e}"

    def _save_history(self, context: dict, decision: dict, tool_result: str):
        history_file = MEMORY / "execution_history.json"
        try:
            history = json.loads(history_file.read_text()) if history_file.exists() else []
        except Exception:
            history = []

        history.append({
            "timestamp": datetime.now().isoformat(),
            "focus": context.get("knowledge", {}).get("focus", "-"),
            "action": decision.get("action"),
            "args": decision.get("args", {}),
            "summary": decision.get("summary"),
            "tool_result": tool_result[:500] if tool_result else None,
        })

        # Keep last 50
        history = history[-50:]
        history_file.write_text(
            json.dumps(history, indent=2, ensure_ascii=False)
        )

    def run_cycle(self) -> dict:
        """
        1 siklus penuh:
        - Kumpulkan context
        - LLM decide aksi
        - Execute tool
        - Notify owner kalau perlu
        - Simpan history
        """
        context = self._load_context()

        # Kirim ke LLM
        prompt = f"CONTEXT:\n{json.dumps(context, indent=2, ensure_ascii=False, default=str)}"

        raw = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            system=self._build_system_prompt(),
            temperature=0.3,
            max_tokens=600,
        )

        # Parse JSON response
        try:
            clean = raw.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            decision = json.loads(clean.strip())
        except Exception as e:
            return {
                "status": "parse_error",
                "raw": raw[:300],
                "error": str(e)
            }

        action = decision.get("action", "none")
        args = decision.get("args", {})
        tool_result = None

        # Execute tool
        if action and action != "none":
            tool_result = self._execute_tool(action, args)

        # Notify owner kalau diminta LLM
        if decision.get("notify_owner") and decision.get("notify_message"):
            try:
                from mcp.tools.openclaw_tool import send_message
                send_message(f"🤖 SiCuan:\n{decision['notify_message']}")
            except Exception:
                pass

        # Simpan history
        self._save_history(context, decision, tool_result)

        # Update executive_state
        state_file = MEMORY / "executive_state.json"
        try:
            state = json.loads(state_file.read_text()) if state_file.exists() else {}
            state["last_action"] = action
            state["last_summary"] = decision.get("summary")
            state["last_run"] = datetime.now().isoformat()
            state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        except Exception:
            pass

        return {
            "status": "completed",
            "thinking": decision.get("thinking"),
            "action": action,
            "summary": decision.get("summary"),
            "tool_result": tool_result[:200] if tool_result else None,
        }
EOF

echo "    ✓ llm_task_executor.py dibuat"

# ─────────────────────────────────────────
# 2. Patch AutonomousLoop pakai LLMTaskExecutor
#    + tetap panggil scheduler lama
# ─────────────────────────────────────────
echo "[2/2] Patch autonomous_loop.py..."

cat > "$CORE/autonomous_loop.py" << 'EOF'
"""
AutonomousLoop — LLM-driven, bukan keyword parsing.
Scheduler lama tetap jalan untuk morning briefing & trading monitor.
"""
from sicuan.core.auto_scheduler import AutoScheduler
from sicuan.core.self_review_loop import SelfReviewLoop
from sicuan.core.knowledge_engine import KnowledgeEngine
from sicuan.core.llm_task_executor import LLMTaskExecutor


class AutonomousLoop:

    def run(self):

        # ── Step 1: Scheduler (morning briefing, trading monitor) ──
        scheduler = AutoScheduler()
        scheduler.run()

        # ── Step 2: Load knowledge context ──
        ke = KnowledgeEngine()
        knowledge = ke.load_all()

        # ── Step 3: LLM decide + execute (1 siklus) ──
        executor = LLMTaskExecutor()
        result = executor.run_cycle()

        # ── Step 4: Self review ──
        review = SelfReviewLoop()
        review_data = review.run()

        return {
            "executed": result,
            "review": review_data,
            "knowledge_focus": ke.summary().get("focus"),
        }
EOF

echo "    ✓ autonomous_loop.py diupdate"

# ─────────────────────────────────────────
# 3. Tambah job ke scheduler — panggil LLMTaskExecutor setiap 15 menit
# ─────────────────────────────────────────
echo "[3/3] Inject job ke scheduler.py..."

python3 << 'PYEOF'
from pathlib import Path

sched = Path("/home/dibs/agentjw/sicuan/scheduler.py")
text = sched.read_text()

NEW_JOB = '''
def run_autonomous_cycle():
    """LLM-driven autonomous cycle — jalankan setiap 15 menit."""
    try:
        import sys
        sys.path.insert(0, str(BASE.parent))
        from sicuan.core.llm_task_executor import LLMTaskExecutor
        executor = LLMTaskExecutor()
        result = executor.run_cycle()
        print(f"[autonomous] {result.get('summary', 'cycle done')}")
    except Exception as e:
        print(f"[autonomous] error: {e}")

'''

TARGET = "def run_scheduler():"
INJECT_JOB = """    # Autonomous LLM cycle setiap 15 menit
    schedule.every(15).minutes.do(run_autonomous_cycle)

    """

if "run_autonomous_cycle" in text:
    print("⚠ Job sudah ada, skip")
else:
    # Tambah function sebelum run_scheduler
    text = text.replace(TARGET, NEW_JOB + TARGET, 1)
    # Inject ke dalam run_scheduler setelah print pertama
    text = text.replace(
        '    print("SiCuan Scheduler started — fully autonomous mode")\n',
        '    print("SiCuan Scheduler started — fully autonomous mode")\n\n' + INJECT_JOB,
        1
    )
    sched.write_text(text)
    print("✓ Job autonomous cycle (15 menit) ditambahkan ke scheduler")
PYEOF

# ─────────────────────────────────────────
# 4. Syntax check
# ─────────────────────────────────────────
echo ""
echo "=== Syntax Check ==="
cd "$ROOT" && source venv/bin/activate

python3 << 'PYEOF'
import ast
from pathlib import Path

files = [
    "sicuan/core/llm_task_executor.py",
    "sicuan/core/autonomous_loop.py",
    "sicuan/scheduler.py",
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
# 5. Test 1 siklus
# ─────────────────────────────────────────
echo ""
echo "=== Test 1 Siklus LLM ==="
cd "$ROOT" && source venv/bin/activate

python3 << 'PYEOF'
import sys
sys.path.insert(0, "/home/dibs/agentjw")

from sicuan.core.llm_task_executor import LLMTaskExecutor
executor = LLMTaskExecutor()
result = executor.run_cycle()

print(f"  status   : {result.get('status')}")
print(f"  thinking : {result.get('thinking', '-')[:80]}...")
print(f"  action   : {result.get('action')}")
print(f"  summary  : {result.get('summary')}")
if result.get('tool_result'):
    print(f"  result   : {result.get('tool_result', '')[:100]}...")

if result.get('status') == 'completed':
    print("\n✅ LLM cycle OK!")
else:
    print(f"\n⚠ Status: {result.get('status')}")
PYEOF

echo ""
echo "======================================"
echo " Patch selesai!"
echo ""
echo " Flow baru (LLM-driven):"
echo "   AutoScheduler      ← morning briefing, trading monitor"
echo "       ↓"
echo "   KnowledgeEngine    ← 9 modul bisnis"  
echo "       ↓"
echo "   LLMTaskExecutor    ← LLM baca context → decide → execute tools"
echo "       ↓"
echo "   SelfReviewLoop"
echo ""
echo " Tidak ada keyword parsing."
echo " LLM yang decide aksi berdasarkan data nyata."
echo " Jalan setiap 15 menit via scheduler."
echo "======================================"
