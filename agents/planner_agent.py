"""
agents/planner_agent.py - Task decomposition and project planning agent
"""
import json
import uuid
from typing import Dict, Any
from agents.base_agent import BaseAgent
from core.models import AgentRole, ProjectPlan


PLANNER_SYSTEM = """You are an expert software architect and project planner.
Your job is to analyze user requests and create detailed, actionable project plans.

When given a task, you MUST respond with a valid JSON object following this exact schema:
{
  "project_name": "short_snake_case_name",
  "description": "what this project does",
  "tech_stack": ["python", "library1", "library2"],
  "directory_structure": {
    "folder/": ["file1.py", "file2.py"],
    "root": ["main.py", "requirements.txt"]
  },
  "files_to_create": [
    {"path": "main.py", "description": "entry point, does X"},
    {"path": "utils.py", "description": "helper functions for Y"}
  ],
  "dependencies": ["requests", "rich"],
  "entry_point": "main.py",
  "tasks": [
    "Create main.py with CLI interface",
    "Create utils.py with helper functions",
    "Test the complete flow"
  ]
}

Rules:
- Be specific and detailed
- Only include actually needed files
- List all pip packages needed
- Keep projects simple and runnable
- NO placeholders, NO pseudo-code descriptions
"""


class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentRole.PLANNER, PLANNER_SYSTEM)

    def run(self, input: str, context: Dict = None) -> ProjectPlan:
        self._log(f"Planning project for: {input[:80]}...")
        context = context or {}

        # Retrieve relevant past project memories
        past_projects = self.memory.recall(type="project", limit=3)
        memory_context = ""
        if past_projects:
            memory_context = "\n\nPAST SUCCESSFUL PROJECTS FOR REFERENCE:\n"
            for p in past_projects:
                memory_context += f"- {p['content'][:200]}\n"

        messages = [
            {
                "role": "user",
                "content": f"Create a detailed project plan for this request:\n\n{input}{memory_context}\n\nRespond ONLY with the JSON plan."
            }
        ]

        response = self._chat(messages, temperature=0.3, max_tokens=16000, json_mode=True)

        try:
            plan_data = json.loads(response)
            plan = ProjectPlan(**plan_data)
            self._log(f"Plan created: {plan.project_name} ({len(plan.files_to_create)} files)")
            return plan
        except (json.JSONDecodeError, Exception) as e:
            self._log(f"Plan parsing error: {e}, using fallback plan")
            return self._fallback_plan(input)

    def _fallback_plan(self, request: str) -> ProjectPlan:
        name = "_".join(request.lower().split()[:3]).replace("/", "")
        return ProjectPlan(
            project_name=name or "project",
            description=request,
            tech_stack=["python"],
            files_to_create=[
                {"path": "main.py", "description": "Main entry point"},
                {"path": "utils.py", "description": "Utility functions"},
            ],
            dependencies=[],
            entry_point="main.py",
            tasks=["Implement the complete solution in main.py"],
        )


planner_agent = PlannerAgent()
