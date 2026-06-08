"""
agents/critic_agent.py - Adversarial quality evaluator
"""
import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from core.models import AgentRole, CodeFile


CRITIC_SYSTEM = """You are an adversarial code critic. Your job is to find EVERY possible flaw, 
weakness, or improvement opportunity in generated code.

Be ruthless but constructive. Look for:
- Edge cases not handled
- Performance bottlenecks  
- Security vulnerabilities
- Design flaws
- Missing functionality
- Incorrect logic

Respond with JSON:
{
  "critical_issues": ["must-fix issues"],
  "warnings": ["should-fix issues"],
  "improvements": ["nice-to-have"],
  "overall_quality": "poor/fair/good/excellent",
  "recommendation": "approve/revise/reject"
}
"""


class CriticAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.CRITIC, CRITIC_SYSTEM)

    def run(self, input: Dict, context: Dict = None) -> Dict:
        files: List[CodeFile] = input.get("files", [])
        request: str = input.get("original_request", "")
        execution_success: bool = input.get("execution_success", False)

        if not files:
            return {"recommendation": "approve", "overall_quality": "fair"}

        self._log("Running adversarial critique...")

        code_text = ""
        for f in files[:4]:
            code_text += f"\n=== {f.path} ===\n{f.content[:1500]}\n"

        messages = [
            {
                "role": "user",
                "content": f"""Critically evaluate this code for requirement: "{request}"

Execution success: {execution_success}

CODE:
{code_text}

Find ALL issues. Respond with JSON."""
            }
        ]

        response = self._chat(messages, temperature=0.4, max_tokens=1500, json_mode=True)

        try:
            critique = json.loads(response)
            quality = critique.get("overall_quality", "fair")
            rec = critique.get("recommendation", "approve")
            self._log(f"Critique: {quality} → {rec}")
            if critique.get("critical_issues"):
                for issue in critique["critical_issues"][:2]:
                    self._log(f"  CRITICAL: {issue}")
            return critique
        except Exception:
            return {
                "critical_issues": [],
                "warnings": [],
                "improvements": [],
                "overall_quality": "fair",
                "recommendation": "approve" if execution_success else "revise",
            }


critic_agent = CriticAgent()
