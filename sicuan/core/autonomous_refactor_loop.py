import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class AutonomousRefactorLoop:


    def __init__(self):

        self.running = True

        self.refactor_executed = False



    def generate_tasks(self):

        from sicuan.core.strategy_executor import StrategyExecutor

        executor = StrategyExecutor()

        result = executor.push_to_queue()

        print(
            "[TASK GENERATOR]",
            result
        )

        return result



    def run_once(self):

        print(
            "\n[AUTONOMOUS] cycle start"
        )


        from sicuan.core.task_executor import TaskExecutor


        executor = TaskExecutor()


        executed = 0


        result = executor.execute_next()


        print(
            "[TASK RESULT]",
            result


        )


        if result.get("status") == "idle":

            executed = 0

        else:

            executed += 1


        action = result.get(
            "action",
            ""
        )


        recommendations = result.get(
            "recommendations",
            []
        )


        needs_refactor = False


        if action in (
            "strategy_ast_analysis",
            "strategy_optimization"
        ):

            if result.get(
                "quality_score",
                0
            ) < 90:

                needs_refactor = True


        if needs_refactor and not self.refactor_executed:

            self.refactor_executed = True

            print(
                "[AUTONOMOUS] triggering refactor engine"
            )

            from sicuan.core.refactor_engine import RefactorEngine

            engine = RefactorEngine()

            refactor = engine.execute_safe_plan()

            print(
                "[REFACTOR RESULT]",
                refactor
            )


        if executed == 0:

            print(
                "[AUTONOMOUS] generating tasks"
            )

            generated = self.generate_tasks()

            if (
                generated.get("added", [])
                ==
                []
                and
                generated.get("queue_size", 0)
                ==
                0
            ):
                print(
                    "[AUTONOMOUS] no new tasks generated, stopping cycle"
                )
                return True

            print(
                "[TASK GENERATED]",
                generated
            )

            from sicuan.core.task_executor import TaskExecutor

            executor = TaskExecutor()

            while True:

                result = executor.execute_next()

                print(
                    "[TASK EXECUTED AFTER GENERATE]",
                    result
                )

                recommendations = result.get(
                    "recommendations",
                    []
                )

                if recommendations:

                    history_file = ROOT / "memory/execution_history.json"

                    completed_tasks = set()

                    if history_file.exists():
                        import json
                        try:
                            history = json.loads(
                                history_file.read_text()
                            )
                            completed_tasks = {
                                h.get("task", "").lower()
                                for h in history
                            }
                        except Exception:
                            pass

                    recommendations = [
                        r for r in recommendations
                        if r.lower() not in completed_tasks
                    ]

                    if recommendations:

                        print(
                            "[AUTONOMOUS] injecting recommendations",
                            recommendations
                        )

                        from sicuan.core.strategy_executor import StrategyExecutor

                        feedback = StrategyExecutor().inject_tasks(
                            recommendations
                        )

                        print(
                            "[FEEDBACK QUEUE]",
                            feedback
                        )

                if result.get("status") == "idle":
                    break


        return True




    def run_forever(self):


        while self.running:

            try:

                self.run_once()


            except Exception as e:

                print(
                    "[ERROR]",
                    e
                )


            time.sleep(
                30
            )



if __name__ == "__main__":


    AutonomousRefactorLoop().run_forever()

