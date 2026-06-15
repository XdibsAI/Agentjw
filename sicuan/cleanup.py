"""
SiCuan Project Cleanup
Cuan bisa audit dan hapus project yang tidak diperlukan
"""
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from core.logger import logger

DB = Path("/home/dibs/agentjw/memory/agentjw.db")


def audit_projects() -> list:
    """Return list project dengan status lengkap"""
    import ast
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    projects = conn.execute(
        "SELECT * FROM managed_projects ORDER BY created_at"
    ).fetchall()
    conn.close()

    result = []
    for p in projects:
        pd = Path(p["project_dir"]) if p["project_dir"] else None
        exists = pd.exists() if pd else False
        py_files = list(pd.glob("*.py")) if exists else []

        corrupt = 0
        for f in py_files:
            try:
                ast.parse(f.read_text())
            except Exception:
                corrupt += 1

        # Tentukan rekomendasi
        rec = "keep"
        reason = ""
        if not exists:
            rec = "delete_db_only"
            reason = "folder tidak ada"
        elif p["status"] == "partial" and corrupt > 0:
            rec = "delete"
            reason = f"{corrupt} file corrupt"
        elif p["status"] == "partial" and len(py_files) <= 1:
            rec = "review"
            reason = "partial, hanya 1 file"
        elif p["name"].startswith("hello_world") or p["name"].startswith("test_"):
            rec = "delete"
            reason = "test project"

        result.append({
            "id": p["id"],
            "name": p["name"],
            "status": p["status"],
            "tool_type": p["tool_type"],
            "project_dir": p["project_dir"],
            "created_at": p["created_at"][:10],
            "dir_exists": exists,
            "py_files": len(py_files),
            "corrupt": corrupt,
            "recommendation": rec,
            "reason": reason,
        })
    return result


def delete_project(project_id: str, delete_files: bool = True) -> dict:
    """
    Hapus project dari DB dan optionally dari disk.
    Cuan selalu backup dulu sebelum hapus.
    """
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    proj = conn.execute(
        "SELECT * FROM managed_projects WHERE id = ?", (project_id,)
    ).fetchone()

    if not proj:
        conn.close()
        return {"success": False, "error": "Project tidak ditemukan"}

    name = proj["name"]
    project_dir = Path(proj["project_dir"]) if proj["project_dir"] else None

    # Backup ke folder trash dulu
    trash_dir = Path("/home/dibs/agentjw/backups/trash")
    trash_dir.mkdir(parents=True, exist_ok=True)

    if delete_files and project_dir and project_dir.exists():
        backup_path = trash_dir / f"{name}_{project_id[:8]}_{datetime.now().strftime('%Y%m%d')}"
        try:
            shutil.copytree(str(project_dir), str(backup_path))
            shutil.rmtree(str(project_dir))
            logger.info(f"Deleted + backed up: {name} → {backup_path}")
        except Exception as e:
            conn.close()
            return {"success": False, "error": f"Gagal hapus folder: {e}"}

    # Hapus dari DB
    conn.execute("DELETE FROM managed_projects WHERE id = ?", (project_id,))
    conn.execute("DELETE FROM project_files WHERE project_id = ?", (project_id,))
    conn.execute("DELETE FROM work_log WHERE project_id = ?", (project_id,))
    conn.commit()
    conn.close()

    logger.info(f"Project deleted from DB: {name} [{project_id[:8]}]")
    return {
        "success": True,
        "deleted": name,
        "backup": str(trash_dir / f"{name}_{project_id[:8]}_*"),
        "files_deleted": delete_files,
    }


def cleanup_report() -> str:
    """Generate laporan cleanup dalam bahasa natural"""
    projects = audit_projects()
    to_delete = [p for p in projects if p["recommendation"] == "delete"]
    to_review = [p for p in projects if p["recommendation"] == "review"]
    to_keep = [p for p in projects if p["recommendation"] == "keep"]
    orphan = [p for p in projects if p["recommendation"] == "delete_db_only"]

    report = f"📊 AUDIT PROJECT ({len(projects)} total)\n\n"

    if to_delete:
        report += f"🗑 BISA DIHAPUS ({len(to_delete)}):\n"
        for p in to_delete:
            report += f"  • {p['name']} [{p['id'][:8]}] — {p['reason']}\n"
        report += "\n"

    if to_review:
        report += f"⚠️ PERLU REVIEW ({len(to_review)}):\n"
        for p in to_review:
            report += f"  • {p['name']} [{p['id'][:8]}] — {p['reason']}\n"
        report += "\n"

    if orphan:
        report += f"👻 ORPHAN DB ({len(orphan)}):\n"
        for p in orphan:
            report += f"  • {p['name']} [{p['id'][:8]}] — folder tidak ada\n"
        report += "\n"

    report += f"✅ SEHAT ({len(to_keep)}): "
    report += ", ".join(p["name"][:20] for p in to_keep[:5])
    if len(to_keep) > 5:
        report += f" +{len(to_keep)-5} lagi"

    return report


cleanup = {
    "audit": audit_projects,
    "delete": delete_project,
    "report": cleanup_report,
}
