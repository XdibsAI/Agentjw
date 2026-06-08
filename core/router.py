import os

class ModelRouter:

    def route(self,task:str):

        task=task.lower()

        if "debug" in task:
            return os.getenv(
                "DEBUG_MODEL",
                "deepseek/deepseek-chat"
            )

        if "review" in task:
            return os.getenv(
                "REVIEW_MODEL",
                "anthropic/claude-sonnet-4"
            )

        if "code" in task:
            return os.getenv(
                "CODE_MODEL",
                "openai/gpt-5"
            )

        return os.getenv(
            "DEFAULT_MODEL",
            "openai/gpt-5-mini"
        )
