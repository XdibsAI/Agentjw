"""
agents/specialist/logic_modifier.py
Targeted logic fix — beda dari repair_specialist (yang cuma syntax-check).
Ini untuk: "implement/fix logic spesifik yang diminta user", bukan cuma
"benerin yang error".

Workflow: trace struktur kode (AST) -> pilih file berdasarkan struktur nyata
(bukan tebak nama file) -> LLM patch -> validasi syntax -> caller (brain.py)
wajib lewat auditor_agent sebelum klaim sukses.
"""
import ast
from pathlib import Path
from core.llm_client import llm
from core.logger import logger, console
from rich.panel import Panel


class LogicModifier:

    def _parse_ok(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _clean_code(self, code: str) -> str:
        """Hapus markdown fence kalau LLM masih nyelip nulis ```python ... ```"""
        code = code.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            lines = lines[1:] if lines[0].startswith("```") else lines
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            code = "\n".join(lines)
        return code.strip()

    def _trace_file(self, filepath: Path) -> str:
        """
        Structural trace SATU file pakai AST — bukan keyword search.
        Untuk tiap function: attribute (self.xxx) yang disentuh dan
        function lain yang dipanggil. Ini jejak alur eksekusi nyata,
        dipakai supaya SiCuan tahu DI MANA logic sebenarnya berada
        sebelum memutuskan file mana yang dipatch.
        """
        try:
            source = filepath.read_text(errors="replace")
            tree = ast.parse(source)
        except SyntaxError:
            return f"{filepath.name}: (syntax error saat trace, dilewati)"
        except Exception as e:
            return f"{filepath.name}: (gagal trace: {e})"

        lines = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                attrs = set()
                calls = set()
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Attribute):
                        if isinstance(sub.value, ast.Name) and sub.value.id == "self":
                            attrs.add(f"self.{sub.attr}")
                    if isinstance(sub, ast.Call):
                        if isinstance(sub.func, ast.Name):
                            calls.add(sub.func.id)
                        elif isinstance(sub.func, ast.Attribute):
                            calls.add(sub.func.attr)

                detail = f"  def {node.name}() [line {node.lineno}]"
                if attrs:
                    detail += f"\n    touches: {', '.join(sorted(attrs))}"
                if calls:
                    detail += f"\n    calls: {', '.join(sorted(calls))}"
                lines.append(detail)

        if not lines:
            return f"{filepath.name}: (tidak ada function terdeteksi)"
        return f"{filepath.name}:\n" + "\n".join(lines)

    def _build_code_trace(self, py_files: list, per_file_cap: int = 700, max_chars: int = 15000) -> str:
        """
        Trace semua file jadi peta struktural untuk LLM. Tiap file dikasih
        alokasi karakter SENDIRI (per_file_cap) -- supaya file yang urutannya
        belakang (misal strategy.py di antara 18 file) tetap kebaca, tidak
        kepotong duluan oleh file besar yang urutannya lebih awal.
        """
        parts = []
        for f in py_files:
            file_trace = self._trace_file(f)
            if len(file_trace) > per_file_cap:
                file_trace = file_trace[:per_file_cap] + "\n  ... (terpotong, ada lebih banyak function di file ini)"
            parts.append(file_trace)
        full = "\n\n".join(parts)
        return full[:max_chars]


    def _extract_function_block(self, code: str, function_name: str):
        """
        Ambil satu function saja dari file menggunakan AST.
        Dipakai agar LLM tidak rewrite seluruh file.
        """
        try:
            tree = ast.parse(code)
        except Exception:
            return None

        lines = code.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    return "\n".join(
                        lines[node.lineno - 1: node.end_lineno]
                    )

        return None


    def _list_functions(self, code: str):
        try:
            tree = ast.parse(code)
        except Exception:
            return []

        return [
            n.name
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]




    def _replace_function_block(self, original: str, function_name: str, new_function: str):
        """
        Replace SATU function memakai AST.
        Preserve class indentation dan function lain.
        """

        try:
            tree = ast.parse(original)
        except Exception:
            return original

        lines = original.splitlines()

        target = None
        parent_class_indent = 0

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef):

                for child in node.body:
                    if (
                        isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and child.name == function_name
                    ):
                        target = child
                        parent_class_indent = (
                            len(lines[node.lineno - 1])
                            - len(lines[node.lineno - 1].lstrip())
                            + 4
                        )

        if target is None:

            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == function_name
                ):
                    target = node
                    break

        if target is None:
            return original


        start = target.lineno - 1
        end = target.end_lineno


        new_lines = new_function.splitlines()

        non_empty = [
            len(x) - len(x.lstrip())
            for x in new_lines
            if x.strip()
        ]

        base_indent = min(non_empty) if non_empty else 0


        normalized = []

        for line in new_lines:

            if line.strip():

                normalized.append(
                    " " * parent_class_indent +
                    line[base_indent:]
                )

            else:
                normalized.append("")


        return "\n".join(
            lines[:start]
            + normalized
            + lines[end:]
        )


    def modify_file(self, filepath: str, instruction: str, project_context: str = "", function_name: str = None, max_retries: int = 2) -> dict:
        """
        Patch SATU file sesuai instruction spesifik dari user.
        Retry dengan error feedback kalau output tidak valid syntax.

        Return:
          {"status": "success"|"failed", "file": str, "reason": str (kalau failed), "attempts": int}
        """
        p = Path(filepath)
        if not p.exists():
            return {"status": "failed", "file": filepath, "reason": "File tidak ditemukan", "attempts": 0}

        original = p.read_text(errors="replace")
        last_error = None
        last_output = None

        for attempt in range(1, max_retries + 1):
            error_feedback = ""
            if last_error:
                error_feedback = (
                    f"\n\nPERHATIAN: percobaan sebelumnya GAGAL dengan error:\n"
                    f"{last_error}\n\n"
                    f"Output sebelumnya (untuk referensi apa yang salah):\n"
                    f"{(last_output or '')[:1500]}\n\n"
                    f"Perbaiki error syntax ini. Pastikan output adalah kode Python "
                    f"yang lengkap dan valid."
                )

            target_code = original

            if function_name:
                extracted = self._extract_function_block(
                    original,
                    function_name
                )

                if extracted:
                    target_code = extracted

            prompt = (
                f"Modifikasi kode Python SESUAI INSTRUKSI.\n"
                f"JANGAN rewrite file lain.\n"
                f"JANGAN ubah function lain.\n\n"
                f"FILE: {p.name}\n"
                f"TARGET FUNCTION: {function_name or 'AUTO'}\n\n"
                f"INSTRUKSI USER:\n{instruction}\n\n"
                f"KODE TARGET SAAT INI:\n{target_code}\n\n"
                f"PROJECT CONTEXT (file lain yang relevan):\n{project_context[:800]}"
                f"{error_feedback}\n\n"
                f"""
OUTPUT RULES WAJIB:

- Jika TARGET FUNCTION diberikan, output HANYA function tersebut.
- Jangan output import.
- Jangan output from.
- Jangan output class.
- Jangan output file header.
- Jangan output function lain.
- Jangan rewrite seluruh file.
- Pertahankan nama function.
- Pertahankan parameter function.
- Output harus langsung dimulai dengan:
  def atau async def

Contoh benar:

async def check_risk(self, position):
    return result

Contoh salah:

import os
class Config:
def check_risk(self):
"""
            )

            try:
                console.print(f"  🔧 Modifying: {p.name} (attempt {attempt}/{max_retries})")
                raw = llm.chat(
                    messages=[{"role": "user", "content": prompt}],
                    system=(
                        "Kamu adalah senior Python engineer. Modifikasi kode SESUAI "
                        "instruksi spesifik, jangan rewrite total, jangan menghapus "
                        "logic yang tidak diminta untuk diubah."
                    ),
                    temperature=0.3,
                    max_tokens=1800,
                )
                fixed = self._clean_code(raw)

                if function_name:

                    forbidden = [
                        "import ",
                        "from ",
                        "class ",
                    ]

                    bad = [
                        token
                        for token in forbidden
                        if token in fixed
                    ]

                    if bad:
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": (
                                f"Patch ditolak: output function "
                                f"mengandung forbidden token {bad}"
                            ),
                            "attempts": attempt,
                        }

                    first_line = fixed.splitlines()[0].strip()

                    if not (
                        first_line.startswith("def ")
                        or first_line.startswith("async def ")
                    ):
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": (
                                "Patch ditolak: output bukan function"
                            ),
                            "attempts": attempt,
                        }


                print("===== DEBUG FIXED =====")
                print(fixed[:1000])
                print("=======================")

                last_output = fixed


                # HARD PATCH GUARD
                # Tolak output LLM yang mencoba rewrite file
                if function_name:

                    forbidden = [
                        "import ",
                        "from ",
                        "class ",
                        "```",
                    ]

                    bad = [
                        x for x in forbidden
                        if x in fixed
                    ]

                    if bad:
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": (
                                "Patch ditolak: "
                                f"LLM mengeluarkan forbidden token {bad}"
                            ),
                            "attempts": attempt,
                        }

                    if not fixed.lstrip().startswith(
                        "def "
                    ):
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": (
                                "Patch ditolak: output bukan function"
                            ),
                            "attempts": attempt,
                        }

                    if f"def {function_name}" not in fixed:
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": (
                                "Patch ditolak: function target hilang"
                            ),
                            "attempts": attempt,
                        }


                if not fixed or not self._parse_ok(fixed):
                    try:
                        ast.parse(fixed or "")
                    except SyntaxError as e:
                        last_error = f"SyntaxError line {e.lineno}: {e.msg}"
                    else:
                        last_error = "Output kosong atau tidak valid"
                    continue  # retry

                if function_name:
                    final_code = self._replace_function_block(
                        original,
                        function_name,
                        fixed
                    )

                    # guard: replace function wajib mempertahankan file lain
                    if len(final_code) < len(original) * 0.75:
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": (
                                f"Function replacement gagal. "
                                f"File menyusut {len(original)} -> {len(final_code)} chars."
                            ),
                            "attempts": attempt,
                        }

                else:
                    final_code = fixed

                if len(final_code) < len(original) * 0.5:
                    return {
                        "status": "failed",
                        "file": filepath,
                        "reason": (
                            f"Output mencurigakan: panjang kode turun drastis "
                            f"({len(original)} -> {len(final_code)} chars). Kemungkinan "
                            f"LLM menghapus logic yang tidak diminta. Ditolak demi keamanan."
                        ),
                        "attempts": attempt,
                    }

                from sicuan.core.llm_patch_guard import (
                    changed_functions,
                    validate_function_patch
                )

                if function_name:
                    validation = validate_function_patch(
                        original,
                        final_code,
                        function_name
                    )

                    if not validation["ok"]:
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": validation["reason"],
                            "attempts": attempt,
                        }

                touched = changed_functions(
                    original,
                    final_code
                )

                print("===== CHANGED FUNCTIONS =====")
                print(touched)
                print("=============================")

                if not touched:
                    return {
                        "status": "failed",
                        "file": filepath,
                        "reason": (
                            "Patch ditolak: tidak ada function yang berubah. "
                            "LLM hanya menghasilkan rewrite kosong."
                        ),
                        "attempts": attempt,
                    }

                console.print(
                    f"  [dim]Functions changed: {', '.join(touched)}[/dim]"
                )

                p.write_text(final_code)

                console.print(f"  [green]✓ Modified: {p.name}[/green]")
                return {
                    "status": "success",
                    "file": filepath,
                    "attempts": attempt,
                    "changed_functions": touched,
                }

            except Exception as e:
                logger.error(f"Logic modify error on {filepath}: {e}")
                last_error = str(e)
                continue

        return {
            "status": "failed",
            "file": filepath,
            "reason": f"Gagal setelah {max_retries} percobaan. Error terakhir: {last_error}",
            "attempts": max_retries,
        }

    def modify_project(self, project_dir: str, instruction: str, target_files: list = None) -> dict:
        """
        Patch project. Kalau target_files tidak dispesifikasikan, trace
        struktur kode (AST) dipakai untuk menentukan file mana yang relevan
        berdasarkan attribute/function yang benar-benar disentuh — bukan
        nebak dari nama file.
        """
        pdir = Path(project_dir)
        if not pdir.exists():
            return {"error": f"Directory not found: {project_dir}"}

        py_files = sorted(pdir.glob("*.py"))
        if not py_files:
            return {"error": "Tidak ada file Python di project ini"}

        code_trace = ""
        if not target_files:
            target_files, code_trace = self._guess_relevant_files(instruction, py_files)

        if not target_files:
            return {
                "modified": [],
                "failed": [],
                "status": "no_target",
                "reason": "Tidak bisa menentukan file mana yang relevan dengan instruksi, bahkan setelah trace struktur kode",
            }

        display_targets = []

        for item in target_files:
            if isinstance(item, dict):
                display_targets.append(
                    f"{item.get('file')}:{item.get('function')}"
                )
            else:
                display_targets.append(str(item))

        console.print(Panel(
            f"[cyan]Project:[/cyan] {pdir.name}\n"
            f"[cyan]Target functions (AST trace):[/cyan] {', '.join(display_targets)}\n"
            f"[cyan]Instruction:[/cyan] {instruction[:200]}",
            title="🎯 Logic Modify",
            border_style="blue"
        ))

        context = self._build_context(py_files, exclude=target_files)

        modified = []
        failed = []
        for item in target_files:
            if isinstance(item, dict):
                fname = item.get("file")
                function_name = item.get("function")
            else:
                fname = item
                function_name = None

            file_path = Path(fname)

            candidates = [
                file_path,
                pdir / file_path.name,
                pdir / file_path,
                Path.cwd() / file_path,
            ]

            fpath = None

            for candidate in candidates:
                if candidate.exists():
                    fpath = candidate
                    break

            if fpath is None:
                failed.append({
                    "file": fname,
                    "reason": "File tidak ditemukan setelah resolve path"
                })
                continue

            result = self.modify_file(
                str(fpath),
                instruction,
                context,
                function_name
            )

            if result.get("status") == "success":
                after_size = fpath.stat().st_size

                if after_size < 200:
                    failed.append({
                        "file": fname,
                        "reason": "Patch ditolak: hasil terlalu kecil/rusak"
                    })
                    continue
            if result["status"] == "success":
                modified.append(fname)
            else:
                failed.append({"file": fname, "reason": result.get("reason", "unknown")})

        status = "success" if modified and not failed else ("partial" if modified else "failed")

        console.print(Panel(
            f"Modified: {modified}\nFailed: {failed}",
            title="🎯 Logic Modify Complete",
            border_style="green" if status == "success" else "yellow"
        ))

        return {"modified": modified, "failed": failed, "status": status, "code_trace_used": bool(code_trace)}

    def _guess_relevant_files(self, instruction: str, py_files: list):
        """
        Tentukan file relevan berdasarkan TRACE STRUKTUR KODE (AST):
        function apa yang ada, attribute apa yang disentuh, function apa
        yang dipanggil. Bukan keyword search di teks mentah, dan bukan
        cuma nebak dari nama file.
        """
        filenames = [f.name for f in py_files]
        code_trace = self._build_code_trace(py_files)

        prompt = (
            f"Instruksi user: {instruction}\n\n"
            f"STRUKTUR KODE PROJECT (hasil trace AST — function, attribute yang "
            f"disentuh tiap function, dan function lain yang dipanggil):\n\n"
            f"{code_trace}\n\n"
            f"Berdasarkan STRUKTUR DI ATAS — bukan nama file, bukan tebakan — "
            f"function dan file mana yang PALING RELEVAN untuk dimodifikasi "
            f"sesuai instruksi user? Perhatikan attribute yang disentuh "
            f"(misal self.paper_balance, self.position) dan alur calls antar "
            f"function. Itu jejak nyata, bukan asumsi dari nama variabel.\n\n"
            f"Jawab maksimal 2 target dengan format EXACT:\n"
            f"nama_file.py:nama_function\n\n"
            f"Contoh:\n"
            f"risk_manager.py:_update_trailing_stop\n"
            f"strategy.py:_check_exit_conditions\n\n"
            f"Jangan jawab penjelasan. Jangan gunakan markdown."
        )
        try:
            raw = llm.chat(
                messages=[{"role": "user", "content": prompt}],
                system=(
                    "Kamu adalah code analyst yang membaca STRUKTUR kode (AST trace) "
                    "untuk menentukan lokasi logic yang benar — bukan menebak dari nama "
                    "file atau keyword. Kalau struktur menunjukkan attribute/function "
                    "tertentu yang relevan, ikuti jejak itu sampai ke file aslinya."
                ),
                temperature=0.1,
                max_tokens=100,
            )
            candidates = [
                c.strip()
                for c in raw.replace("\n", ",").split(",")
                if c.strip()
            ]

            result = []

            for item in candidates[:5]:

                if ":" in item:
                    file_name, function_name = item.split(":", 1)

                    file_name = file_name.strip()
                    function_name = function_name.strip()

                    if file_name in filenames:
                        result.append({
                            "file": file_name,
                            "function": function_name
                        })

                elif item in filenames:
                    result.append({
                        "file": item,
                        "function": None
                    })

            # Prioritaskan function paling spesifik sesuai request
            if (
                "trailing" in instruction.lower()
                and "stop" in instruction.lower()
            ):
                result = [
                    x for x in result
                    if (
                        "trailing" in str(x.get("function", "")).lower()
                    )
                ]


            console.print(
                f"  [dim]Trace hasil: "
                f"{', '.join(
                    [
                        x['file'] + ':' + str(x['function'])
                        for x in result
                    ]
                ) if result else '(tidak ketemu)'}[/dim]"
            )

            priority_keywords = {
                "risk": [
                    "risk",
                    "stop_loss",
                    "take_profit",
                    "trailing",
                    "exposure",
                    "cooldown",
                    "loss",
                ],
                "profitability": [
                    "pnl",
                    "profit",
                    "return",
                    "roi",
                    "sell",
                    "buy",
                ],
                "performance": [
                    "run",
                    "execute",
                    "monitor",
                    "cache",
                    "async",
                ]
            }


            instruction_lower = instruction.lower()


            def score(item):

                fn = item["function"].lower()

                value = 0

                for category, words in priority_keywords.items():

                    if category in instruction_lower:

                        for word in words:

                            if word in fn:
                                value += 10

                return value


            result.sort(
                key=score,
                reverse=True
            )


            result = [
                x for x in result
                if score(x) > 0
            ][:2]


            return result, code_trace
        except Exception as e:
            logger.error(f"Trace-based file selection failed: {e}")
            return [], code_trace

    def _build_context(self, py_files: list, exclude: list, max_chars: int = 1500) -> str:
        parts = []

        exclude_names = [
            x.get("file") if isinstance(x, dict) else x
            for x in exclude
        ]

        for f in py_files:
            if f.name in exclude_names:
                continue
            try:
                content = f.read_text(errors="replace")
                parts.append(f"--- {f.name} (first 300 chars) ---\n{content[:300]}")
            except Exception:
                continue
        return "\n\n".join(parts)[:max_chars]



    def modify(
        self,
        project_dir,
        instruction,
        target_files=None
    ):
        """
        Compatibility wrapper for autonomous agents.
        """
        return self.modify_project(
            str(project_dir),
            instruction,
            target_files
        )


logic_modifier = LogicModifier()


