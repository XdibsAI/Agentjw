"""
Media Registry — SiCuan tahu semua video/gambar yang pernah dibuat
"""
import sqlite3
from pathlib import Path
from datetime import datetime

DB = Path("/home/dibs/agentjw/memory/media_registry.db")
BASE = Path("/home/dibs/agentjw")


def init_db():
    conn = sqlite3.connect(DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            path TEXT UNIQUE,
            project TEXT,
            size_kb INTEGER,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def scan_and_index():
    """Scan seluruh VPS untuk video/gambar yang pernah dibuat"""
    init_db()
    conn = sqlite3.connect(DB)

    patterns = {
        "video": ["*.mp4", "*.mov"],
        "image": ["*.png", "*.jpg", "*.jpeg"],
    }

    search_dirs = [
        BASE / "uploads",
        BASE / "projects",
        BASE,
    ]

    found = 0
    for media_type, patterns_list in patterns.items():
        for pattern in patterns_list:
            for d in search_dirs:
                if not d.exists():
                    continue
                for f in d.rglob(pattern):
                    if "venv" in str(f) or "node_modules" in str(f):
                        continue
                    try:
                        size_kb = f.stat().st_size // 1024
                        project = f.parent.name
                        conn.execute("""
                            INSERT OR IGNORE INTO media (type, path, project, size_kb, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (media_type, str(f), project, size_kb, datetime.now().isoformat()))
                        found += 1
                    except Exception:
                        pass

    conn.commit()
    conn.close()
    return found


def list_media(media_type: str = None) -> list:
    init_db()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    if media_type:
        rows = conn.execute("SELECT * FROM media WHERE type = ? ORDER BY created_at DESC", (media_type,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM media ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def gallery_summary() -> str:
    media = list_media()
    if not media:
        return "Gallery masih kosong — belum ada video/gambar yang ter-scan."

    videos = [m for m in media if m["type"] == "video"]
    images = [m for m in media if m["type"] == "image"]

    text = f"🎬 GALLERY STUDIO ({len(media)} item)\n\n"
    text += f"📹 Video ({len(videos)}):\n"
    for v in videos[:10]:
        text += f"  • {Path(v['path']).name} ({v['size_kb']}KB) — {v['project']}\n"

    text += f"\n🖼 Gambar ({len(images)}):\n"
    for img in images[:10]:
        text += f"  • {Path(img['path']).name} ({img['size_kb']}KB) — {img['project']}\n"

    return text


if __name__ == "__main__":
    n = scan_and_index()
    print(f"✓ Indexed {n} media files")
    print(gallery_summary())
