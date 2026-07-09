"""
Backup & Restore - Workspace backup system
"""

import json
import shutil
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional


class BackupManager:
    """Backup dan restore workspace"""

    def __init__(self):
        self.workspace_dir = Path("/home/dibs/agentjw/memory/workspaces")
        self.backup_dir = Path("/home/dibs/agentjw/memory/backups")
        self.backup_dir.mkdir(exist_ok=True)

    def backup(self, workspace_id: str) -> Dict:
        """Backup workspace"""
        ws_dir = self.workspace_dir / workspace_id
        if not ws_dir.exists():
            return {"success": False, "error": "Workspace not found"}
        
        backup_name = f"{workspace_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.backup_dir / f"{backup_name}.zip"
        
        # Create zip
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in ws_dir.rglob("*"):
                if file.is_file():
                    zipf.write(file, file.relative_to(ws_dir))
        
        return {
            "success": True,
            "backup_id": backup_name,
            "path": str(backup_path),
            "size": backup_path.stat().st_size,
            "created_at": datetime.now().isoformat()
        }

    def list_backups(self, workspace_id: str = None) -> list:
        """List backups"""
        backups = []
        for f in self.backup_dir.glob("*.zip"):
            if workspace_id and not f.name.startswith(workspace_id):
                continue
            backups.append({
                "id": f.stem,
                "path": str(f),
                "size": f.stat().st_size,
                "created_at": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
            })
        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def restore(self, backup_id: str, target_workspace_id: str = None) -> Dict:
        """Restore backup"""
        backup_path = self.backup_dir / f"{backup_id}.zip"
        if not backup_path.exists():
            return {"success": False, "error": "Backup not found"}
        
        # Extract
        extract_dir = self.backup_dir / "temp_restore"
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        # Determine workspace_id
        if not target_workspace_id:
            target_workspace_id = backup_id.split("_")[0]
        
        target_dir = self.workspace_dir / target_workspace_id
        
        # Backup existing if exists
        if target_dir.exists():
            self.backup(target_workspace_id)
            shutil.rmtree(target_dir)
        
        # Copy restored
        shutil.copytree(extract_dir, target_dir)
        
        # Cleanup
        shutil.rmtree(extract_dir)
        
        return {
            "success": True,
            "workspace_id": target_workspace_id,
            "restored_at": datetime.now().isoformat()
        }


def get_backup_manager():
    _manager = None
    if _manager is None:
        _manager = BackupManager()
    return _manager
