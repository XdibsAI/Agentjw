from pathlib import Path
import sqlite3
import json

ROOT = Path(__file__).resolve().parents[1]

DB = ROOT / "memory/projects_db/project_registry.db"


class ProjectRegistry:

    def __init__(self):
        DB.parent.mkdir(parents=True, exist_ok=True)

        self.db = sqlite3.connect(DB)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS projects(
            name TEXT PRIMARY KEY,
            path TEXT,
            database_path TEXT,
            log_path TEXT,
            status TEXT,
            metadata TEXT
        )
        """)

        self.db.commit()

    def upsert(
        self,
        name,
        path,
        database_path="",
        log_path="",
        status="unknown",
        metadata=None
    ):

        metadata = metadata or {}

        self.db.execute(
            """
            REPLACE INTO projects
            VALUES(?,?,?,?,?,?)
            """,
            (
                name,
                path,
                database_path,
                log_path,
                status,
                json.dumps(metadata)
            )
        )

        self.db.commit()

    def list_projects(self):

        cur = self.db.execute("""
        SELECT
            name,
            path,
            database_path,
            log_path,
            status
        FROM projects
        """)

        return cur.fetchall()

