#!/bin/bash
# ============================================================
# Patch brain.py — inject KnowledgeEngine ke SiCuan context
# Tidak ubah logic lama, hanya tambah knowledge ke prompt
# Jalankan: bash patch_brain_knowledge.sh
# ============================================================

set -e
ROOT="/home/dibs/agentjw"
BRAIN="$ROOT/sicuan/brain.py"
BACKUP="$ROOT/sicuan/brain.py.bak_knowledge_$(date +%H%M%S)"

echo "======================================"
echo " Patch brain.py — Business Brain"
echo "======================================"

# ── Backup dulu ──
cp "$BRAIN" "$BACKUP"
echo "✓ Backup: $BACKUP"

# ── Patch 1: Tambah import KnowledgeEngine setelah import logger ──
python3 << 'PYEOF'
from pathlib import Path

brain = Path("/home/dibs/agentjw/sicuan/brain.py")
text = brain.read_text()

OLD_IMPORT = "from core.logger import logger"
NEW_IMPORT = """from core.logger import logger

# Business Brain — inject knowledge ke context
import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    from sicuan.core.knowledge_engine import KnowledgeEngine as _KE
    _knowledge_engine = _KE()
except Exception:
    _knowledge_engine = None"""

if "KnowledgeEngine" in text:
    print("⚠ Import KnowledgeEngine sudah ada, skip patch 1")
else:
    text = text.replace(OLD_IMPORT, NEW_IMPORT, 1)
    print("✓ Patch 1: import KnowledgeEngine ditambahkan")

# ── Patch 2: Tambah method _build_knowledge_context di SiCuanBrain ──
OLD_FIND_PROJECT = "    def _find_project(self, target: str, projects: List[Dict]) -> Optional[Dict]:"
NEW_METHOD = '''    def _build_knowledge_context(self) -> str:
        """
        Ambil ringkasan business knowledge untuk inject ke prompt.
        Dipanggil setiap kali SiCuan mau reply — selalu fresh dari JSON.
        """
        if _knowledge_engine is None:
            return ""
        try:
            s = _knowledge_engine.summary()
            sop = _knowledge_engine.get_active_sop("daily_routine")
            branding = _knowledge_engine.load("branding")
            finance = _knowledge_engine.load("finance")

            lines = [
                "\\n=== BUSINESS CONTEXT (selalu update dari JSON) ===",
                f"Fokus saat ini   : {s.get('focus', '-')}",
                f"Vision           : {s.get('vision', '-')}",
                f"Target Q3 2026   : {list(s.get('quarterly_target', {}).values())[0] if s.get('quarterly_target') else '-'}",
                f"Belajar selanjut : {', '.join(s.get('learning_next', [])) or '-'}",
                f"Monthly OPEX     : ${s.get('monthly_opex_usd', 0)}/bln",
            ]

            if sop:
                lines.append("Daily SOP        : " + " → ".join(sop[:3]))

            tone = branding.get("tone", {})
            if tone:
                lines.append(f"Tone brand       : {tone.get('casual', '-')} (casual) / {tone.get('formal', '-')} (formal)")

            income = finance.get("income_streams", [])
            active = [i["source"] for i in income if i.get("status") == "development"]
            if active:
                lines.append(f"Income aktif     : {', '.join(active)}")

            lines.append("=================================================")
            return "\\n".join(lines)
        except Exception as e:
            return f"\\n[knowledge_context error: {e}]"

    def _find_project(self, target: str, projects: List[Dict]) -> Optional[Dict]:'''

if "_build_knowledge_context" in text:
    print("⚠ Method _build_knowledge_context sudah ada, skip patch 2")
else:
    text = text.replace(OLD_FIND_PROJECT, NEW_METHOD, 1)
    print("✓ Patch 2: _build_knowledge_context ditambahkan")

brain.write_text(text)
print("✓ brain.py disimpan")
PYEOF

# ── Patch 3: Inject _build_knowledge_context ke SICUAN_IDENTITY ──
# Kita cari method yang build system prompt dan inject di sana
python3 << 'PYEOF'
from pathlib import Path

brain = Path("/home/dibs/agentjw/sicuan/brain.py")
text = brain.read_text()

# Cari tempat SICUAN_IDENTITY dipakai dalam method (biasanya sebagai system prompt)
# Inject knowledge context tepat setelah SICUAN_IDENTITY digunakan

TARGET = 'system_prompt = SICUAN_IDENTITY'
REPLACEMENT = '''system_prompt = SICUAN_IDENTITY + self._build_knowledge_context()'''

if "self._build_knowledge_context()" in text:
    print("⚠ Inject ke system_prompt sudah ada, skip patch 3")
elif TARGET in text:
    text = text.replace(TARGET, REPLACEMENT, 1)
    brain.write_text(text)
    print("✓ Patch 3: knowledge context di-inject ke system_prompt")
else:
    # Fallback: cari variasi lain
    import re
    # Cari pattern: system=SICUAN_IDENTITY atau "system": SICUAN_IDENTITY
    pattern = r'(system\s*=\s*SICUAN_IDENTITY)([^+])'
    if re.search(pattern, text):
        text = re.sub(
            pattern,
            r'system = SICUAN_IDENTITY + self._build_knowledge_context()\2',
            text, count=1
        )
        brain.write_text(text)
        print("✓ Patch 3 (fallback): knowledge context di-inject ke system")
    else:
        print("⚠ Tidak ketemu pattern system_prompt — cek manual letak SICUAN_IDENTITY dipakai")
        print("  Tambahkan: + self._build_knowledge_context()")
        print("  Di baris yang pakai SICUAN_IDENTITY sebagai system prompt")
PYEOF

# ── Syntax check ──
echo ""
echo "=== Syntax Check ==="
cd "$ROOT" && source venv/bin/activate

python3 << 'PYEOF'
import ast
from pathlib import Path

f = Path("sicuan/brain.py")
try:
    ast.parse(f.read_text())
    print("  ✓ brain.py — syntax OK")
except SyntaxError as e:
    print(f"  ✗ brain.py — line {e.lineno}: {e.msg}")
    print("  → Restore dari backup jika perlu")
PYEOF

# ── Quick test: apakah knowledge engine bisa load ──
echo ""
echo "=== Test KnowledgeEngine ==="
python3 << 'PYEOF'
import sys
sys.path.insert(0, "/home/dibs/agentjw")

try:
    from sicuan.core.knowledge_engine import KnowledgeEngine
    ke = KnowledgeEngine()
    s = ke.summary()
    print(f"  ✓ summary() OK")
    print(f"    focus          : {s['focus']}")
    print(f"    monthly_opex   : ${s['monthly_opex_usd']}/bln")
    print(f"    learning_next  : {s['learning_next']}")

    all_k = ke.load_all()
    loaded = [k for k, v in all_k.items() if v]
    print(f"  ✓ load_all() — {len(loaded)} modul loaded: {', '.join(loaded)}")
except Exception as e:
    print(f"  ✗ Error: {e}")
PYEOF

echo ""
echo "======================================"
echo " Patch selesai!"
echo ""
echo " Sekarang setiap reply SiCuan akan"
echo " otomatis inject business context:"
echo ""
echo "   • Fokus project saat ini"
echo "   • Vision & quarterly target"
echo "   • Topic belajar berikutnya"
echo "   • Monthly OPEX budget"
echo "   • Daily SOP"
echo "   • Tone brand"
echo "   • Income stream aktif"
echo ""
echo " Backup tersimpan di:"
echo "   $BACKUP"
echo "======================================"
