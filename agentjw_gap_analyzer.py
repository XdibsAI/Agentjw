#!/usr/bin/env python3
"""
agentjw_gap_analyzer.py — Diagnostic gap analyzer untuk AgentJW/SiCuan.
Read-only. Tidak mengubah file apapun.

Cek 5 kategori gap:
1. Action coverage (prompt LLM vs handler nyata)
2. Import graph (file orphan / dead code)
3. Endpoint reachability (api_server.py vs Flutter api_service.dart)
4. Runtime state (proses/cron vs modul yang ada di filesystem)
5. Env/config gap (key dipakai vs key terisi)

Usage: python3 agentjw_gap_analyzer.py
"""
import ast
import json
import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
REPORT_LINES = []


def section(title):
    REPORT_LINES.append(f"\n{'='*70}\n{title}\n{'='*70}")
    print(f"\n▶ {title}")


def log(msg, level="info"):
    icon = {"ok": "✅", "warn": "⚠️ ", "err": "❌", "info": "  "}.get(level, "  ")
    line = f"{icon} {msg}"
    REPORT_LINES.append(line)
    print(line)


# ───────────────────────────────────────────────────────────
# 1. ACTION COVERAGE CHECK
# ───────────────────────────────────────────────────────────
def check_action_coverage():
    section("1. ACTION COVERAGE — Prompt LLM vs Handler Nyata")

    brain_file = ROOT / "sicuan" / "brain.py"
    if not brain_file.exists():
        log("sicuan/brain.py tidak ditemukan", "err")
        return

    text = brain_file.read_text(errors="ignore")

    # Extract action list dari prompt: "action": "null | x | y | z"
    # PENTING: ambil match yang isinya benar-benar daftar action (mengandung "|"
    # dan kata "null"), bukan match pertama yang ditemukan — karena ada contoh
    # JSON lain di prompt (misal di instruksi planner) yang juga match pattern
    # "action": "..." tapi isinya cuma placeholder seperti "nama action".
    prompt_actions = set()
    for m in re.finditer(r'"action":\s*"([^"]+)"', text):
        raw = m.group(1)
        if "|" in raw and "null" in raw:
            prompt_actions = {a.strip() for a in raw.split("|") if a.strip() and a.strip() != "null"}
            break

    # Extract handler nyata: elif action == "xxx"
    handler_actions = set(re.findall(r'elif\s+action\s*==\s*"([^"]+)"', text))
    if_first = re.findall(r'if\s+action\s*==\s*"([^"]+)"', text)
    handler_actions.update(if_first)

    # CATATAN ARSITEKTUR: action juga bisa dipanggil lewat planner multi-step
    # ("plan": [{"action": ..., "action_target": ...}, ...] -> execute_plan()
    # -> execute_action()), bukan cuma field "action" tunggal di top-level
    # decision. Selama field tunggal "action" di schema tetap include semua
    # action yang ada handler-nya, planner TIDAK membuat handler jadi "dead" —
    # planner cuma jalur kedua untuk MEMANGGIL action yang sama.
    has_planner = '"plan":' in text and "execute_plan" in text
    if has_planner:
        log("Terdeteksi planner multi-step (\"plan\": [...] -> execute_plan()) — "
            "action juga bisa dipanggil lewat sini, bukan cuma field action tunggal.", "info")

    log(f"Action di prompt LLM: {len(prompt_actions)} -> {sorted(prompt_actions)}")
    log(f"Handler nyata di kode: {len(handler_actions)} -> {sorted(handler_actions)}")

    promised_not_handled = prompt_actions - handler_actions
    handled_not_promised = handler_actions - prompt_actions

    if promised_not_handled:
        log(f"ORPHAN PROMISE (LLM bisa pilih tapi TIDAK ADA handler): {sorted(promised_not_handled)}", "err")
    else:
        log("Semua action di prompt punya handler", "ok")

    if handled_not_promised:
        log(f"DEAD HANDLER (ada kode tapi LLM TIDAK PERNAH disuruh pilih): {sorted(handled_not_promised)}", "warn")
    else:
        log("Semua handler bisa dijangkau dari prompt", "ok")


# ───────────────────────────────────────────────────────────
# 2. IMPORT GRAPH CHECK
# ───────────────────────────────────────────────────────────
def check_import_graph():
    section("2. IMPORT GRAPH — File Orphan / Dead Code")

    SCAN_DIRS = ["sicuan", "agents", "core", "tools", "mcp", "memory", "runtime", "extensions", "swarm"]
    ENTRY_POINTS = ["sicuan/telegram_bot.py", "interface/cli.py", "api_server.py", "main.py"]

    all_py_files = {}
    for d in SCAN_DIRS:
        dpath = ROOT / d
        if not dpath.exists():
            continue
        for f in dpath.rglob("*.py"):
            if "__pycache__" in str(f) or f.suffix != ".py":
                continue
            if any(suf in f.name for suf in [".bak", ".backup", ".before_", ".pre_"]):
                continue
            rel = f.relative_to(ROOT)
            all_py_files[str(rel)] = f

    # Build module name -> file map (best effort, dotted path style)
    module_to_file = {}
    for rel, f in all_py_files.items():
        mod = rel.replace("/", ".").replace(".py", "")
        module_to_file[mod] = rel
        if f.name == "__init__.py":
            pkg = str(Path(rel).parent).replace("/", ".")
            module_to_file[pkg] = rel

    # Collect all import statements across the whole codebase
    imported_modules = set()
    for rel, f in all_py_files.items():
        try:
            tree = ast.parse(f.read_text(errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)
                    # also add submodule combos
                    for alias in node.names:
                        imported_modules.add(f"{node.module}.{alias.name}")

    orphans = []
    for rel, f in all_py_files.items():
        mod = rel.replace("/", ".").replace(".py", "")
        if rel in ENTRY_POINTS:
            continue
        is_imported = any(
            mod == im or im.startswith(mod + ".") or mod.startswith(im + ".") or im.endswith("." + mod.split(".")[-1])
            for im in imported_modules
        )
        if not is_imported:
            orphans.append(rel)

    log(f"Total file Python discan: {len(all_py_files)}")
    if orphans:
        log(f"Kemungkinan ORPHAN FILES ({len(orphans)}) — tidak terdeteksi diimport siapapun:", "warn")
        for o in sorted(orphans)[:40]:
            REPORT_LINES.append(f"     - {o}")
            print(f"     - {o}")
        if len(orphans) > 40:
            log(f"... dan {len(orphans)-40} lainnya (lihat report file)", "warn")
    else:
        log("Tidak ada file orphan terdeteksi", "ok")

    log("Catatan: deteksi ini heuristik (string-match modul), false positive mungkin terjadi untuk dynamic import.", "info")


# ───────────────────────────────────────────────────────────
# 3. ENDPOINT REACHABILITY CHECK
# ───────────────────────────────────────────────────────────
def check_endpoint_reachability():
    section("3. ENDPOINT REACHABILITY — Backend vs Flutter")

    api_file = ROOT / "api_server.py"
    if not api_file.exists():
        log("api_server.py tidak ditemukan", "err")
        return

    text = api_file.read_text(errors="ignore")
    backend_endpoints = set(re.findall(r'@app\.(?:get|post|put|delete)\(\s*["\']([^"\']+)["\']', text))
    log(f"Backend endpoints terdaftar: {len(backend_endpoints)}")

    # Cari Flutter project — coba beberapa lokasi umum
    flutter_candidates = [
        ROOT.parent / "agentjw_remote",
        ROOT / "agentjw_remote",
    ]
    flutter_dir = next((d for d in flutter_candidates if d.exists()), None)

    if not flutter_dir:
        log("Flutter project tidak ditemukan di lokasi umum, skip cross-check", "warn")
        for ep in sorted(backend_endpoints):
            REPORT_LINES.append(f"     - {ep}")
        return

    dart_files = list(flutter_dir.rglob("*.dart"))
    dart_text = "\n".join(f.read_text(errors="ignore") for f in dart_files)

    called_endpoints = set()
    for ep in backend_endpoints:
        # Normalize path param style {id} -> regex agar match pemanggilan dinamis
        pattern = re.escape(ep)
        pattern = re.sub(r"\\\{[^}]+\\\}", r"[^/\"'\\s]+", pattern)
        if re.search(pattern, dart_text):
            called_endpoints.add(ep)

    unused_by_apk = backend_endpoints - called_endpoints
    log(f"Endpoint dipanggil dari APK: {len(called_endpoints)}")
    if unused_by_apk:
        log(f"Endpoint TIDAK dipanggil APK manapun ({len(unused_by_apk)}):", "warn")
        for ep in sorted(unused_by_apk):
            REPORT_LINES.append(f"     - {ep}")
            print(f"     - {ep}")
    else:
        log("Semua endpoint backend dipakai APK", "ok")


# ───────────────────────────────────────────────────────────
# 4. RUNTIME STATE CHECK
# ───────────────────────────────────────────────────────────
def check_runtime_state():
    section("4. RUNTIME STATE — Proses Aktif vs Modul Tersedia")

    try:
        ps_out = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=10).stdout
    except Exception as e:
        log(f"Gagal jalankan ps aux: {e}", "err")
        return

    candidates = {
        "telegram_bot": "sicuan/telegram_bot.py",
        "api_server": "api_server.py",
        "autonomous_loop": "sicuan/core/autonomous_loop.py",
        "scheduler": "sicuan/scheduler.py",
        "godmeme main.py": "projects/godmeme_bot/main.py",
    }

    for label, filepath in candidates.items():
        running = filepath.split("/")[-1] in ps_out or label in ps_out
        f_exists = (ROOT / filepath).exists()
        if f_exists and running:
            log(f"{label}: file ADA, proses JALAN", "ok")
        elif f_exists and not running:
            log(f"{label}: file ADA, proses TIDAK JALAN", "warn")
        elif not f_exists:
            log(f"{label}: file tidak ditemukan ({filepath})", "info")

    try:
        cron_out = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=10).stdout
        log("Crontab aktif:")
        for line in cron_out.strip().splitlines():
            if line.strip() and not line.startswith("#"):
                REPORT_LINES.append(f"     - {line}")
                print(f"     - {line}")
    except Exception:
        log("Tidak bisa baca crontab", "warn")


# ───────────────────────────────────────────────────────────
# 5. ENV / CONFIG GAP CHECK
# ───────────────────────────────────────────────────────────
def check_env_gap():
    section("5. ENV/CONFIG GAP — Key Dipakai vs Key Terisi")

    # Scan root .env DAN semua .env di tiap project aktif (skip backups/trash)
    env_files = [ROOT / ".env"]
    projects_dir = ROOT / "projects"
    if projects_dir.exists():
        env_files.extend(projects_dir.glob("*/.env"))

    filled_keys = {}
    for env_file in env_files:
        if not env_file.exists():
            continue
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                k = k.strip()
                v = v.strip()
                # Kalau key sudah ada dari .env lain dan terisi, jangan ditimpa kosong
                if k not in filled_keys or (v and v not in ("your_key_here", "PASTE_YOUR_KEY_HERE")):
                    filled_keys[k] = v

    log(f"Scan {len(env_files)} file .env: {[str(f.relative_to(ROOT)) for f in env_files if f.exists()]}")

    used_keys = set()
    for f in ROOT.rglob("*.py"):
        if "__pycache__" in str(f) or "venv" in str(f):
            continue
        try:
            text = f.read_text(errors="ignore")
        except Exception:
            continue
        used_keys.update(re.findall(r'os\.getenv\(\s*["\']([A-Z_]+)["\']', text))
        used_keys.update(re.findall(r'os\.environ\[\s*["\']([A-Z_]+)["\']\s*\]', text))
        used_keys.update(re.findall(r'os\.environ\.get\(\s*["\']([A-Z_]+)["\']', text))

    log(f"Keys dipakai di kode: {len(used_keys)}")
    log(f"Keys ada di .env: {len(filled_keys)}")

    empty_or_missing = []
    for k in sorted(used_keys):
        val = filled_keys.get(k)
        if val is None:
            empty_or_missing.append((k, "TIDAK ADA di .env"))
        elif val == "" or val in ("your_key_here", "PASTE_YOUR_KEY_HERE"):
            empty_or_missing.append((k, "KOSONG/placeholder"))

    if empty_or_missing:
        log(f"Keys bermasalah ({len(empty_or_missing)}):", "warn")
        for k, reason in empty_or_missing:
            REPORT_LINES.append(f"     - {k}: {reason}")
            print(f"     - {k}: {reason}")
    else:
        log("Semua key yang dipakai kode sudah terisi", "ok")


# ───────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────


# ───────────────────────────────────────────────────────────
# 6. PROMPT CONSISTENCY CHECK
# ───────────────────────────────────────────────────────────
def check_prompt_consistency():
    section("6. PROMPT CONSISTENCY — Instruksi Brain.py")

    brain_file = ROOT / "sicuan" / "brain.py"
    if not brain_file.exists():
        log("brain.py tidak ditemukan", "err")
        return

    text = brain_file.read_text(errors="ignore")

    # Cari semua blok instruksi besar "PENTING SOAL ..."
    blocks = re.findall(r'PENTING SOAL ([A-Z\s/]+):', text)
    log(f"Blok instruksi 'PENTING SOAL' ditemukan: {len(blocks)} -> {blocks}")

    # Cek tiap action yang disebut di multiple blok (potensi konflik instruksi)
    action_mentions = {}
    for action in re.findall(r'"?action"?\s*[=:]\s*"([a-z_]+)"', text):
        action_mentions[action] = action_mentions.get(action, 0) + 1

    heavily_mentioned = {a: c for a, c in action_mentions.items() if c >= 4}
    if heavily_mentioned:
        log(f"Action yang disebut berkali-kali (cek manual potensi instruksi tumpang tindih): {heavily_mentioned}", "warn")

    # Cek action yang butuh action_target tapi tidak dijelaskan formatnya
    prompt_actions = set()
    m = re.search(r'"action":\s*"([^"]+)"', text)
    if m:
        prompt_actions = {a.strip() for a in m.group(1).split("|") if a.strip() and a.strip() != "null"}

    target_dependent_keywords = ["target", "action_target"]
    actions_without_format_hint = []
    for action in prompt_actions:
        # Cari apakah ada penjelasan format action_target untuk action ini di sekitar definisinya
        pattern = re.escape(action) + r'.{0,400}?action_target'
        if not re.search(pattern, text, re.DOTALL) and action not in ("null",):
            actions_without_format_hint.append(action)

    if actions_without_format_hint:
        log(f"Action TANPA penjelasan format action_target eksplisit: {sorted(actions_without_format_hint)}", "warn")
    else:
        log("Semua action punya penjelasan action_target", "ok")


# ───────────────────────────────────────────────────────────
# 7. AUDITOR COVERAGE CHECK
# ───────────────────────────────────────────────────────────
def check_auditor_coverage():
    section("7. AUDITOR COVERAGE — Risiko Klaim Palsu")

    brain_file = ROOT / "sicuan" / "brain.py"
    if not brain_file.exists():
        log("brain.py tidak ditemukan", "err")
        return

    text = brain_file.read_text(errors="ignore")

    # Split per action handler block
    handler_blocks = re.split(r'(elif action == "[a-z_]+":)', text)

    claim_keywords = ["selesai", "berhasil", "diperbaiki", "sukses", "success", "done", "fixed"]

    risky_actions = []
    safe_actions = []

    for i in range(1, len(handler_blocks), 2):
        header = handler_blocks[i]
        body = handler_blocks[i+1] if i+1 < len(handler_blocks) else ""
        action_name = re.search(r'"([a-z_]+)"', header).group(1)

        # Ambil body sampai elif/def berikutnya saja (heuristik: 2000 char pertama)
        body_snippet = body[:2000]

        has_claim = any(kw in body_snippet.lower() for kw in claim_keywords)
        has_auditor = "auditor_agent" in body_snippet

        if has_claim and not has_auditor:
            risky_actions.append(action_name)
        elif has_claim and has_auditor:
            safe_actions.append(action_name)

    if risky_actions:
        log(f"UNVERIFIED CLAIM RISK — action ini klaim sukses TANPA lewat auditor: {sorted(set(risky_actions))}", "err")
    else:
        log("Tidak ada action yang klaim sukses tanpa auditor", "ok")

    if safe_actions:
        log(f"Action yang SUDAH pakai auditor sebelum klaim: {sorted(set(safe_actions))}", "ok")


# ───────────────────────────────────────────────────────────
# 8. KNOWLEDGE FILE USAGE CHECK
# ───────────────────────────────────────────────────────────
def check_knowledge_usage():
    section("8. KNOWLEDGE FILE USAGE — File Pengetahuan SiCuan")

    knowledge_dir = ROOT / "sicuan" / "knowledge"
    if not knowledge_dir.exists():
        log("sicuan/knowledge/ tidak ditemukan", "warn")
        return

    knowledge_files = list(knowledge_dir.glob("*.json"))
    log(f"File knowledge ditemukan: {len(knowledge_files)} -> {[f.name for f in knowledge_files]}")

    # Scan semua .py di sicuan/ untuk referensi ke file ini
    all_sicuan_code = ""
    for f in (ROOT / "sicuan").rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        try:
            all_sicuan_code += f.read_text(errors="ignore")
        except Exception:
            continue

    orphan_knowledge = []
    used_knowledge = []
    for kf in knowledge_files:
        stem = kf.stem  # contoh: "branding" dari "branding.json"
        if stem in all_sicuan_code or kf.name in all_sicuan_code:
            used_knowledge.append(kf.name)
        else:
            orphan_knowledge.append(kf.name)

    if orphan_knowledge:
        log(f"ORPHAN KNOWLEDGE (file ada, TIDAK PERNAH dibaca kode manapun): {orphan_knowledge}", "warn")
    else:
        log("Semua knowledge file terhubung ke kode", "ok")

    if used_knowledge:
        log(f"Knowledge yang terhubung: {used_knowledge}", "ok")


# ───────────────────────────────────────────────────────────
# 9. DEPARTMENT MODULE CHECK
# ───────────────────────────────────────────────────────────
def check_department_modules():
    section("9. DEPARTMENT MODULES — Strategi/Curriculum/SOP/Branding/Finance/HR")

    dept_base = ROOT / "sicuan" / "core" / "department_base.py"
    if not dept_base.exists():
        log("department_base.py belum ada — 6 modul departemen belum dibangun", "warn")
        return

    log("department_base.py ditemukan", "ok")

    core_dir = ROOT / "sicuan" / "core"
    dept_files = [f for f in core_dir.glob("*.py") if f.name != "department_base.py"]

    # Cari subclass DepartmentBase
    department_subclasses = []
    for f in dept_files:
        try:
            text = f.read_text(errors="ignore")
            if "DepartmentBase" in text and "class" in text:
                cls_match = re.search(r'class\s+(\w+)\s*\(\s*DepartmentBase', text)
                if cls_match:
                    department_subclasses.append((f.name, cls_match.group(1)))
        except Exception:
            continue

    log(f"Department subclass ditemukan: {len(department_subclasses)} -> {department_subclasses}")

    expected = ["strategy", "curriculum", "sop", "branding", "finance", "hr"]
    found_keywords = [name.lower() for _, name in department_subclasses]
    missing = [e for e in expected if not any(e in fk for fk in found_keywords)]

    if missing:
        log(f"Departemen BELUM dibuat: {missing}", "warn")

    # Cek apakah dipanggil dari brain.py
    brain_text = (ROOT / "sicuan" / "brain.py").read_text(errors="ignore")
    for fname, clsname in department_subclasses:
        if clsname in brain_text or fname.replace(".py", "") in brain_text:
            log(f"{clsname} ({fname}): terhubung ke brain.py", "ok")
        else:
            log(f"{clsname} ({fname}): ORPHAN — tidak dipanggil dari brain.py", "warn")


# ───────────────────────────────────────────────────────────
# 10. AUDIT LOG TRACK RECORD
# ───────────────────────────────────────────────────────────
def check_audit_track_record():
    section("10. AUDIT LOG TRACK RECORD — Histori Verifikasi SiCuan")

    audit_log = ROOT / "memory" / "audit_log.json"
    if not audit_log.exists():
        log("audit_log.json belum ada — auditor belum pernah dipanggil", "warn")
        return

    try:
        entries = json.loads(audit_log.read_text())
    except Exception as e:
        log(f"Gagal baca audit_log.json: {e}", "err")
        return

    if not entries:
        log("audit_log.json kosong", "warn")
        return

    verdicts = {}
    for e in entries:
        v = e.get("verdict", "UNKNOWN")
        verdicts[v] = verdicts.get(v, 0) + 1

    log(f"Total audit tercatat: {len(entries)}")
    log(f"Breakdown verdict: {verdicts}")

    verified = verdicts.get("VERIFIED", 0)
    total = len(entries)
    if total > 0:
        rate = (verified / total) * 100
        level = "ok" if rate >= 50 else "warn"
        log(f"Success rate (VERIFIED/total): {rate:.1f}%", level)

    log("5 entry terakhir:")
    for e in entries[-5:]:
        ts = e.get("timestamp", "?")
        v = e.get("verdict", "?")
        req = e.get("user_request", "")[:60]
        REPORT_LINES.append(f"     [{ts}] {v} — \"{req}\"")
        print(f"     [{ts}] {v} — \"{req}\"")


def main():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    REPORT_LINES.append(f"AGENTJW GAP ANALYZER REPORT — {ts}")
    print(f"AGENTJW GAP ANALYZER — {ts}")

    check_action_coverage()
    check_import_graph()
    check_endpoint_reachability()
    check_runtime_state()
    check_env_gap()
    check_prompt_consistency()
    check_auditor_coverage()
    check_knowledge_usage()
    check_department_modules()
    check_audit_track_record()

    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    report_path = log_dir / f"gap_report_{ts}.md"
    report_path.write_text("\n".join(REPORT_LINES))

    print(f"\n{'='*70}")
    print(f"✅ Report tersimpan: {report_path}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
