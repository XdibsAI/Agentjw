"""
agents/reviewer_agent.py - Code quality and correctness reviewer
"""
import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from core.models import AgentRole, CodeFile, ExecutionResult


REVIEWER_SYSTEM = """You are an expert code reviewer and software quality engineer.
Your job is to review generated code and execution results for quality and correctness.

When reviewing, you MUST respond with JSON in this format:
{
  "passed": true/false,
  "score": 0-100,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1"],
  "summary": "brief review summary"
}

Check for:
- Syntax errors and logic bugs
- Missing imports or undefined references
- Incomplete implementations (TODO, pass, ...)
- Error handling gaps
- Security issues
- Logical correctness vs requirements
"""


class ReviewerAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.REVIEWER, REVIEWER_SYSTEM)

    def run(self, input: Dict, context: Dict = None) -> Dict:
        files: List[CodeFile] = input.get("files", [])
        execution_result: ExecutionResult = input.get("execution_result")
        original_request: str = input.get("original_request", "")

        self._log(f"Reviewing {len(files)} files...")

        review_text = self._build_review_text(files, execution_result, original_request)

        messages = [
            {"role": "user", "content": review_text}
        ]

        response = self._chat(messages, temperature=0.2, max_tokens=16000, json_mode=True)

        try:
            review = json.loads(response)
            passed = review.get("passed", False)
            score = review.get("score", 0)
            self._log(f"Review {'PASSED' if passed else 'FAILED'} (score: {score}/100)")
            if review.get("issues"):
                for issue in review["issues"][:3]:
                    self._log(f"  Issue: {issue}")
            return review
        except json.JSONDecodeError:
            return {
                "passed": execution_result.success if execution_result else False,
                "score": 50,
                "issues": ["Could not parse review response"],
                "suggestions": [],
                "summary": "Review parsing failed, using execution result",
            }

    def _build_review_text(self, files: List[CodeFile], result: ExecutionResult, request: str) -> str:
        text = f"Review this code for the requirement: '{request}'\n\n"

        for f in files[:5]:
            text += f"=== {f.path} ===\n{f.content[:2000]}\n\n"

        if result:
            text += f"\n=== EXECUTION RESULT ===\n"
            text += f"Success: {result.success}\n"
            if result.stdout:
                text += f"Output:\n{result.stdout[:500]}\n"
            if result.stderr:
                text += f"Errors:\n{result.stderr[:500]}\n"

        text += "\nProvide your review as JSON."
        return text


reviewer_agent = ReviewerAgent()
