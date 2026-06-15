#!/bin/bash
# agentjw_diagnose_fix.sh — Diagnosa & fix crash uvicorn + telegram bot
# Jalankan: cd ~/agentjw && bash agentjw_diagnose_fix.sh

set -e
cd ~/agentjw
source venv/bin/activate 2>/dev/null || true

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}✅ $1${RESET}"; }
err()  { echo -e "  ${RED}❌ $1${RESET}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${RESET}"; }
info() { echo -e "  ${CYAN}ℹ  $1${RESET}"; }
h()    { echo -e "\n${BOLD}${CYAN}══════════════════════════════════════════${RESET}"; \
         echo -e "${BOLD}  $1${RESET}"; \
         echo -e "${BOLD}${CYAN}══════════════════════════════════════════${RESET}"; }

# ════════════════════════════════════════════════════════════════════
# STEP 1: Baca semua log error
# ════════════════════════════════════════════════════════════════════
h "STEP 1: Diagnosa Error Log"

echo ""
echo "=== api_server.log (tail 30) ==="
tail -30 logs/api_server.log 2>/dev/null || echo "(kosong)"

echo ""
echo "=== sicuan_telegram.log (tail 30) ==="
tail -30 logs/sicuan_telegram.log 2>/dev/null || echo "(kosong)"

# ════════════════════════════════════════════════════════════════════
# STEP 2: Cek import api_server.py
# ════════════════════════════════════════════════════════════════════
h "STEP 2: Cek Import api_server.py"

python3 - << 'PYEOF'
import sys, traceback
sys.path.insert(0, '/home/dibs/agentjw')
try:
    # Cek syntax dulu
    import ast
    src = open('api_server.py').read()
    ast.parse(src)
    print("  ✅ api_server.py syntax OK")
except SyntaxError as e:
    print(f"  ❌ SYNTAX ERROR: {e}")
    sys.exit(1)

# Cek import satu per satu
modules = [
    'fastapi', 'uvicorn', 'dotenv', 'pydantic',
    'core.config', 'core.llm_client',
    'agents.orchestrator', 'agents.brain',
    'memory.memory_store',
]
for mod in modules:
    try:
        __import__(mod)
        print(f"  ✅ import {mod}")
    except ImportError as e:
        print(f"  ❌ MISSING: {mod} — {e}")
    except Exception as e:
        print(f"  ⚠️  ERROR {mod}: {type(e).__name__}: {e}")
PYEOF

# ════════════════════════════════════════════════════════════════════
# STEP 3: Cek import telegram bot
# ════════════════════════════════════════════════════════════════════
h "STEP 3: Cek Import Telegram Bot"

python3 - << 'PYEOF'
import sys, traceback
sys.path.insert(0, '/home/dibs/agentjw')
try:
    import ast
    src = open('sicuan/telegram_bot.py').read()
    ast.parse(src)
    print("  ✅ telegram_bot.py syntax OK")
except SyntaxError as e:
    print(f"  ❌ SYNTAX ERROR line {e.lineno}: {e.msg}")
    sys.exit(1)
except FileNotFoundError:
    print("  ❌ sicuan/telegram_bot.py tidak ditemukan")
    sys.exit(1)

mods = [
    'telegram', 'telegram.ext',
    'sicuan.chat', 'sicuan.memory_engine',
]
for mod in mods:
    try:
        __import__(mod)
        print(f"  ✅ import {mod}")
    except ImportError as e:
        print(f"  ❌ MISSING: {mod} — {e}")
    except Exception as e:
        print(f"  ⚠️  {mod}: {type(e).__name__}: {str(e)[:100]}")
PYEOF

# ════════════════════════════════════════════════════════════════════
# STEP 4: Cek sicuan/chat.py & memory_engine.py
# ════════════════════════════════════════════════════════════════════
h "STEP 4: Cek SiCuan Module Structure"

for f in \
    sicuan/__init__.py \
    sicuan/chat.py \
    sicuan/memory_engine.py \
    sicuan/telegram_bot.py \
    sicuan/consolidator.py; do
    if [ -f "$f" ]; then
        ok "$f ($(wc -l < $f) baris)"
    else
        err "$f TIDAK ADA"
    fi
done

# Cek class SiCuanChat ada di chat.py
if [ -f "sicuan/chat.py" ]; then
    grep -n "class SiCuanChat\|def chat" sicuan/chat.py | head -5 || true
fi

# ════════════════════════════════════════════════════════════════════
# STEP 5: Cek apakah sicuan/chat.py punya method yang dibutuhkan bot
# ════════════════════════════════════════════════════════════════════
h "STEP 5: Validasi SiCuanChat"

python3 - << 'PYEOF'
import sys
sys.path.insert(0, '/home/dibs/agentjw')
try:
    from sicuan.chat import SiCuanChat
    c = SiCuanChat()
    # Cek method
    for m in ['chat', 'session_id', 'history']:
        if hasattr(c, m):
            print(f"  ✅ SiCuanChat.{m} ada")
        else:
            print(f"  ❌ SiCuanChat.{m} TIDAK ADA")
except Exception as e:
    print(f"  ❌ SiCuanChat error: {e}")
    import traceback; traceback.print_exc()
PYEOF

# ════════════════════════════════════════════════════════════════════
# STEP 6: Cek memory_engine
# ════════════════════════════════════════════════════════════════════
h "STEP 6: Validasi Memory Engine"

python3 - << 'PYEOF'
import sys
sys.path.insert(0, '/home/dibs/agentjw')
try:
    from sicuan.memory_engine import memory_engine
    for m in ['save_insight', 'recall_insights', 'summarize_period']:
        if hasattr(memory_engine, m):
            print(f"  ✅ memory_engine.{m} ada")
        else:
            print(f"  ❌ memory_engine.{m} TIDAK ADA — perlu dibuat")
except Exception as e:
    print(f"  ❌ memory_engine error: {e}")
PYEOF

# ════════════════════════════════════════════════════════════════════
# STEP 7: Cek port & proses yang berjalan
# ════════════════════════════════════════════════════════════════════
h "STEP 7: Port & Process Status"

echo "  Proses yang berjalan:"
ps aux | grep -E "uvicorn|api_server|telegram|sicuan|python3" | grep -v grep || echo "  (tidak ada)"

echo ""
echo "  Port yang listen:"
ss -tlnp 2>/dev/null | grep -E "18790|8080|8000" || netstat -tlnp 2>/dev/null | grep -E "18790|8080|8000" || echo "  (tidak ada port aktif)"

echo ""
echo "  .env PORT config:"
grep -E "API_PORT|PORT=" .env | head -5

# ════════════════════════════════════════════════════════════════════
# STEP 8: Fix — install missing packages
# ════════════════════════════════════════════════════════════════════
h "STEP 8: Auto-Fix Missing Packages"

pip install \
    "python-telegram-bot>=20.0" \
    schedule \
    aiofiles \
    python-multipart \
    --quiet 2>&1 | tail -3

ok "Packages installed"

# ════════════════════════════════════════════════════════════════════
# STEP 9: Fix sicuan/memory_engine.py jika method hilang
# ════════════════════════════════════════════════════════════════════
h "STEP 9: Fix Memory Engine (jika perlu)"

python3 - << 'PYEOF'
import sys
sys.path.insert(0, '/home/dibs/agentjw')

# Cek apakah memory_engine sudah punya semua method
needs_fix = False
try:
    from sicuan.memory_engine import memory_engine
    for m in ['save_insight', 'recall_insights', 'summarize_period']:
        if not hasattr(memory_engine, m):
            needs_fix = True
            print(f"  ⚠️  Missing method: {m}")
except:
    needs_fix = True
    print("  ⚠️  memory_engine tidak bisa diimport")

if needs_fix:
    print("  🔧 Menulis ulang memory_engine.py...")
    from pathlib import Path
    Path('sicuan/memory_engine.py').write_text('''"""
sicuan/memory_engine.py — SiCuan Memory Engine
Simpan, recall, dan konsolidasikan memory SiCuan
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("/home/dibs/agentjw/memory/agentjw.db")


class MemoryEngine:
    def __init__(self):
        self.db = DB_PATH
        self._ensure_table()

    def _conn(self):
        conn = sqlite3.connect(self.db)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        try:
            conn = self._conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    created_at TEXT DEFAULT (datetime('now','localtime')),
                    updated_at TEXT DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[MemoryEngine] DB error: {e}")

    def save_insight(self, topic: str, content: str, importance: float = 0.7):
        """Simpan insight baru atau update yang sudah ada"""
        try:
            conn = self._conn()
            existing = conn.execute(
                "SELECT id FROM memories WHERE topic=?", (topic,)
            ).fetchone()

            if existing:
                conn.execute(
                    "UPDATE memories SET content=?, importance=?, updated_at=? WHERE topic=?",
                    (content, importance, datetime.now().isoformat(), topic)
                )
            else:
                conn.execute(
                    "INSERT INTO memories (topic, content, importance) VALUES (?,?,?)",
                    (topic, content, importance)
                )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[MemoryEngine] save_insight error: {e}")
            return False

    def recall_insights(self, topic: str = None, limit: int = 10,
                        min_importance: float = 0.5):
        """Recall insights dari memory"""
        try:
            conn = self._conn()
            if topic:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE topic LIKE ? AND importance >= ? "
                    "ORDER BY importance DESC, updated_at DESC LIMIT ?",
                    (f"%{topic}%", min_importance, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE importance >= ? "
                    "ORDER BY importance DESC, updated_at DESC LIMIT ?",
                    (min_importance, limit)
                ).fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[MemoryEngine] recall error: {e}")
            return []

    def summarize_period(self, days: int = 7) -> str:
        """Rangkum memory dan aktivitas N hari terakhir"""
        try:
            conn = self._conn()
            since = (datetime.now() - timedelta(days=days)).isoformat()

            memories = conn.execute(
                "SELECT topic, content, importance FROM memories "
                "WHERE updated_at >= ? ORDER BY importance DESC LIMIT 20",
                (since,)
            ).fetchall()

            # Coba ambil work log jika ada
            worklogs = []
            try:
                worklogs = conn.execute(
                    "SELECT project_name, action FROM work_log "
                    "WHERE timestamp >= ? LIMIT 10", (since,)
                ).fetchall()
            except:
                pass

            conn.close()

            lines = [f"📊 SiCuan Summary — {days} hari terakhir\n"]
            if memories:
                lines.append("🧠 Memory penting:")
                for m in memories:
                    lines.append(f"  [{m['topic']}] {m['content'][:100]}")
            if worklogs:
                lines.append("\\n📁 Pekerjaan:")
                for w in worklogs:
                    lines.append(f"  {w['project_name']}: {w['action']}")
            if not memories and not worklogs:
                lines.append("Belum ada data.")

            return "\\n".join(lines)
        except Exception as e:
            return f"Error summarize: {e}"

    def get_context_for_llm(self, topic: str = None, limit: int = 5) -> str:
        """Format memory sebagai context untuk LLM"""
        insights = self.recall_insights(topic=topic, limit=limit)
        if not insights:
            return ""
        lines = ["[Memory SiCuan yang relevan:]"]
        for ins in insights:
            lines.append(f"- {ins[\'topic\']}: {ins[\'content\'][:150]}")
        return "\\n".join(lines)


memory_engine = MemoryEngine()
''', encoding='utf-8')
    print("  ✅ memory_engine.py ditulis ulang")
else:
    print("  ✅ memory_engine.py sudah OK")
PYEOF

# ════════════════════════════════════════════════════════════════════
# STEP 10: Fix api_server.py jika ada import error
# ════════════════════════════════════════════════════════════════════
h "STEP 10: Fix & Restart api_server"

# Jalankan api_server dalam foreground singkat untuk capture error
info "Testing api_server.py startup..."
timeout 5 python3 -m uvicorn api_server:app \
    --host 0.0.0.0 --port 18790 \
    --log-level debug 2>&1 | head -30 || true

# Cek apakah sekarang sudah bisa start
sleep 1
pkill -f "api_server" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
sleep 1

info "Starting api_server di background..."
nohup python3 -m uvicorn api_server:app \
    --host 0.0.0.0 --port 18790 \
    --log-level warning \
    > logs/api_server.log 2>&1 &
API_PID=$!
echo $API_PID > logs/api_server.pid
info "PID: $API_PID"
sleep 3

# Test
CODE=$(curl -s -o /tmp/agentjw_resp.json -w "%{http_code}" \
    --max-time 8 http://localhost:18790/api/status 2>/dev/null)
if [ "$CODE" = "200" ]; then
    ok "api_server UP — port 18790"
    cat /tmp/agentjw_resp.json | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(f'    model: {d.get(\"model\",\"?\")}')
    print(f'    status: {d.get(\"status\",\"?\")}')
except: pass"
else
    err "api_server MASIH CRASH (HTTP: $CODE)"
    echo ""
    echo "=== Error log ==="
    tail -20 logs/api_server.log
fi

# ════════════════════════════════════════════════════════════════════
# STEP 11: Fix & Restart Telegram Bot
# ════════════════════════════════════════════════════════════════════
h "STEP 11: Fix & Restart Telegram Bot"

# Cek token
TG_TOKEN=$(grep "TELEGRAM_BOT_TOKEN" .env | cut -d= -f2 | tr -d '"' | tr -d "'")
if [ -z "$TG_TOKEN" ] || [ "$TG_TOKEN" = "your_bot_token" ]; then
    err "TELEGRAM_BOT_TOKEN kosong di .env"
    warn "Set: echo 'TELEGRAM_BOT_TOKEN=xxxx:yyy' >> .env"
    SKIP_BOT=true
else
    ok "TELEGRAM_BOT_TOKEN ada"
    SKIP_BOT=false
fi

# Test import telegram_bot tanpa run
if python3 - << 'PYEOF' 2>&1; then
import sys, ast
sys.path.insert(0, '/home/dibs/agentjw')

# Parse
src = open('sicuan/telegram_bot.py').read()
ast.parse(src)
print("  ✅ telegram_bot.py parse OK")

# Test import tanpa run_bot
import importlib.util
spec = importlib.util.spec_from_file_location("tgbot", "sicuan/telegram_bot.py")
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
    print("  ✅ telegram_bot.py import OK")
except SystemExit:
    pass
except Exception as e:
    print(f"  ❌ Import error: {e}")
    raise
PYEOF
    ok "telegram_bot.py siap"
else
    warn "Ada error di telegram_bot.py — cek output di atas"
fi

if [ "$SKIP_BOT" = "false" ]; then
    pkill -f "telegram_bot" 2>/dev/null || true
    sleep 1
    nohup python3 -c "
import sys
sys.path.insert(0, '/home/dibs/agentjw')
from sicuan.telegram_bot import run_bot
run_bot()
" > logs/sicuan_telegram.log 2>&1 &
    TG_PID=$!
    echo $TG_PID > logs/telegram_bot.pid
    sleep 3

    if kill -0 $TG_PID 2>/dev/null; then
        ok "Telegram bot running (PID: $TG_PID)"
        tail -5 logs/sicuan_telegram.log
    else
        err "Telegram bot crash — log:"
        tail -15 logs/sicuan_telegram.log
    fi
fi

# ════════════════════════════════════════════════════════════════════
# STEP 12: Test API agent endpoint
# ════════════════════════════════════════════════════════════════════
h "STEP 12: Test API Chat"

if [ "$CODE" = "200" ]; then
    info "Testing /api/agent..."
    RESP=$(curl -s --max-time 30 \
        -X POST http://localhost:18790/api/agent \
        -H "Content-Type: application/json" \
        -d '{"message":"halo cuan, kamu bisa apa aja?","session_id":"test_fix","history":[],"mode":"chat"}')

    if echo "$RESP" | python3 -c "
import sys,json
d=json.loads(sys.stdin.read())
r=d.get('response','')
print(f'  Response ({len(r)} chars):')
print(f'  {r[:300]}')
" 2>/dev/null; then
        ok "Chat API berfungsi!"
    else
        err "Chat API gagal"
        echo "  Raw: ${RESP:0:200}"
    fi
fi

# ════════════════════════════════════════════════════════════════════
# SUMMARY
# ════════════════════════════════════════════════════════════════════
h "SUMMARY"

echo ""
echo "  Status proses:"
ps aux | grep -E "uvicorn|telegram_bot|api_server|sicuan" | grep -v grep | \
    awk '{print "  ✅ " $11 " " $12 " (PID: " $2 ")"}' || echo "  (tidak ada)"

echo ""
echo "  Test manual:"
echo "  curl http://localhost:18790/api/status"
echo ""
echo "  Lihat log:"
echo "  tail -f logs/api_server.log"
echo "  tail -f logs/sicuan_telegram.log"
echo ""
