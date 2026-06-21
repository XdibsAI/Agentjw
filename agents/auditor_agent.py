"""
agents/auditor_agent.py
Reality Check Agent — verifikasi independen sebelum SiCuan boleh klaim "sudah diperbaiki".

State machine:
  REQUESTED -> PATCHING -> PATCH_APPLIED -> VERIFYING -> VERIFIED | REJECTED
"""
import ast
import difflib
import json
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG = ROOT / "memory" / "audit_log.json"


class AuditorAgent:

    def snapshot(self, filepaths: list) -> dict:
        snap = {}
        for fp in filepaths:
            p = Path(fp)
            snap[str(p)] = p.read_text(errors="replace") if p.exists() else None
        return snap

    def _diff(self, before: str, after: str, filename: str) -> str:
        if before is None and after is None:
            return ""
        before_lines = (before or "").splitlines(keepends=True)
        after_lines = (after or "").splitlines(keepends=True)
        diff = difflib.unified_diff(
            before_lines, after_lines,
            fromfile=f"{filename} (before)",
            tofile=f"{filename} (after)",
            lineterm=""
        )
        return "".join(diff)

    def verify(self, user_request: str, before_snapshot: dict, repair_result: dict) -> dict:
        diffs = {}
        files_changed = []
        files_unchanged = []

        for filepath, before_content in before_snapshot.items():
            p = Path(filepath)
            after_content = p.read_text(errors="replace") if p.exists() else None

            if before_content == after_content:
                files_unchanged.append(filepath)
                continue

            d = self._diff(before_content, after_content, p.name)
            if d.strip():
                diffs[filepath] = d
                files_changed.append(filepath)

        if not files_changed:
            verdict = {
                "verdict": "NO_CHANGE",
                "diffs": {},
                "reasoning": (
                    "Tidak ada satupun file yang berubah secara aktual. "
                    "Klaim perbaikan tidak bisa diverifikasi karena tidak ada "
                    "perubahan source code yang terdeteksi."
                ),
                "files_changed": [],
                "files_unchanged": files_unchanged,
            }
            self._log(user_request, verdict)
            return verdict

        verdict = self._llm_verify_relevance(user_request, diffs, repair_result)

        # Deterministic safety net: cek apakah function BARU yang
        # ditambahkan benar-benar dipanggil dari mana pun di project.
        # LLM bisa terkelabui "nama function kedengaran relevan" --
        # ini tidak bisa, karena cuma menghitung occurrence call nyata.
        orphans = self._find_orphan_functions(before_snapshot, diffs)
        if orphans and verdict["verdict"] == "VERIFIED":
            original_reasoning = verdict.get("reasoning", "")
            verdict["verdict"] = "REJECTED"
            verdict["reasoning"] = (
                f"DOWNGRADE OTOMATIS dari VERIFIED ke REJECTED: function baru "
                f"{', '.join(orphans)} ditambahkan tapi TIDAK PERNAH dipanggil "
                f"dari mana pun di project (dead code). LLM auditor menilai diff "
                f"'relevan' secara permukaan, tapi tidak ada bukti integrasi nyata. "
                f"Reasoning asli LLM: {original_reasoning}"
            )

        verdict["files_changed"] = files_changed
        verdict["files_unchanged"] = files_unchanged
        verdict["orphan_functions"] = orphans
        self._log(user_request, verdict)
        return verdict

    def _extract_function_names(self, code: str) -> set:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return set()
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
        return names

    def _find_orphan_functions(self, before_snapshot: dict, diffs: dict) -> list:
        """
        Function BARU yang ditambahkan di diff, tapi TIDAK PERNAH dipanggil
        dari mana pun di seluruh project (cuma ada baris def-nya sendiri)
        dianggap dead code -- bukan integrasi nyata, walau LLM bilang relevan.
        """
        orphans = []
        all_after_content = {}
        for filepath in before_snapshot.keys():
            p = Path(filepath)
            all_after_content[filepath] = p.read_text(errors="replace") if p.exists() else ""

        combined_source = "\n".join(all_after_content.values())

        for filepath in diffs.keys():
            before_code = before_snapshot.get(filepath) or ""
            after_code = all_after_content.get(filepath, "")
            new_funcs = self._extract_function_names(after_code) - self._extract_function_names(before_code)

            for fn in new_funcs:
                total_paren = len(re.findall(r'\b' + re.escape(fn) + r'\s*\(', combined_source))
                def_count = len(re.findall(r'\bdef\s+' + re.escape(fn) + r'\s*\(', combined_source))
                call_count = total_paren - def_count
                if call_count <= 0:
                    orphans.append(fn)

        return orphans

    def _llm_verify_relevance(self, user_request: str, diffs: dict, repair_result: dict) -> dict:
        from core.llm_client import llm

        diff_text = "\n\n".join(
            f"=== {fp} ===\n{d[:2000]}" for fp, d in diffs.items()
        )

        prompt = f"""PERMINTAAN USER (asli):
{user_request}

REPAIR ENGINE STATUS (jangan terlalu percaya ini, ini cuma syntax-check):
{json.dumps(repair_result, ensure_ascii=False)[:500]}

DIFF AKTUAL YANG TERJADI DI SOURCE CODE:
{diff_text[:4000]}

Tugas kamu: audit independen. Apakah diff di atas BENAR-BENAR mengatasi
permintaan user? Jangan percaya status repair engine begitu saja — baca
diff-nya sendiri.

Kalau diff tidak relevan dengan request (misal user minta fix SELL logic
tapi diff cuma ubah formatting/comment), verdict harus REJECTED.

Jawab JSON:
{{"verdict": "VERIFIED atau REJECTED", "reasoning": "penjelasan singkat berbasis diff yang kamu baca, bukan asumsi"}}"""

        try:
            raw = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system=(
                    "Kamu adalah Auditor — agent skeptis yang TIDAK percaya "
                    "klaim sukses tanpa bukti diff nyata. Tugasmu mencegah "
                    "false positive 'sudah diperbaiki'."
                ),
                temperature=0.2,
                max_tokens=600,
                json_mode=True,
            )
            parsed = json.loads(raw)
            verdict = parsed.get("verdict", "REJECTED").upper()
            if verdict not in ("VERIFIED", "REJECTED"):
                verdict = "REJECTED"
            return {
                "verdict": verdict,
                "diffs": diffs,
                "reasoning": parsed.get("reasoning", ""),
            }
        except Exception as e:
            return {
                "verdict": "REJECTED",
                "diffs": diffs,
                "reasoning": f"Auditor gagal memverifikasi (error: {e}). "
                              f"Default ke REJECTED demi keamanan.",
            }

    def _log(self, user_request: str, verdict: dict):
        entries = []
        if AUDIT_LOG.exists():
            try:
                entries = json.loads(AUDIT_LOG.read_text())
            except Exception:
                entries = []

        entries.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "user_request": user_request,
            "verdict": verdict["verdict"],
            "reasoning": verdict.get("reasoning", ""),
            "files_changed": verdict.get("files_changed", []),
        })
        entries = entries[-100:]
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_LOG.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

    def format_response(self, verdict: dict) -> str:
        v = verdict["verdict"]

        if v == "NO_CHANGE":
            return (
                "⚠️ Repair TIDAK menghasilkan perubahan apapun di source code.\n"
                f"{verdict['reasoning']}\n"
                "Aku belum bisa klaim ini sudah diperbaiki."
            )

        if v == "REJECTED":
            diff_preview = "\n\n".join(
                f"📄 {fp}:\n```diff\n{d[:500]}\n```"
                for fp, d in list(verdict.get("diffs", {}).items())[:2]
            )
            return (
                "⚠️ Ada perubahan kode, TAPI auditor menilai ini belum benar-benar "
                f"menjawab permintaan kamu.\n\nAlasan: {verdict['reasoning']}\n\n"
                f"{diff_preview}\n\nMau aku lanjut perbaiki lagi?"
            )

        diff_preview = "\n\n".join(
            f"📄 {fp}:\n```diff\n{d[:800]}\n```"
            for fp, d in list(verdict.get("diffs", {}).items())[:3]
        )
        return (
            "✅ VERIFIED — perubahan kode terbukti sesuai permintaan.\n\n"
            f"{diff_preview}\n\nAlasan: {verdict['reasoning']}"
        )


auditor_agent = AuditorAgent()
