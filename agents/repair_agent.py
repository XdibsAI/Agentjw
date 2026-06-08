"""
agents/repair_agent.py - Automatic error detection and fix generation
"""
import re
from typing import Dict, List, Optional
from agents.base_agent import BaseAgent
from core.models import AgentRole, CodeFile, ExecutionResult


REPAIR_SYSTEM = """You are an elite Python debugger.
Fix broken code based on error messages.

RULES:
1. Analyze error carefully
2. Output COMPLETE fixed file
3. NO markdown fences
4. NO <think> tags
5. Fix ALL errors, not just first one
6. Ensure all imports are correct
7. Raw Python code only
"""


class RepairAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.REPAIR, REPAIR_SYSTEM)

    def run(self, input: Dict, context: Dict = None) -> List[CodeFile]:
        files: List[CodeFile] = input.get("files", [])
        execution_result: ExecutionResult = input.get("execution_result")
        original_request: str = input.get("original_request", "")
        attempt: int = input.get("attempt", 1)

        if not execution_result or execution_result.success:
            return files

        error_type = execution_result.error_type or "RuntimeError"
        stderr = execution_result.stderr
        self._log(f"Repair attempt #{attempt} - {error_type}")

        known_fixes = self.memory.get_error_fixes(error_type)
        known_fix_context = ""
        if known_fixes:
            known_fix_context = f"\nKNOWN FIXES:\n" + "\n".join(f"- {f['fix'][:150]}" for f in known_fixes[:2])

        faulty_file = self._identify_faulty_file(files, stderr)
        repaired_files = list(files)

        if faulty_file:
            fixed_code = self._repair_file(
                file=faulty_file,
                stderr=stderr,
                error_type=error_type,
                all_files=files,
                original_request=original_request,
                known_fix_context=known_fix_context,
            )
            for i, f in enumerate(repaired_files):
                if f.path == faulty_file.path:
                    repaired_files[i] = CodeFile(
                        path=f.path,
                        content=fixed_code,
                        language=f.language,
                        description=f.description + f" [repair#{attempt}]",
                    )
                    break
            self.memory.log_error(
                error_type=error_type,
                error_message=stderr[:500],
                fix_applied=f"Repaired {faulty_file.path} attempt {attempt}",
                success=False,
                context=original_request[:200],
            )
        return repaired_files

    def _repair_file(self, file: CodeFile, stderr: str, error_type: str,
                     all_files: List[CodeFile], original_request: str,
                     known_fix_context: str) -> str:
        other_ctx = ""
        for f in all_files:
            if f.path != file.path:
                other_ctx += f"\n--- {f.path} ---\n{f.content[:400]}\n"

        messages = [{
            "role": "user",
            "content": (
                f"Fix this Python file.\n\n"
                f"REQUIREMENT: {original_request}\n"
                f"FILE: {file.path}\n"
                f"ERROR TYPE: {error_type}\n"
                f"ERROR:\n{stderr}\n"
                f"{known_fix_context}\n\n"
                f"CURRENT CODE:\n{file.content}\n\n"
                f"OTHER FILES:\n{other_ctx}\n\n"
                f"Output ONLY the complete fixed Python code. No markdown."
            )
        }]
        fixed = self._chat(messages, temperature=0.1, max_tokens=8192)
        from runtime.ast_validator import ast_validator
        return ast_validator.clean_code(fixed)

    def _identify_faulty_file(self, files: List[CodeFile], stderr: str) -> Optional[CodeFile]:
        for file in files:
            if file.path in stderr:
                return file
        for file in files:
            if file.path == "main.py":
                return file
        return files[0] if files else None


repair_agent = RepairAgent()
