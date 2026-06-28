class ProjectOperator:


    def build_context(self, report):

        return {

            "available_system":

            [
                "agents",
                "planner",
                "executor",
                "memory",
                "mcp",
                "projects",
                "tools"
            ],

            "audit":report

        }
