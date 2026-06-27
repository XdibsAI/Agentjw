from sicuan.brain import SiCuanBrain


class LLMTaskExecutor:

    def __init__(self):
        self.brain = SiCuanBrain()

    def run_cycle(self):

        mission = """
Lakukan PROFITABILITY AUDIT untuk godmeme_bot.
Fokus mencari bug profit.
"""

        try:

            decision = self.brain.think_and_respond(mission)

            plan = decision.get("plan", [])

            results = []

            if plan:

                for step in plan[:5]:

                    action = step.get("action")
                    target = step.get("action_target", "")

                    try:

                        result = self.brain.execute_action(
                            action,
                            target,
                            mission,
                            "autonomous"
                        )

                        results.append({
                            "action": action,
                            "target": target,
                            "result": str(result)[:3000]
                        })

                    except Exception as e:

                        results.append({
                            "action": action,
                            "target": target,
                            "error": str(e)
                        })

            else:

                action = decision.get("action")
                target = decision.get("action_target")

                if action and str(action).lower() != "null":

                    result = self.brain.execute_action(
                        action,
                        target,
                        mission,
                        "autonomous"
                    )

                    results.append({
                        "action": action,
                        "target": target,
                        "result": str(result)[:3000]
                    })

            return {
                "success": True,
                "results": results
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e)
            }
