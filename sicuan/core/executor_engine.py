"""
Executor Engine - Queue → Resolve → Execute → Validate → Reflect → Runtime
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List

from sicuan.core.runtime_bus import RuntimeBus
from core.logger import logger

ROOT = Path("/home/dibs/agentjw")
QUEUE_FILE = ROOT / "memory" / "task_queue.json"


class ExecutorEngine:
    def __init__(self):
        self.runtime = RuntimeBus()
        self._ensure_queue_exists()
        self._task_counter = 0
    
    def _ensure_queue_exists(self):
        QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not QUEUE_FILE.exists():
            QUEUE_FILE.write_text("[]")
    
    def _load_queue(self) -> list:
        try:
            return json.loads(QUEUE_FILE.read_text())
        except:
            return []
    
    def _save_queue(self, queue: list):
        QUEUE_FILE.write_text(json.dumps(queue, indent=2, ensure_ascii=False))
    
    def _generate_task_id(self) -> str:
        self._task_counter += 1
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        short_uuid = uuid.uuid4().hex[:8]
        return f"task_{timestamp}_{short_uuid}_{self._task_counter:04d}"
    
    def create_task(self, action: str, target: str = "", user_request: str = "", 
                    priority: int = 1, context: dict = None) -> dict:
        return {
            "id": self._generate_task_id(),
            "action": action,
            "target": target,
            "user_request": user_request,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "context": context or {},
            "status": "pending"
        }
    
    def push_task(self, action: str, target: str = "", user_request: str = "",
                  priority: int = 1, context: dict = None) -> dict:
        task = self.create_task(action, target, user_request, priority, context)
        queue = self._load_queue()
        queue.append(task)
        self._save_queue(queue)
        return task
    
    def pop_task(self) -> Optional[dict]:
        queue = self._load_queue()
        if not queue:
            return None
        task = queue.pop(0)
        self._save_queue(queue)
        return task
    
    def queue_size(self) -> int:
        return len(self._load_queue())
    
    def clear_queue(self):
        self._save_queue([])
    
    def _resolve_handler(self, action: str) -> Optional[Callable]:
        try:
            if action == "scan_project":
                from sicuan.actions.scan_project import execute
                return execute
            elif action == "analyze_project":
                from sicuan.actions.analyze_project import execute
                return execute
            elif action == "trace_code":
                from sicuan.actions.trace_code import execute
                return execute
            elif action == "modify_logic":
                from sicuan.actions.modify_logic import execute
                return execute
            elif action == "repair_project":
                from sicuan.actions.repair_project import execute
                return execute
            elif action == "get_file":
                from sicuan.actions.get_file import execute
                return execute
            elif action == "project_summary":
                from sicuan.actions.project_summary import execute
                return execute
            elif action == "show_log":
                from sicuan.actions.show_log import execute
                return execute
            elif action == "godmeme_status":
                from sicuan.actions.godmeme_status import execute
                return execute
            elif action == "run_bot":
                from sicuan.actions.run_bot import execute
                return execute
            elif action == "list_projects":
                from sicuan.actions.list_projects import execute
                return execute
            elif action == "business_analysis":
                from sicuan.actions.business_analysis import execute
                return execute
            elif action == "gallery":
                from sicuan.actions.gallery import execute
                return execute
            elif action == "video_info":
                from sicuan.actions.video_info import execute
                return execute
            elif action == "build_project":
                from sicuan.actions.build_project import execute
                return execute
            elif action == "modify_project":
                from sicuan.actions.modify_project import execute
                return execute
            elif action == "autonomous_project":
                from sicuan.actions.autonomous_project import execute
                return execute
            else:
                return None
        except ImportError as e:
            logger.error(f"Failed to import handler for {action}: {e}")
            return None
    
    def _validate(self, result: dict) -> dict:
        if not result.get("success", False):
            return {
                "valid": False,
                "reason": result.get("error", "Unknown error"),
                "errors": result.get("errors", [])
            }
        if "data" not in result and "summary" not in result:
            return {
                "valid": False,
                "reason": "Result tidak memiliki data atau summary"
            }
        return {"valid": True}
    
    
    def _reflect(self, task: dict, result: dict, validation: dict) -> dict:
        is_valid = validation.get("valid", False)
        success = result.get("success", False)
        
        # Hitung confidence berdasarkan success + valid
        if success and is_valid:
            confidence = 0.95
            reason = "Execution successful"
        elif success and not is_valid:
            confidence = 0.60
            reason = "Execution returned but validation failed"
        elif not success and is_valid:
            confidence = 0.40
            reason = "Execution failed but validation passed"
        else:
            confidence = 0.20
            reason = "Execution failed"
        
        # Adjust based on duration
        duration = result.get("duration", 0)
        if duration > 10:
            confidence = max(0.1, confidence - 0.2)
        elif duration > 5:
            confidence = max(0.2, confidence - 0.1)
        
        return {
            "task_id": task.get("id"),
            "action": task.get("action"),
            "target": task.get("target"),
            "validation": validation,
            "confidence": confidence * 100,
            "should_retry": not is_valid,
            "reason": reason
        }
    
    def execute_next(self) -> Dict:
        import time
        start_time = time.time()
        
        task = self.pop_task()
        if not task:
            return {"success": False, "error": "Queue kosong", "queue_empty": True}

        action = task.get("action", "")
        handler = self._resolve_handler(action)

        if not handler:
            result = {"success": False, "error": f"Handler untuk '{action}' tidak ditemukan"}
        else:
            try:
                result = handler(task)
                if not result.get("success", False) and not result.get("error"):
                    result["error"] = result.get("summary", "Unknown error")
            except Exception as e:
                result = {"success": False, "error": str(e), "errors": [str(e)]}
        
        duration = time.time() - start_time
        result["duration"] = duration
        
        # Log jika duration terlalu lama
        if duration > 10:
            logger.warning(f"SLOW EXECUTION: {action} took {duration:.2f}s")
        elif duration > 60:
            logger.error(f"VERY SLOW EXECUTION: {action} took {duration:.2f}s - possible timeout/retry issue")
        
        validation = self._validate(result)
        reflection = self._reflect(task, result, validation)

        self.runtime.add_execution(task, result, duration)
        self.runtime.add_reflection(reflection)

        return {
            "success": result.get("success", False),
            "action": action,
            "summary": result.get("summary", ""),
            "data": result.get("data", {}),
            "error": result.get("error", ""),
            "errors": result.get("errors", []),
            "duration": duration,
            "reflection": reflection,
            "task": task,
            "validation": validation
        }
    def status(self) -> Dict:
        return {
            "queue_size": self.queue_size(),
            "stats": self.runtime.get_stats()
        }

    def _handle_api_error(self, error: Exception, retry_count: int = 0) -> Dict:
        """Handle API error dengan graceful fallback"""
        max_retries = 3
        if retry_count < max_retries:
            wait_time = 2 ** retry_count  # Exponential backoff
            logger.warning(f"API error, retrying in {wait_time}s... ({retry_count+1}/{max_retries})")
            time.sleep(wait_time)
            return self._retry_with_backoff(error, retry_count + 1)
        else:
            logger.error(f"API error after {max_retries} retries: {error}")
            return {
                "success": False,
                "error": f"API error after {max_retries} retries: {str(error)}",
                "fallback": True
            }

    def _retry_with_backoff(self, error: Exception, retry_count: int) -> Dict:
        """Retry dengan exponential backoff"""
        try:
            return self.execute_next()
        except Exception as e:
            return self._handle_api_error(e, retry_count)
