"""
swarm/swarm_engine.py - Parallel agent swarm with voting consensus
"""
import concurrent.futures
import json
from typing import List, Dict, Any
from core.logger import logger, console
from core.models import ProjectPlan


class SwarmEngine:
    """
    Runs multiple coder agents in parallel with different temperatures/approaches,
    then uses a voting system to select the best solution.
    """
    def __init__(self, num_agents: int = 3):
        self.num_agents = num_agents

    def parallel_generate(self, plan: ProjectPlan, user_request: str) -> List[Dict]:
        """Generate multiple solutions in parallel"""
        console.print(f"[agent.critic]🐝 SWARM: Spawning {self.num_agents} parallel agents...[/agent.critic]")

        temperatures = [0.1, 0.4, 0.7][:self.num_agents]
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_agents) as executor_pool:
            futures = {
                executor_pool.submit(self._generate_solution, plan, user_request, temp, i): i
                for i, temp in enumerate(temperatures)
            }

            for future in concurrent.futures.as_completed(futures):
                agent_id = futures[future]
                try:
                    result = future.result()
                    results.append({"agent_id": agent_id, "files": result, "score": 0})
                    console.print(f"[agent.coder]  Agent #{agent_id} completed[/agent.coder]")
                except Exception as e:
                    logger.error(f"Swarm agent #{agent_id} failed: {e}")

        return results

    def _generate_solution(self, plan: ProjectPlan, request: str, temperature: float, agent_id: int) -> List:
        """Generate a single solution with given temperature"""
        from agents.coder_agent import CoderAgent
        agent = CoderAgent()
        # Override temperature by modifying the agent temporarily
        original_chat = agent._chat
        def temp_chat(messages, **kwargs):
            kwargs["temperature"] = temperature
            return original_chat(messages, **kwargs)
        agent._chat = temp_chat
        return agent.run({"plan": plan})

    def vote_best(self, solutions: List[Dict], user_request: str) -> List:
        """Score each solution and return the best one"""
        if not solutions:
            return []
        if len(solutions) == 1:
            return solutions[0]["files"]

        console.print(f"[agent.critic]🗳️  Voting on {len(solutions)} solutions...[/agent.critic]")

        from core.llm_client import llm

        best_idx = 0
        best_score = -1

        for i, sol in enumerate(solutions):
            files = sol["files"]
            code_sample = ""
            for f in files[:2]:
                code_sample += f"\n=== {f.path} ===\n{f.content[:800]}\n"

            messages = [{
                "role": "user",
                "content": f"""Score this solution (0-100) for requirement: "{user_request}"

{code_sample}

Reply with only a JSON object: {{"score": 85, "reason": "brief reason"}}"""
            }]

            try:
                response = llm.chat(messages=messages, temperature=0.1, max_tokens=200, json_mode=True)
                data = json.loads(response)
                score = data.get("score", 0)
                solutions[i]["score"] = score
                console.print(f"  Agent #{sol['agent_id']}: score={score}")
                if score > best_score:
                    best_score = score
                    best_idx = i
            except Exception as e:
                logger.warning(f"Voting failed for agent {i}: {e}")

        winner = solutions[best_idx]
        console.print(f"[status.success]🏆 Winner: Agent #{winner['agent_id']} (score: {winner['score']})[/status.success]")
        return winner["files"]


swarm_engine = SwarmEngine()
