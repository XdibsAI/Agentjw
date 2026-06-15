"""
SiCuan Memory Engine
Cuan bisa baca, pahami, dan ingat semua yang pernah terjadi
Bukan session-based — truly persistent long-term memory
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional

DB_PATH = Path("/home/dibs/agentjw/memory/agentjw.db")
SICUAN_MEMORY = Path("/home/dibs/agentjw/sicuan/memory")
SICUAN_MEMORY.mkdir(exist_ok=True)


class MemoryEngine:
    def __init__(self):
        self._conn = None

    def conn(self):
        if not self._conn:
            self._conn = sqlite3.connect(DB_PATH)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    # ── SELF AWARENESS ─────────────────────────────────────────────
    def who_am_i(self) -> str:
        """Cuan baca dirinya sendiri — projects, history, capabilities"""
        c = self.conn()

        projects = c.execute("""
            SELECT name, status, tool_type, created_at, description
            FROM managed_projects ORDER BY created_at DESC
        """).fetchall()

        work = c.execute("""
            SELECT project_name, action, detail, timestamp
            FROM work_log ORDER BY timestamp DESC LIMIT 20
        """).fetchall()

        chat_count = c.execute("SELECT COUNT(*) FROM chat_history").fetchone()[0]
        errors = c.execute("SELECT error_type, COUNT(*) as c FROM error_registry GROUP BY error_type").fetchall()

        # Build self-awareness summary
        project_summary = []
        for p in projects:
            project_summary.append(
                f"- {p['name']} ({p['tool_type']}) — {p['status']} | {p['created_at'][:10]}"
            )

        work_summary = []
        for w in work[:10]:
            work_summary.append(f"- [{w['timestamp'][:16]}] {w['project_name']}: {w['action']} — {str(w['detail'])[:60]}")

        identity = f"""=== SIAPA CUAN ===
Saya SiCuan, AI partner bisnis yang sudah aktif sejak 2026-06-04.

PROJECTS YANG PERNAH SAYA BUAT/KELOLA ({len(projects)} total):
{chr(10).join(project_summary)}

AKTIVITAS TERAKHIR:
{chr(10).join(work_summary)}

STATISTIK:
- Total percakapan tersimpan: {chat_count:,}
- Error yang pernah ditangani: {sum(e['c'] for e in errors)}
- Project files tersimpan: {c.execute('SELECT COUNT(*) FROM project_files').fetchone()[0]}

KEMAMPUAN SAYA:
- Build project (trading bot, YouTube tools, Telegram bot, Flask API, dll)
- Repair project yang error
- Generate video package (script, scenes, voice, thumbnails)
- Monitor trading bot Godmeme
- Analisa strategi dan data
- Manage project files secara langsung
- Self-patch jika ada yang rusak
"""
        return identity

    # ── LONG TERM MEMORY ───────────────────────────────────────────
    def recall_conversation(self, days: int = 7, limit: int = 50) -> List[Dict]:
        """Ambil percakapan N hari terakhir"""
        c = self.conn()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        rows = c.execute("""
            SELECT session_id, role, content, timestamp
            FROM chat_history
            WHERE timestamp >= ?
            ORDER BY timestamp DESC LIMIT ?
        """, (cutoff, limit)).fetchall()
        return [dict(r) for r in rows]

    def recall_by_topic(self, topic: str, limit: int = 10) -> List[Dict]:
        """Cari percakapan berdasarkan topik"""
        c = self.conn()
        rows = c.execute("""
            SELECT session_id, role, content, timestamp
            FROM chat_history
            WHERE content LIKE ?
            ORDER BY timestamp DESC LIMIT ?
        """, (f"%{topic}%", limit)).fetchall()
        return [dict(r) for r in rows]

    def get_project_full_context(self, project_name: str) -> Dict:
        """Ambil full context sebuah project — files, logs, history"""
        c = self.conn()

        project = c.execute("""
            SELECT * FROM managed_projects
            WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1
        """, (f"%{project_name}%",)).fetchone()

        if not project:
            return {"error": f"Project '{project_name}' tidak ditemukan"}

        proj_dict = dict(project)

        # Files
        files = c.execute("""
            SELECT file_path, language, updated_at
            FROM project_files WHERE project_id = ?
        """, (proj_dict["id"],)).fetchall()
        proj_dict["files_list"] = [dict(f) for f in files]

        # Work log
        logs = c.execute("""
            SELECT action, detail, status, timestamp
            FROM work_log WHERE project_id = ?
            ORDER BY timestamp DESC LIMIT 10
        """, (proj_dict["id"],)).fetchall()
        proj_dict["work_history"] = [dict(l) for l in logs]

        return proj_dict

    def summarize_period(self, days: int = 30) -> str:
        """Buat ringkasan aktivitas N hari terakhir — seperti Dudu bisa recap 1 bulan"""
        c = self.conn()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Projects dibuat periode ini
        new_projects = c.execute("""
            SELECT name, tool_type, status, created_at
            FROM managed_projects WHERE created_at >= ?
            ORDER BY created_at
        """, (cutoff,)).fetchall()

        # Work done
        work_done = c.execute("""
            SELECT project_name, action, COUNT(*) as count
            FROM work_log WHERE timestamp >= ?
            GROUP BY project_name, action
        """, (cutoff,)).fetchall()

        # Errors fixed
        errors_fixed = c.execute("""
            SELECT error_type, COUNT(*) as count
            FROM error_registry WHERE timestamp >= ?
            GROUP BY error_type
        """, (cutoff,)).fetchall()

        summary = f"""=== RINGKASAN {days} HARI TERAKHIR ===

PROJECT BARU ({len(new_projects)}):
"""
        for p in new_projects:
            summary += f"  • {p['name']} ({p['tool_type']}) — {p['status']} [{p['created_at'][:10]}]\n"

        summary += f"\nAKTIVITAS:\n"
        for w in work_done:
            summary += f"  • {w['project_name']}: {w['action']} ({w['count']}x)\n"

        if errors_fixed:
            summary += f"\nERROR YANG DITANGANI:\n"
            for e in errors_fixed:
                summary += f"  • {e['error_type']}: {e['count']}x\n"

        return summary

    # ── SELF WRITE ─────────────────────────────────────────────────
    def save_insight(self, topic: str, content: str, importance: float = 0.7):
        """Cuan simpan insight/learning ke memorinya sendiri"""
        c = self.conn()
        now = datetime.now().isoformat()
        c.execute("""
            INSERT INTO memories (type, content, metadata, importance, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ("sicuan_insight", content, json.dumps({"topic": topic}), importance, now, now))
        self.conn().commit()

    def recall_insights(self, topic: str = None, limit: int = 10) -> List[Dict]:
        """Ambil insights yang pernah Cuan simpan"""
        c = self.conn()
        if topic:
            rows = c.execute("""
                SELECT * FROM memories
                WHERE type = 'sicuan_insight' AND content LIKE ?
                ORDER BY importance DESC, created_at DESC LIMIT ?
            """, (f"%{topic}%", limit)).fetchall()
        else:
            rows = c.execute("""
                SELECT * FROM memories WHERE type = 'sicuan_insight'
                ORDER BY importance DESC, created_at DESC LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]

    def patch_self(self, file_path: str, old_code: str, new_code: str, reason: str) -> bool:
        """
        Cuan edit kodenya sendiri — self-modification
        Hanya boleh edit file di /home/dibs/agentjw/sicuan/
        """
        allowed_base = Path("/home/dibs/agentjw/sicuan")
        target = Path(file_path)

        if not str(target).startswith(str(allowed_base)):
            return False

        if not target.exists():
            return False

        content = target.read_text()
        if old_code not in content:
            return False

        # Backup dulu
        backup = target.with_suffix(f".bak.{int(datetime.now().timestamp())}")
        backup.write_text(content)

        # Apply patch
        new_content = content.replace(old_code, new_code, 1)
        target.write_text(new_content)

        # Log ke memory
        self.save_insight(
            topic="self_patch",
            content=f"Self-patched {file_path}: {reason}",
            importance=0.9
        )
        return True


memory_engine = MemoryEngine()
