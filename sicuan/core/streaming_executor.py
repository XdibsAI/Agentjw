"""
Streaming Tool Executor — Parallel tool execution
"""
import asyncio
import threading
from typing import Dict, List, Callable, Any
from concurrent.futures import ThreadPoolExecutor


class StreamingToolExecutor:
    """Eksekusi tool secara parallel dengan streaming"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self._results = {}
        self._progress = {}

    def execute_parallel(self, tools: List[Dict]) -> Dict:
        """
        Execute multiple tools in parallel
        tools: [{"name": "analyze_project", "params": {...}}, ...]
        """
        if not tools:
            return {"results": [], "errors": []}

        futures = []
        results = []
        errors = []

        for tool in tools:
            name = tool.get("name")
            params = tool.get("params", {})
            
            # Submit task
            future = self.executor.submit(self._run_tool, name, params)
            futures.append((name, future))

        # Collect results
        for name, future in futures:
            try:
                result = future.result(timeout=60)
                results.append({"name": name, "result": result, "success": True})
            except Exception as e:
                errors.append({"name": name, "error": str(e), "success": False})

        return {
            "results": results,
            "errors": errors,
            "total": len(tools),
            "success_count": len(results),
            "error_count": len(errors)
        }

    def _run_tool(self, name: str, params: Dict) -> Any:
        """Run a single tool"""
        # Import tool registry
        from sicuan.core.action_registry import get_action_registry
        registry = get_action_registry()
        action = registry.get(name)
        if action:
            return action.execute(params)
        raise Exception(f"Tool '{name}' not found")


_executor = None


def get_streaming_executor() -> StreamingToolExecutor:
    global _executor
    if _executor is None:
        _executor = StreamingToolExecutor()
    return _executor
