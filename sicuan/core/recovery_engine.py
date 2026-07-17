"""
Recovery Engine — Checkpoint & Resume untuk workflow
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List


class RecoveryEngine:
    """Recovery Engine — Simpan checkpoint dan resume workflow"""

    def __init__(self):
        self.db_path = Path("/home/dibs/agentjw/memory/recovery.db")
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                name TEXT,
                status TEXT,
                created_at TEXT,
                updated_at TEXT,
                data TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS steps (
                id TEXT PRIMARY KEY,
                workflow_id TEXT,
                step_id TEXT,
                name TEXT,
                agent TEXT,
                action TEXT,
                status TEXT,
                result TEXT,
                error TEXT,
                started_at TEXT,
                completed_at TEXT,
                data TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT,
                step_index INTEGER,
                timestamp TEXT,
                data TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_workflow(self, workflow_data: Dict) -> str:
        """Simpan workflow ke database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        workflow_id = workflow_data.get("id")
        cursor.execute('''
            INSERT OR REPLACE INTO workflows (id, name, status, created_at, updated_at, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            workflow_id,
            workflow_data.get("name"),
            workflow_data.get("status"),
            workflow_data.get("created_at"),
            datetime.now().isoformat(),
            json.dumps(workflow_data)
        ))
        
        # Simpan steps
        for step in workflow_data.get("steps", []):
            cursor.execute('''
                INSERT OR REPLACE INTO steps 
                (id, workflow_id, step_id, name, agent, action, status, result, error, started_at, completed_at, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                f"{workflow_id}_{step.get('id')}",
                workflow_id,
                step.get("id"),
                step.get("name"),
                step.get("agent"),
                step.get("action"),
                step.get("status"),
                step.get("result"),
                step.get("error"),
                step.get("started_at"),
                step.get("completed_at"),
                json.dumps(step)
            ))
        
        conn.commit()
        conn.close()
        return workflow_id

    def save_checkpoint(self, workflow_id: str, step_index: int, data: Dict):
        """Simpan checkpoint"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO checkpoints (workflow_id, step_index, timestamp, data)
            VALUES (?, ?, ?, ?)
        ''', (
            workflow_id,
            step_index,
            datetime.now().isoformat(),
            json.dumps(data)
        ))
        conn.commit()
        conn.close()

    def get_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Ambil workflow dari database"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM workflows WHERE id = ?', (workflow_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        workflow = json.loads(row["data"])
        workflow["_recovered"] = True
        
        # Ambil steps
        cursor.execute('SELECT * FROM steps WHERE workflow_id = ?', (workflow_id,))
        steps = []
        for s in cursor.fetchall():
            steps.append(json.loads(s["data"]))
        workflow["steps"] = steps
        
        # Ambil checkpoint terakhir
        cursor.execute('''
            SELECT * FROM checkpoints 
            WHERE workflow_id = ? 
            ORDER BY id DESC LIMIT 1
        ''', (workflow_id,))
        checkpoint = cursor.fetchone()
        if checkpoint:
            workflow["_checkpoint"] = json.loads(checkpoint["data"])
            workflow["_checkpoint_step"] = checkpoint["step_index"]
        
        conn.close()
        return workflow

    def get_pending_workflows(self) -> List[Dict]:
        """Ambil semua workflow yang pending atau running"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM workflows 
            WHERE status IN ('pending', 'running', 'partial')
            ORDER BY created_at DESC
        ''')
        
        workflows = []
        for row in cursor.fetchall():
            workflow = json.loads(row["data"])
            workflow["_recovered"] = True
            workflows.append(workflow)
        
        conn.close()
        return workflows

    def recover_workflow(self, workflow_id: str) -> Optional[Dict]:
        """Recover workflow dari checkpoint terakhir"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # Tandai untuk resume
        workflow["_resume"] = True
        return workflow

    def get_summary(self) -> str:
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM workflows')
        total_workflows = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM workflows WHERE status IN ("pending", "running", "partial")')
        pending = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM checkpoints')
        total_checkpoints = cursor.fetchone()[0]
        
        conn.close()
        
        lines = []
        lines.append("🔄 **RECOVERY ENGINE SUMMARY**")
        lines.append("=" * 30)
        lines.append(f"📊 Total Workflows: {total_workflows}")
        lines.append(f"⏳ Pending/Running: {pending}")
        lines.append(f"📌 Checkpoints: {total_checkpoints}")
        return "\n".join(lines)


_recovery = None


def get_recovery_engine() -> RecoveryEngine:
    global _recovery
    if _recovery is None:
        _recovery = RecoveryEngine()
    return _recovery
