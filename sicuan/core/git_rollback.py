"""
Git Rollback — Kembalikan perubahan jika repair gagal
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class GitRollback:
    """Git integration untuk rollback jika repair gagal"""

    def __init__(self, repo_dir: str = "/home/dibs/agentjw"):
        self.repo_dir = Path(repo_dir)

    def save_state(self, file_path: str) -> Dict:
        """Save state sebelum repair"""
        result = {
            "success": False,
            "hash": "",
            "message": ""
        }

        if not self._is_git_repo():
            result["message"] = "Not a git repository"
            return result

        try:
            # Get current hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            if hash_result.returncode == 0:
                result["hash"] = hash_result.stdout.strip()[:8]
                result["success"] = True
                result["message"] = f"State saved at {result['hash']}"
        except Exception as e:
            result["message"] = str(e)

        return result

    def rollback(self, file_path: str, before_hash: str) -> Dict:
        """Rollback ke state sebelumnya"""
        result = {
            "success": False,
            "message": ""
        }

        if not self._is_git_repo():
            result["message"] = "Not a git repository"
            return result

        try:
            # Checkout file ke state sebelumnya
            result = subprocess.run(
                ["git", "checkout", before_hash, "--", str(file_path)],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return {"success": True, "message": f"Rollback to {before_hash} successful"}
            else:
                return {"success": False, "message": result.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def commit_if_success(self, file_path: str, message: str = "Auto-repair successful") -> Dict:
        """Commit jika repair berhasil"""
        result = {
            "success": False,
            "message": ""
        }

        if not self._is_git_repo():
            result["message"] = "Not a git repository"
            return result

        try:
            # Add file
            add_result = subprocess.run(
                ["git", "add", str(file_path)],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            if add_result.returncode != 0:
                return {"success": False, "message": add_result.stderr}

            # Commit
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_dir,
                capture_output=True,
                text=True
            )
            if commit_result.returncode == 0:
                return {"success": True, "message": "Commit successful"}
            else:
                return {"success": False, "message": commit_result.stderr}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def _is_git_repo(self) -> bool:
        """Cek apakah ini git repository"""
        return (self.repo_dir / ".git").exists()


def get_git_rollback():
    return GitRollback()
