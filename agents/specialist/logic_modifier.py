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

                            if isinstance(sub.func.value, ast.Name):
                                calls.add(
                                    f"{sub.func.value.id}.{sub.func.attr}"
                                )
                            else:
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

    def _build_code_trace(self, py_files: list, per_file_cap: int = 1800, max_chars: int = 30000) -> str:
        """
        Trace semua file jadi peta struktural untuk LLM. Tiap file dikasih
        alokasi karakter SENDIRI (per_file_cap) -- supaya file yang urutannya
        belakang (misal strategy.py di antara 18 file) tetap kebaca, tidak
        kepotong duluan oleh file besar yang urutannya lebih awal.
        """
        trading_priority = {
            "strategy.py",
            "risk_manager.py",
            "sniper.py",
            "raydium_client.py",
            "jupiter_client.py",
            "wallet.py",
            "database.py",
            "token_memory.py",
        }

        priority_order = [
            "strategy.py",
            "risk_manager.py",
            "sniper.py",
            "raydium_client.py",
            "jupiter_client.py",
            "wallet.py",
            "database.py",
            "token_memory.py",
        ]

        py_files = sorted(
            [
                f for f in py_files
                if f.name in trading_priority
            ],
            key=lambda x: (
                priority_order.index(x.name)
                if x.name in priority_order
                else 999
            )
        )

        # budget per file supaya semua core module tetap terlihat LLM
        budgets = {
            "strategy.py": 5000,
            "risk_manager.py": 4000,
            "raydium_client.py": 4000,
            "jupiter_client.py": 3000,
            "wallet.py": 3000,
            "database.py": 3000,
            "sniper.py": 3000,
            "token_memory.py": 1500,
        }

        parts = []

        for f in py_files:

            file_trace = self._trace_file(f)

            cap = budgets.get(
                f.name,
                per_file_cap
            )

            if len(file_trace) > cap:
                file_trace = (
                    file_trace[:cap]
                    + "\n  ... (function lain dipotong)"
                )

            parts.append(file_trace)

        return "\n\n".join(parts)


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


    def modify_file(
        self,
        filepath: str,
        instruction: str,
        project_context: str = "",
        function_name: str = None,
        max_retries: int = 2
    ) -> dict:
        """
        Modify one target function safely.
        Output from LLM is sanitized before replacing.
        """

        path = Path(filepath)

        if not path.exists():
            return {
                "status": "failed",
                "file": filepath,
                "reason": "file_not_found"
            }

        code = path.read_text(errors="replace")

        target_code = code

        if function_name:
            extracted = self._extract_function_block(code, function_name)
            if extracted:
                target_code = extracted

        prompt = (
            "Modifikasi kode Python SESUAI INSTRUKSI.\n"
            "JANGAN rewrite file lain.\n"
            "JANGAN ubah function lain.\n\n"
            f"FILE: {path.name}\n"
            f"TARGET FUNCTION: {function_name or 'AUTO'}\n\n"
            f"INSTRUKSI USER:\n{instruction}\n\n"
            f"KODE TARGET SAAT INI:\n{target_code}\n\n"
            f"PROJECT CONTEXT:\n{project_context[:800]}\n\n"
            "OUTPUT RULES:\n"
            "- Output hanya function.\n"
            "- Jangan output import.\n"
            "- Jangan output class.\n"
            "- Pertahankan nama function.\n"
            "- Pertahankan parameter.\n"
            "- Mulai dengan def atau async def."
        )

        for attempt in range(1, max_retries + 1):
            try:
                console.print(
                    f"  🔧 Modifying: {path.name} "
                    f"(attempt {attempt}/{max_retries})"
                )

                raw = llm.chat(
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    system=(
                        "Kamu adalah senior Python engineer. "
                        "Modifikasi logic spesifik tanpa rewrite total."
                    ),
                    temperature=0.3,
                    max_tokens=16000,
                )

                fixed = self._clean_code(raw)

                if not (
                    fixed.startswith("def ")
                    or fixed.startswith("async def ")
                ):
                    return {
                        "status": "failed",
                        "file": filepath,
                        "reason": "invalid_function_output"
                    }

                # Safety check:
                # hanya blokir statement import/class nyata.
                # Jangan blokir string/comment/docstring yang kebetulan
                # mengandung kata import/from/class.

                try:
                    output_tree = ast.parse(fixed)

                    forbidden_nodes = any(
                        isinstance(
                            node,
                            (
                                ast.Import,
                                ast.ImportFrom,
                                ast.ClassDef,
                            )
                        )
                        for node in ast.walk(output_tree)
                    )

                    if forbidden_nodes:
                        return {
                            "status": "failed",
                            "file": filepath,
                            "reason": "forbidden_output"
                        }

                except Exception:
                    return {
                        "status": "failed",
                        "file": filepath,
                        "reason": "invalid_function_output"
                    }

                if function_name and f"def {function_name}" not in fixed and f"async def {function_name}" not in fixed:
                    return {
                        "status": "failed",
                        "file": filepath,
                        "reason": "wrong_function"
                    }

                updated = self._replace_function_block(
                    code,
                    function_name,
                    fixed
                )

                path.write_text(updated)

                return {
                    "status": "success",
                    "file": filepath,
                    "function": function_name
                }

            except Exception as e:
                logger.error(
                    f"modify_file failed: {e}"
                )

        return {
            "status": "failed",
            "file": filepath,
            "reason": "max_retry"
        }

    def modify_project(self, project_dir: str, instruction: str, target_files: list = None) -> dict:
        """
        Patch project. Kalau target_files tidak dispesifikasikan, trace
        struktur kode (AST) dipakai untuk menentukan file mana yang relevan
        berdasarkan attribute/function yang benar-benar disentuh — bukan
        nebak dari nama file.
        """
        pdir = Path(project_dir)

        # Normalize target_files dari planner/LLM
        if isinstance(target_files, dict):
            target_files = [target_files]

        if target_files:
            normalized_targets = []

            for item in target_files:
                if isinstance(item, dict):
                    if item.get("file"):
                        normalized_targets.append({
                            "file": item.get("file"),
                            "function": item.get("function")
                        })

                elif isinstance(item, str):
                    normalized_targets.append(item)

            target_files = normalized_targets

        if not pdir.exists():
            return {"error": f"Directory not found: {project_dir}"}

        priority_files = [
            "strategy.py",
            "sniper.py",
            "risk_manager.py",
            "raydium_client.py",
            "jupiter_client.py",
            "wallet.py",
            "database.py",
        ]

        py_files = sorted(
            pdir.glob("*.py"),
            key=lambda x: (
                priority_files.index(x.name)
                if x.name in priority_files
                else 99
            )
        )

        if not py_files:
            return {"error": "Tidak ada file Python di project ini"}

        code_trace = ""
        if not target_files:
            target_files, code_trace = self._guess_relevant_files(
                instruction,
                py_files
            )

        # Normalize target_files agar selalu list[dict]
        if isinstance(target_files, dict):
            target_files = [target_files]

        elif isinstance(target_files, list):
            normalized_targets = []

            for item in target_files:

                if isinstance(item, list):
                    for sub in item:
                        if isinstance(sub, dict):
                            normalized_targets.append(sub)

                elif isinstance(item, dict):
                    normalized_targets.append(item)

                elif isinstance(item, str):
                    if ":" in item:
                        fname, func = item.split(":", 1)
                        normalized_targets.append({
                            "file": fname.strip(),
                            "function": func.strip()
                        })
                    else:
                        normalized_targets.append({
                            "file": item.strip(),
                            "function": None
                        })

            target_files = normalized_targets

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

        if not isinstance(target_files, list):
            target_files = [target_files]

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

        # === EXECUTION VALIDATION ===
        try:
            from sicuan.core.execution_validator import get_validator
            validator = get_validator()
            validation = validator.validate({"patch": {"modified": modified, "failed": failed}})
            if validation["status"] == "verified":
                print(f"[VALIDATOR] ✅ {validation['reason']}")
            elif validation["status"] == "warning":
                print(f"[VALIDATOR] ⚠️ {validation['reason']}")
            else:
                print(f"[VALIDATOR] ❌ {validation['reason']}")
        except Exception as e:
            print(f"[VALIDATOR] Error: {e}")

                # === WRITE MODIFIED FILES ===
        for file_path in modified:
            try:
                # Baca file asli
                                # Fix path: jika file_path hanya nama file, tambahkan project_dir
                if not Path(file_path).exists():
                    full_path = Path("projects/godmeme_bot") / file_path
                    if not full_path.exists():
                        full_path = Path("projects/godmeme_bot") / Path(file_path).name
                else:
                    full_path = Path(file_path)
                if not full_path.exists():
                    print(f"[MODIFY] ❌ File not found: {file_path}")
                    continue
                
                # Baca new_code dari memory (harusnya sudah disimpan sebelumnya)
                # Jika tidak ada, skip
                print(f"[MODIFY] ✅ Would write: {file_path}")
                # TODO: Implement actual write
            except Exception as e:
                print(f"[MODIFY] ❌ Error writing {file_path}: {e}")
        
        return {"modified": modified, "failed": failed, "status": status, "code_trace_used": bool(code_trace)}


    def _score_ast_relevance(self, instruction: str, py_files: list):
        """
        AST based relevance ranking.
        Mencari function paling dekat dengan intent user sebelum LLM.
        """
        keywords = {
            "buy": 8,
            "entry": 8,
            "open": 6,
            "sell": 8,
            "exit": 8,
            "close": 6,
            "profit": 8,
            "pnl": 8,
            "loss": 8,
            "risk": 9,
            "stop": 8,
            "take": 7,
            "balance": 6,
            "wallet": 6,
            "swap": 7,
            "trade": 6,
            "token": 5,
            "scan": 5,
            "monitor": 5,
        }

        text = instruction.lower()
        scored = []

        for f in py_files:
            try:
                source = f.read_text(errors="replace")
            except Exception:
                continue

            for fn in self._list_functions(source):

                score = 0
                blob = fn.lower()

                for k, weight in keywords.items():
                    if k in text and k in blob:
                        score += weight

                # cek function body
                block = self._extract_function_block(
                    source,
                    fn
                )

                if block:
                    block_low = block.lower()

                    for k, weight in keywords.items():
                        if k in text and k in block_low:
                            score += weight // 2

                # bonus untuk function yang berada di decision flow trading
                flow_bonus = {
                    # decision layer
                    "_should_buy": 20,
                    "_assess_risk_level": 18,
                    "can_open_position": 16,

                    # position lifecycle
                    "_open_position": 18,
                    "add_position": 14,

                    # execution layer
                    "execute_buy": 14,
                    "swap": 8,

                    # exit management
                    "check_stop_loss": 10,
                    "check_take_profit": 10,

                    # token filtering
                    "check_risk": 8,
                }

                score += flow_bonus.get(fn, 0)

                # penalti function pembacaan/reporting
                passive_penalty = {
                    "get_risk_metrics": -5,
                    "get_recent_risk_metrics": -5,
                    "save_risk_metrics": -3,
                    "send_risk_alert": -3,
                }

                score += passive_penalty.get(fn, 0)

                if score:
                    scored.append(
                        {
                            "file": f.name,
                            "function": fn,
                            "score": score,
                        }
                    )

        scored.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return scored[:10]


    def _rank_logic_candidates(self, instruction, py_files):
        """
        Ranking logic target berdasarkan AST + trading flow.
        LLM hanya melakukan validasi dari kandidat ini.
        """

        instruction_lower = instruction.lower()

        keywords = {
            "buy": 10,
            "entry": 10,
            "cuan": 8,
            "profit": 8,
            "risiko": 8,
            "risk": 8,
            "sell": 8,
            "exit": 8,
            "loss": 8,
            "stop": 6,
            "strategi": 6,
            "trading": 6,
        }

        flow_bonus = {
            "_should_buy": 18,
            "can_open_position": 17,
            "_assess_risk_level": 14,
            "_open_position": 16,
            "add_position": 10,
            "execute_buy": 13,
            "swap": 5,
            "check_stop_loss": 8,
            "check_take_profit": 8,
        }

        passive_penalty = {
            "get_risk_metrics": -5,
            "get_recent_risk_metrics": -5,
            "save_risk_metrics": -3,
            "send_risk_alert": -3,
        }

        result = []

        for f in py_files:
            try:
                code = f.read_text(errors="replace")
                funcs = self._list_functions(code)
            except Exception:
                continue

            for fn in funcs:
                score = 0
                text = f"{f.name} {fn}".lower()

                for key, weight in keywords.items():
                    if key in instruction_lower and key in text:
                        score += weight

                score += flow_bonus.get(fn, 0)
                score += passive_penalty.get(fn, 0)

                if score:
                    result.append({
                        "file": f.name,
                        "function": fn,
                        "score": score
                    })

        return sorted(
            result,
            key=lambda x: x["score"],
            reverse=True
        )

    def _guess_relevant_files(self, instruction: str, py_files: list):
        """
        Tentukan file relevan berdasarkan TRACE STRUKTUR KODE (AST):
        function apa yang ada, attribute apa yang disentuh, function apa
        yang dipanggil. Bukan keyword search di teks mentah, dan bukan
        cuma nebak dari nama file.
        """
        filenames = [f.name for f in py_files]
        code_trace = self._build_code_trace(py_files)

        ranked = self._rank_logic_candidates(
            instruction,
            py_files
        )

        # ENTRY BUY FLOW PRIORITY OVERRIDE
        # Jangan biarkan LLM salah memilih open_position/risk sizing
        # untuk instruksi yang menyentuh entry.

        instruction_lower = instruction.lower()

        entry_keywords = [
            "entry",
            "buy",
            "beli",
            "masuk posisi",
            "open position",
            "strategi",
        ]

        if any(k in instruction_lower for k in entry_keywords):

            preferred_flow = [
                "strategy.py:_should_buy",
                "sniper.py:execute_buy",
                "sniper.py:can_open_position",
                "risk_manager.py:add_position",
                "strategy.py:_open_position",
            ]

            boosted = []

            ranked_names = [
                f"{x['file']}:{x['function']}"
                for x in ranked
            ]

            for target in preferred_flow:
                if target in ranked_names:
                    boosted.append(target)

            if boosted:
                ranked_context = "\n".join(boosted[:5])
            else:
                ranked_context = "\n".join(
                    [
                        f"{x['file']}:{x['function']} score={x['score']}"
                        for x in ranked[:15]
                    ]
                )

        else:
            ranked_context = "\n".join(
                [
                    f"{x['file']}:{x['function']} score={x['score']}"
                    for x in ranked[:15]
                ]
            )

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
                max_tokens=16000,
            )
            import re

            candidates = []

            for line in raw.splitlines():

                line = line.strip()

                if not line:
                    continue

                # buang numbering markdown
                line = re.sub(
                    r"^[0-9]+[.)-]\\s*",
                    "",
                    line
                )

                # ambil pola file:function
                match = re.search(
                    r"([A-Za-z0-9_]+\.py)(?::([A-Za-z0-9_]+))?",
                    line
                )

                if match:
                    candidates.append(
                        match.group(0)
                    )

            result = []

            # fallback AST jika LLM tidak memberikan target
            if not candidates:
                fallback = []

                instruction_lower = instruction.lower()

                for f in py_files:
                    try:
                        funcs = self._list_functions(
                            f.read_text(errors="replace")
                        )
                    except Exception:
                        continue

                    for fn in funcs:
                        fn_lower = fn.lower()

                        if any(
                            x in instruction_lower
                            for x in [
                                "cuan",
                                "profit",
                                "pnl",
                                "risiko",
                                "trading",
                                "buy",
                                "sell",
                                "stop",
                                "take",
                                "strategi",
                            ]
                        ):
                            if any(
                                y in fn_lower
                                for y in [
                                    "buy",
                                    "sell",
                                    "profit",
                                    "loss",
                                    "risk",
                                    "position",
                                    "trade",
                                    "entry",
                                    "exit",
                                    "stop",
                                    "take",
                                    "monitor",
                                ]
                            ):
                                fallback.append(
                                    {
                                        "file": f.name,
                                        "function": fn
                                    }
                                )

                candidates = [
                    f"{x['file']}:{x['function']}"
                    for x in fallback[:5]
                ]

            console.print(f"  [yellow]DEBUG candidates={candidates}[/yellow]")
            console.print(f"  [yellow]DEBUG filenames={filenames}[/yellow]")

            for item in candidates[:5]:

                if ":" in item:
                    file_name, function_name = item.split(":", 1)

                    file_name = file_name.strip()
                    function_name = function_name.strip()

                    print("DEBUG CHECK FILE:", repr(file_name))
                    print("DEBUG FILENAMES:", [repr(x) for x in filenames])

                    if file_name.strip() in [x.strip() for x in filenames]:
                        result.append({
                            "file": file_name.strip(),
                            "function": function_name.strip()
                        })

                elif item in filenames:
                    result.append({
                        "file": item,
                        "function": None
                    })

            # Trailing stop menjadi prioritas tambahan,
            # bukan filter yang membuang reasoning LLM.
            if (
                "trailing" in instruction.lower()
                and "stop" in instruction.lower()
            ):
                for x in result:
                    fn = str(x.get("function", "")).lower()

                    if "trailing" in fn:
                        x["_priority_bonus"] = 50

                    elif any(
                        key in fn
                        for key in [
                            "monitor",
                            "position",
                            "update",
                            "close"
                        ]
                    ):
                        x["_priority_bonus"] = 20

                    else:
                        x["_priority_bonus"] = 0


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

            print(
                "DEBUG INSTRUCTION:",
                repr(instruction_lower)
            )


            def score(item):

                fn = str(item.get("function", "")).lower()
                file_name = str(item.get("file", "")).lower()

                # Bonus dari reasoning LLM / context modifier.
                # Tidak menggantikan semantic scoring.
                value = int(item.get("_priority_bonus", 0))

                semantic_map = {
                    "buy": [
                        "buy",
                        "entry",
                        "open",
                        "position",
                        "swap",
                        "trade",
                    ],
                    "sell": [
                        "sell",
                        "close",
                        "exit",
                        "take",
                        "profit",
                    ],
                    "risk": [
                        "risk",
                        "position",
                        "exposure",
                        "loss",
                        "stop",
                    ],
                    "profit": [
                        "profit",
                        "pnl",
                        "return",
                        "roi",
                    ],
                }

                instruction_words = instruction_lower.split()

                for key, aliases in semantic_map.items():

                    if key in instruction_lower:

                        for alias in aliases:

                            if alias in fn:
                                value += 10

                            if alias in file_name:
                                value += 5

                return value


            result.sort(
                key=score,
                reverse=True
            )


            print("DEBUG SCORE:")
            for x in result:
                print(
                    x,
                    "=>",
                    score(x)
                )

            # Jangan membuang hasil reasoning LLM hanya karena
            # nama function tidak mengandung keyword.
            # Keyword hanya boleh menjadi bonus ranking.

            if result:
                result = result[:5]

            # Safety fallback:
            # jika LLM sudah memberi candidate valid tetapi scoring kosong,
            # tetap gunakan reasoning LLM.
            if not result and candidates:
                result = [
                    {
                        "file": x.split(":", 1)[0],
                        "function": (
                            x.split(":", 1)[1]
                            if ":" in x
                            else None
                        )
                    }
                    for x in candidates[:2]
                ]


            return result
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


