"""
Dynamic Blacklist - Data-driven token blacklist
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional


class DynamicBlacklist:
    """Blacklist dinamis berdasarkan data trading"""

    def __init__(self, memory_dir: str = "memory"):
        self.memory_dir = Path(memory_dir)
        self.blacklist_file = self.memory_dir / "dynamic_blacklist.json"
        self.blacklist = {}
        self._load()

    def update(self, token: str, win_rate: float, trades: int, pnl: float = 0):
        """Update blacklist berdasarkan data"""
        # Blacklist if: win_rate < 10% and trades >= 3
        if win_rate < 10 and trades >= 3:
            self.blacklist[token] = {
                "reason": f"win_rate {win_rate:.1f}% from {trades} trades",
                "pnl": pnl,
                "timestamp": datetime.now().isoformat()
            }
            print(f"[BLACKLIST] Added {token} (win_rate: {win_rate:.1f}%)")
        elif token in self.blacklist:
            # If token improves, remove from blacklist
            if win_rate > 20:
                del self.blacklist[token]
                print(f"[BLACKLIST] Removed {token} (win_rate: {win_rate:.1f}%)")
        
        self._save()

    def is_blacklisted(self, token: str) -> bool:
        """Cek apakah token di blacklist"""
        return token in self.blacklist

    def get_blacklist(self) -> Dict:
        """Dapatkan daftar blacklist"""
        return self.blacklist

    def auto_cleanup(self, days: int = 7):
        """Hapus blacklist yang sudah lama"""
        cutoff = datetime.now() - timedelta(days=days)
        removed = []
        for token, data in list(self.blacklist.items()):
            try:
                if datetime.fromisoformat(data["timestamp"]) < cutoff:
                    removed.append(token)
                    del self.blacklist[token]
            except:
                pass
        
        if removed:
            print(f"[BLACKLIST] Cleanup: removed {len(removed)} old entries")
        
        self._save()

    def _load(self):
        """Load dari disk"""
        if self.blacklist_file.exists():
            try:
                self.blacklist = json.loads(self.blacklist_file.read_text())
                print(f"[BLACKLIST] Loaded {len(self.blacklist)} entries")
            except:
                self.blacklist = {}

    def _save(self):
        """Save ke disk"""
        self.blacklist_file.write_text(json.dumps(self.blacklist, indent=2))


# Singleton
_blacklist = None

def get_blacklist():
    global _blacklist
    if _blacklist is None:
        _blacklist = DynamicBlacklist()
    return _blacklist
