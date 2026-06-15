"""
agents/coder_agent.py - Code generation agent
Auto-strips all AI artifacts from output
"""
import re
from typing import Dict, List
from agents.base_agent import BaseAgent
from core.models import AgentRole, ProjectPlan, CodeFile


CODER_SYSTEM = """You are an elite Python software engineer.
Write complete, production-quality, immediately runnable Python code.

ABSOLUTE RULES:
1. Output ONLY raw Python code - nothing else
2. NO markdown fences (no ```)
3. NO <think> tags or any XML tags
4. NO explanations or comments outside code
5. COMPLETE implementation - no TODO, no pass, no placeholders
6. All imports at top
7. Proper error handling throughout
"""


class CoderAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.CODER, CODER_SYSTEM)

    def run(self, input: Dict, context: Dict = None) -> List[CodeFile]:
        plan: ProjectPlan = input.get("plan")
        if not plan:
            raise ValueError("CoderAgent requires a ProjectPlan")

        self._log(f"Generating {len(plan.files_to_create)} files for: {plan.project_name}")

        generated_files = []
        file_contents = {}

        for file_info in plan.files_to_create:
            file_path = file_info["path"] if isinstance(file_info, dict) else file_info.path
            file_desc = file_info.get("description", "") if isinstance(file_info, dict) else file_info.description

            self._log(f"  Writing: {file_path}")

            code = self._generate_file(plan, file_path, file_desc, file_contents)

            code_file = CodeFile(
                path=file_path,
                content=code,
                language=self._detect_language(file_path),
                description=file_desc,
            )

            generated_files.append(code_file)
            file_contents[file_path] = code[:500]

        return generated_files

    def _generate_file(self, plan, file_path, file_description, existing_files) -> str:
        context_info = ""

        if existing_files:
            context_info = "\n\nALREADY GENERATED FILES:\n"
            for fp, fc in list(existing_files.items())[:3]:
                context_info += f"\n--- {fp} ---\n{fc[:300]}\n"

        messages = [{
            "role": "user",
            "content": (
                f"Generate complete Python code for: {file_path}\n"
                f"PURPOSE: {file_description}\n\n"
                f"PROJECT: {plan.project_name}\n"
                f"DESCRIPTION: {plan.description}\n"
                f"TECH STACK: {', '.join(plan.tech_stack)}\n"
                f"DEPENDENCIES: {', '.join(plan.dependencies)}\n"
                f"ALL FILES: {', '.join([f['path'] if isinstance(f, dict) else f.path for f in plan.files_to_create])}\n"
                f"{context_info}\n\n"
                f"Output ONLY raw Python code. No markdown. No think tags."
            )
        }]

        code = self._chat(messages, temperature=0.2, max_tokens=8192)
        return self._clean_code(code)

    def generate_single_file(self, description: str, context: str = "") -> str:
        messages = [{
            "role": "user",
            "content": f"Write complete Python code for: {description}\n{context}\nRaw Python only."
        }]
        return self._clean_code(self._chat(messages, temperature=0.2, max_tokens=8192))

    def _clean_code(self, code: str) -> str:
        from runtime.ast_validator import ast_validator
        return ast_validator.clean_code(code)

    def _detect_language(self, file_path: str) -> str:
        ext = file_path.rsplit(".", 1)[-1].lower()
        return {"py": "python", "js": "javascript", "sh": "bash", "ts": "typescript"}.get(ext, "text")


coder_agent = CoderAgent()
