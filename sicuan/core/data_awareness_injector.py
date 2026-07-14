"""
Data Awareness Injector - Menyisipkan status data ke context tanpa mengubah brain.py
"""

from pathlib import Path
#   # Migrated to adapter


def get_data_availability(target: str) -> str:
    """Dapatkan status data availability untuk target project"""
    if not target:
        return "⚠️ Target project tidak ditentukan."

    # Cari project
    project_dir = Path("/home/dibs/agentjw/projects") / target
    if not project_dir.exists():
        adapter = get_project_adapter()
        projects = adapter.get_projects()
        for p in projects:
            if target.lower() in p["name"].lower():
                project_dir = Path(p["project_dir"])
                break

    if not project_dir.exists():
        return f"❌ Project '{target}' tidak ditemukan"

    # Cek trade_history.db
    db_path = project_dir / "trade_history.db"
    if db_path.exists():
        return f"✅ Trade history tersedia di {db_path}"
    else:
        return f"❌ Trade history TIDAK tersedia. Data untuk analisis tidak lengkap."


def inject_to_context(context: list, target: str) -> list:
    """Sisipkan data availability ke context"""
    status = get_data_availability(target)
    context.append(f"\n[DATA AVAILABILITY]\n{status}\n")
    return context
