from pathlib import Path
import sqlite3

DB = "memory/projects_db/projects.db"


class ProjectIndexer:

    def __init__(self):
        Path("memory/projects_db").mkdir(
            parents=True,
            exist_ok=True
        )

        self.db = sqlite3.connect(DB)

        self.db.execute("""
        CREATE TABLE IF NOT EXISTS files(
            path TEXT PRIMARY KEY,
            content TEXT
        )
        """)

    def index_project(self, root):

        root = Path(root)

        for file in root.rglob("*.py"):

            try:

                content = file.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                self.db.execute(
                    "REPLACE INTO files VALUES(?,?)",
                    (str(file), content)
                )

            except Exception:
                pass

        self.db.commit()

    def search(self, query):

        words = [
            w.strip()
            for w in query.lower().split()
            if len(w.strip()) > 1
        ]

        if not words:
            return []

        where = " OR ".join(
            ["LOWER(content) LIKE ?"] * len(words)
        )

        sql = f"""
        SELECT DISTINCT path
        FROM files
        WHERE {where}
        LIMIT 20
        """

        params = [
            f"%{w}%"
            for w in words
        ]

        cur = self.db.execute(sql, params)

        return [row[0] for row in cur.fetchall()]

    def get_content(self, path, max_chars=None):

        cur = self.db.execute(
            """
            SELECT content
            FROM files
            WHERE path = ?
            LIMIT 1
            """,
            (path,)
        )

        row = cur.fetchone()

        if not row:
            return ""

        content = row[0]

        if max_chars:
            return content[:max_chars]

        return content
