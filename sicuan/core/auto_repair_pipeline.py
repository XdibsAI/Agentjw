"""
Auto Repair Pipeline — Desain baru yang deterministik
"""

from pathlib import Path
import hashlib
import subprocess
import time
from typing import Dict, List, Optional
from sicuan.core.patch_verifier import get_patch_verifier
from datetime import datetime


class AutoRepairPipeline:
    """
    Pipeline auto-repair:
    1. Error Classifier → tentukan jenis error
    2. Repair Planner → pilih strategi berdasarkan jenis
    3. Patch Generator → generate patch
    4. Patch Verifier → cek apakah patch berhasil di-apply
    5. Build/Test → jalankan test
    6. Health Check → cek apakah error hilang
    """

    def __init__(self):
        self.project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")
        self.main_py = self.project_dir / "main.py"
        self.attempt_history = []
        self.max_attempts = 3

    def classify_error(self, error: str) -> Dict:
        """Klasifikasi error berdasarkan traceback"""
        error_type = "unknown"
        file = None
        line = None
        message = ""

        if "ModuleNotFoundError" in error:
            error_type = "import_error"
            # Extract module name
            import re
            match = re.search(r"No module named '([^']+)'", error)
            if match:
                message = f"Module not found: {match.group(1)}"
        elif "SyntaxError" in error:
            error_type = "syntax_error"
        elif "AttributeError" in error:
            error_type = "attribute_error"
        elif "IndentationError" in error:
            error_type = "indentation_error"
        elif "FileNotFoundError" in error:
            error_type = "file_not_found"

        # Extract file and line
        import re
        file_match = re.search(r'File "([^"]+)", line (\d+)', error)
        if file_match:
            file = file_match.group(1)
            line = int(file_match.group(2))

        return {
            "type": error_type,
            "file": file,
            "line": line,
            "message": message,
            "traceback": error[:500]
        }

    def get_strategies(self, error_type: str) -> List[str]:
        """Dapatkan strategi perbaikan berdasarkan jenis error"""
        strategies = {
            "import_error": [
                "fix_sys_path",
                "fix_import_statement",
                "fix_pythonpath",
                "fix_module_installation"
            ],
            "syntax_error": [
                "fix_syntax",
                "fix_indentation"
            ],
            "attribute_error": [
                "add_method",
                "fix_attribute_name"
            ],
            "indentation_error": [
                "fix_indentation",
                "fix_syntax"
            ],
            "file_not_found": [
                "create_file",
                "fix_file_path"
            ],
            "unknown": [
                "analyze_and_fix"
            ]
        }
        return strategies.get(error_type, strategies["unknown"])

    def verify_patch(self, file_path: str) -> Dict:
        """Verifikasi apakah patch berhasil di-apply"""
        full_path = self.project_dir / file_path
        result = {
            "exists": full_path.exists(),
            "hash": "",
            "size": 0,
            "changed": False
        }
        if full_path.exists():
            with open(full_path, "rb") as f:
                result["hash"] = hashlib.md5(f.read()).hexdigest()
            result["size"] = full_path.stat().st_size
        return result

    def restart_and_check(self) -> Dict:
        """Restart bot dan cek error"""
        result = {
            "success": False,
            "error": "",
            "error_type": "unknown"
        }

        try:
            # Kill existing
            subprocess.run(["pkill", "-f", "main.py"], capture_output=True, timeout=5)
            time.sleep(2)

            # Start bot
            process = subprocess.Popen(
                ["python3", str(self.main_py)],
                cwd=str(self.project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            time.sleep(3)

            if process.poll() is not None:
                stdout, stderr = process.communicate(timeout=5)
                output = stderr or stdout
                if output:
                    result["error"] = output[:500]
                    classified = self.classify_error(output)
                    result["error_type"] = classified["type"]
                result["success"] = False
            else:
                result["success"] = True
                process.terminate()

        except Exception as e:
            result["error"] = str(e)

        return result

    def run(self, error: str, traceback: str = None) -> Dict:
        """Jalankan pipeline auto-repair dengan traceback lengkap"""
        print(f"[PIPELINE] Starting auto-repair for: {error[:50]}...")

        # 1. Classify error — gunakan traceback jika ada
        error_text = traceback if traceback else error
        error_info = self.classify_error(error_text)
        print(f"[PIPELINE] Error Type: {error_info['type']}")
        print(f"[PIPELINE] File: {error_info.get('file', 'N/A')}")
        if error_info.get('file'):
            print(f"[PIPELINE] Line: {error_info.get('line', 'N/A')}")

        # 2. Get strategies
        strategies = self.get_strategies(error_info['type'])
        print(f"[PIPELINE] Strategies: {strategies}")

        # 3. Loop through strategies
        for attempt, strategy in enumerate(strategies[:self.max_attempts], 1):
            print(f"\n[PIPELINE] Attempt {attempt}/{self.max_attempts}: {strategy}")

            # Check if strategy already tried
            if strategy in self.attempt_history:
                print(f"[PIPELINE] ⚠️ Strategy '{strategy}' already tried, skipping")
                continue

            # 4. Generate patch (simulasi)
            patch_result = self._generate_patch(strategy, error_info)
            self.attempt_history.append(strategy)

            # 5. Verify patch
            if patch_result["success"]:
                print(f"[PIPELINE] ✅ Patch applied to: {patch_result['file']}")

                # 6. Restart and check
                restart_result = self.restart_and_check()

                if restart_result["success"]:
                    print(f"[PIPELINE] ✅ Bot running!")
                    return {
                        "success": True,
                        "attempt": attempt,
                        "strategy": strategy,
                        "error_type": error_info['type']
                    }
                else:
                    print(f"[PIPELINE] ❌ Bot failed: {restart_result['error_type']}")
                    # Update error untuk iterasi berikutnya
                    error_info = self.classify_error(restart_result['error'])
            else:
                print(f"[PIPELINE] ❌ Patch failed to apply")

        print(f"\n[PIPELINE] ❌ All strategies exhausted")
        return {
            "success": False,
            "attempts": len(self.attempt_history),
            "strategies_tried": self.attempt_history
        }

    def _generate_patch(self, strategy: str, error_info: Dict) -> Dict:
        """Generate patch berdasarkan strategi dengan PatchExecutor"""
        from sicuan.core.patch_executor import get_patch_executor
        executor = get_patch_executor()
        verifier = get_patch_verifier()
        
        # Simulasi patch
        file_path = error_info.get("file")
        if file_path is None:
            # Default ke main.py jika tidak ada file
            file_path = "godmeme_bot/main.py"
            print(f"[PIPELINE] ⚠️ No file in error, using default: {file_path}")
        full_path = self.project_dir / file_path
        
        if not full_path.exists():
            return {"success": False, "file": file_path, "error": "File not found"}
        
        # Baca sebelum
        before = full_path.read_text()
        
        # Execute patch dengan PatchExecutor
        # Peta strategi ke patch type
        patch_type_map = {
            "fix_sys_path": "add_sys_path",
            "fix_import_statement": "add_import",
            "fix_pythonpath": "add_sys_path",
        }
        
        patch_type = patch_type_map.get(strategy, "add_sys_path")
        patch_plan = {"type": patch_type, "content": ""}
        
        # Execute patch
        result = executor.execute(file_path, patch_plan)
        
        if result["success"] and result["changed"]:
            print(f"[PIPELINE] ✅ Patch applied: {file_path}")
            print(f"[PIPELINE]    Hash: {result.get('hash_before', 'N/A')} → {result.get('hash_after', 'N/A')}")
            return {"success": True, "file": file_path, "diff": ""}
        else:
            print(f"[PIPELINE] ❌ Patch failed: {result.get('error', 'No changes')}")
            return {"success": False, "file": file_path, "error": result.get("error", "No changes")}
        
        # Debug: print before content
        print(f"[PIPELINE] DEBUG: File: {full_path}")
        print(f"[PIPELINE] DEBUG: File exists: {full_path.exists()}")
        print(f"[PIPELINE] DEBUG: Before content length: {len(before)}")
        print(f"[PIPELINE] DEBUG: After content length: {len(after)}")
        print(f"[PIPELINE] DEBUG: Strategy: {strategy}")
        print(f"[PIPELINE] DEBUG: Before first 100 chars: {before[:100]}...")
        print(f"[PIPELINE] DEBUG: After first 100 chars: {after[:100]}...")
        
        if verify_result["success"] and verify_result["content_changed"]:
            # Apply patch
            full_path.write_text(after)
            print(f"[PIPELINE] ✅ Patch applied: {file_path}")
            print(f"[PIPELINE]    Hash: {verify_result['hash_before']} → {verify_result['hash_after']}")
            return {"success": True, "file": file_path, "diff": verify_result["diff"]}
        else:
            print(f"[PIPELINE] ❌ Patch verification failed: {verify_result.get('error', 'No changes')}")
            if not verify_result["success"]:
                print(f"[PIPELINE]    Verification success: {verify_result['success']}")
            if not verify_result["content_changed"]:
                print(f"[PIPELINE]    Content changed: {verify_result['content_changed']}")
                print(f"[PIPELINE]    Hash before: {verify_result.get('hash_before', 'N/A')}")
                print(f"[PIPELINE]    Hash after: {verify_result.get('hash_after', 'N/A')}")
            return {"success": False, "file": file_path, "error": verify_result.get("error", "No changes")}

    def _apply_strategy(self, strategy: str, content: str, error_info: Dict) -> str:
        """Apply strategy to content"""
        if strategy == "fix_sys_path":
            # Tambahkan sys.path yang benar di AWAL file
            lines = content.splitlines()
            new_lines = []
            # Tambahkan sys.path di awal
            new_lines.append('import sys')
            new_lines.append('import os')
            new_lines.append('sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))')
            new_lines.append('')
            # Tambahkan sisa content
            for line in lines:
                if 'sys.path.insert' in line:
                    continue
                new_lines.append(line)
            return "\n".join(new_lines)
        
        elif strategy == "fix_import_statement":
            # Ubah import menjadi relative
            return content.replace('from sicuan.core.token_scorer import', 'from ...core.token_scorer import')
        
        elif strategy == "fix_pythonpath":
            # Tambahkan PYTHONPATH
            return content
        
        return content


# Singleton
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = AutoRepairPipeline()
    return _pipeline
