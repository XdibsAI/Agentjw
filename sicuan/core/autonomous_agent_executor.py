from pathlib import Path


class AutonomousAgentExecutor:

    def execute(
        self,
        logic_task
    ):

        try:

            from agents.specialist.logic_modifier import logic_modifier


            project = logic_task["project"]

            instruction = logic_task["instruction"]

            targets = logic_task.get(
                "targets",
                []
            )


            project_dir = Path(
                "projects"
            ) / project


            if not project_dir.exists():

                return {
                    "status": "FAILED",
                    "error": f"project not found: {project_dir}"
                }


            # Resolve abstract optimization goals
            # menjadi file nyata berdasarkan isi project

            py_files = list(
                project_dir.glob("*.py")
            )


            resolved_files = []

            keywords = []

            for t in targets:
                keywords.append(
                    str(t).lower()
                )


            for f in py_files:

                name = f.name.lower()

                try:
                    content = f.read_text(
                        errors="replace"
                    ).lower()

                except Exception:
                    continue


                score = 0


                for key in keywords:

                    if key in name:
                        score += 3

                    if key in content:
                        score += 1


                # core trading files selalu kandidat optimizer
                if any(
                    x in name
                    for x in [
                        "strategy",
                        "sniper",
                        "risk",
                        "database",
                        "token"
                    ]
                ):
                    score += 2


                if score > 0:
                    resolved_files.append(
                        str(f)
                    )


            if not resolved_files:

                resolved_files = [
                    str(x)
                    for x in py_files
                    if x.name in [
                        "strategy.py",
                        "risk_manager.py",
                        "sniper.py"
                    ]
                ]


            result = logic_modifier.modify(
                str(project_dir),
                instruction,
                resolved_files
            )


            return {
                "status": "EXECUTED",
                "project": project,
                "path": str(project_dir),
                "resolved_targets": resolved_files,
                "result": result
            }


        except Exception as e:

            return {
                "status": "FAILED",
                "error": str(e)
            }
