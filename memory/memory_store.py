"""
memory/memory_store.py - GOD MODE persistent memory store
Tracks: chat, projects, errors, strategies, tasks, work logs
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from core.config import config
from core.logger import logger


class MemoryStore:
    def __init__(self):
        self.db_path = config.SQLITE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY, type TEXT NOT NULL, content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}', importance REAL DEFAULT 1.0,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL, timestamp TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS error_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT, error_type TEXT,
                error_message TEXT, fix_applied TEXT, success INTEGER DEFAULT 0,
                context TEXT, timestamp TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS managed_projects (
                id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT,
                project_dir TEXT, status TEXT DEFAULT 'pending',
                tool_type TEXT DEFAULT 'general',
                files TEXT DEFAULT '[]',
                tasks_completed TEXT DEFAULT '[]',
                tasks_pending TEXT DEFAULT '[]',
                errors_history TEXT DEFAULT '[]',
                notes TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS work_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                project_name TEXT,
                action TEXT NOT NULL,
                detail TEXT,
                status TEXT DEFAULT 'done',
                timestamp TEXT NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS project_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                content TEXT,
                language TEXT DEFAULT 'python',
                updated_at TEXT NOT NULL)""")
            conn.commit()
        logger.info(f"Memory store initialized at {self.db_path}")

    # ── Chat ──────────────────────────────────────────────────────
    def save_chat(self, session_id: str, role: str, content: str):
        if not content:  # guard: never insert NULL content
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO chat_history (session_id,role,content,timestamp) VALUES (?,?,?,?)",
                (session_id, role, content, datetime.now().isoformat()))
            conn.commit()

    def get_chat_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT role,content FROM chat_history WHERE session_id=? ORDER BY id DESC LIMIT ?",
                (session_id, limit)).fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def clear_chat_history(self, session_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chat_history WHERE session_id=?", (session_id,))
            conn.commit()

    # ── General Memory ────────────────────────────────────────────
    def store(self, type: str, content: str, metadata: Dict = None, importance: float = 1.0) -> str:
        mid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO memories (id,type,content,metadata,importance,created_at,updated_at) VALUES (?,?,?,?,?,?,?)",
                (mid, type, content, json.dumps(metadata or {}), importance, now, now))
            conn.commit()
        return mid

    def recall(self, type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            if type:
                rows = conn.execute("SELECT id,type,content,metadata,importance,created_at FROM memories WHERE type=? ORDER BY importance DESC,created_at DESC LIMIT ?",
                    (type, limit)).fetchall()
            else:
                rows = conn.execute("SELECT id,type,content,metadata,importance,created_at FROM memories ORDER BY importance DESC,created_at DESC LIMIT ?",
                    (limit,)).fetchall()
        return [{"id": r[0], "type": r[1], "content": r[2], "metadata": json.loads(r[3]), "importance": r[4], "created_at": r[5]} for r in rows]

    def search_memories(self, query: str, type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        # Keyword-based OR matching: split query into significant words
        # (len > 3) and match any of them, instead of requiring the whole
        # sentence to appear verbatim (which almost never happens).
        words = [w for w in query.lower().split() if len(w) > 3][:6]
        if not words:
            return self.recall(type=type, limit=limit)

        conditions = " OR ".join(["lower(content) LIKE ?"] * len(words))
        params: List = [f"%{w}%" for w in words]

        sql = f"SELECT id,type,content,metadata,importance,created_at FROM memories WHERE ({conditions})"
        if type:
            sql += " AND type=?"
            params.append(type)
        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(sql, params).fetchall()

        seen = set()
        results = []
        for r in rows:
            if r[0] in seen:
                continue
            seen.add(r[0])
            results.append({"id": r[0], "type": r[1], "content": r[2], "metadata": json.loads(r[3]), "importance": r[4], "created_at": r[5]})
        return results

    # ── Error Registry ────────────────────────────────────────────
    def log_error(self, error_type: str, error_message: str, fix_applied: str = "", success: bool = False, context: str = ""):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO error_registry (error_type,error_message,fix_applied,success,context,timestamp) VALUES (?,?,?,?,?,?)",
                (error_type, error_message, fix_applied, int(success), context, datetime.now().isoformat()))
            conn.commit()

    def get_error_fixes(self, error_type: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT error_message,fix_applied,success FROM error_registry WHERE error_type=? AND success=1 ORDER BY rowid DESC LIMIT 5",
                (error_type,)).fetchall()
        return [{"error": r[0], "fix": r[1], "success": bool(r[2])} for r in rows]

    # ── Managed Projects (GOD MODE) ───────────────────────────────
    def create_project(self, name: str, description: str, project_dir: str,
                       tool_type: str = "general", tasks: List[str] = None,
                       metadata: Dict = None) -> str:
        pid = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""INSERT INTO managed_projects
                (id,name,description,project_dir,status,tool_type,files,tasks_completed,tasks_pending,errors_history,notes,metadata,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (pid, name, description, project_dir, "in_progress", tool_type,
                 "[]", "[]", json.dumps(tasks or []), "[]", "", json.dumps(metadata or {}), now, now))
            conn.commit()
        self.log_work(pid, name, "project_created", f"Project '{name}' created at {project_dir}")
        return pid

    def update_project(self, project_id: str, **kwargs):
        now = datetime.now().isoformat()
        allowed = ["status", "files", "tasks_completed", "tasks_pending",
                   "errors_history", "notes", "metadata", "description"]
        updates = {k: v for k, v in kwargs.items() if k in allowed}
        if not updates:
            return
        for key, val in updates.items():
            if isinstance(val, (list, dict)):
                updates[key] = json.dumps(val)
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [now, project_id]
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE managed_projects SET {set_clause}, updated_at=? WHERE id=?", values)
            conn.commit()

    def get_project(self, project_id: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM managed_projects WHERE id=?", (project_id,)).fetchone()
        if not row:
            return None
        return self._row_to_project(row)

    def get_project_by_name(self, name: str) -> Optional[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT * FROM managed_projects WHERE name LIKE ?", (f"%{name}%",)).fetchone()
        if not row:
            return None
        return self._row_to_project(row)

    def list_projects(self, status: str = None, tool_type: str = None, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            if status and tool_type:
                rows = conn.execute("SELECT * FROM managed_projects WHERE status=? AND tool_type=? ORDER BY updated_at DESC LIMIT ?",
                    (status, tool_type, limit)).fetchall()
            elif status:
                rows = conn.execute("SELECT * FROM managed_projects WHERE status=? ORDER BY updated_at DESC LIMIT ?",
                    (status, limit)).fetchall()
            elif tool_type:
                rows = conn.execute("SELECT * FROM managed_projects WHERE tool_type=? ORDER BY updated_at DESC LIMIT ?",
                    (tool_type, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM managed_projects ORDER BY updated_at DESC LIMIT ?",
                    (limit,)).fetchall()
        return [self._row_to_project(r) for r in rows]

    def _row_to_project(self, row) -> Dict:
        cols = ["id","name","description","project_dir","status","tool_type",
                "files","tasks_completed","tasks_pending","errors_history",
                "notes","metadata","created_at","updated_at"]
        d = dict(zip(cols, row))
        for key in ["files","tasks_completed","tasks_pending","errors_history","metadata"]:
            try:
                d[key] = json.loads(d[key])
            except Exception:
                d[key] = []
        return d

    # ── Work Log ──────────────────────────────────────────────────
    def log_work(self, project_id: str, project_name: str, action: str, detail: str = "", status: str = "done"):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO work_log (project_id,project_name,action,detail,status,timestamp) VALUES (?,?,?,?,?,?)",
                (project_id, project_name, action, detail, status, datetime.now().isoformat()))
            conn.commit()

    def get_work_log(self, project_id: str = None, limit: int = 30) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            if project_id:
                rows = conn.execute("SELECT project_name,action,detail,status,timestamp FROM work_log WHERE project_id=? ORDER BY id DESC LIMIT ?",
                    (project_id, limit)).fetchall()
            else:
                rows = conn.execute("SELECT project_name,action,detail,status,timestamp FROM work_log ORDER BY id DESC LIMIT ?",
                    (limit,)).fetchall()
        return [{"project": r[0], "action": r[1], "detail": r[2], "status": r[3], "timestamp": r[4]} for r in rows]

    # ── Project Files ─────────────────────────────────────────────
    def save_project_file(self, project_id: str, file_path: str, content: str, language: str = "python"):
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute("SELECT id FROM project_files WHERE project_id=? AND file_path=?",
                (project_id, file_path)).fetchone()
            now = datetime.now().isoformat()
            if existing:
                conn.execute("UPDATE project_files SET content=?,language=?,updated_at=? WHERE project_id=? AND file_path=?",
                    (content, language, now, project_id, file_path))
            else:
                conn.execute("INSERT INTO project_files (project_id,file_path,content,language,updated_at) VALUES (?,?,?,?,?)",
                    (project_id, file_path, content, language, now))
            conn.commit()

    def get_project_files(self, project_id: str) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT file_path,content,language,updated_at FROM project_files WHERE project_id=?",
                (project_id,)).fetchall()
        return [{"path": r[0], "content": r[1], "language": r[2], "updated_at": r[3]} for r in rows]

    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            for table in ["memories", "chat_history", "error_registry"]:
                conn.execute(f"DELETE FROM {table}")
            conn.commit()
        logger.warning("Memory cleared (projects preserved)")


memory_store = MemoryStore()
