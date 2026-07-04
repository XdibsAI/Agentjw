"""
Vault Manager - Mengelola Obsidian Vault sebagai Second Brain
"""

import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class VaultNote:
    """Representasi satu note di vault"""
    path: str
    title: str
    content: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    folder: str


class VaultManager:
    """Mengelola Obsidian Vault"""

    def __init__(self, vault_path: str = "/home/dibs/agentjw/obsidian"):
        self.vault_path = Path(vault_path)
        self.folders = {
            "inbox": "00-Inbox",
            "sources": "01-Sources",
            "ideas": "02-Ideas",
            "projects": "03-Projects",
            "claude": "04-Claude",
        }
        self._ensure_structure()

    def _ensure_structure(self):
        """Pastikan folder structure ada"""
        for folder in self.folders.values():
            (self.vault_path / folder).mkdir(parents=True, exist_ok=True)

    def scan(self) -> Dict[str, List[VaultNote]]:
        """Scan semua notes di vault"""
        result = {}
        for key, folder in self.folders.items():
            path = self.vault_path / folder
            if path.exists():
                notes = []
                for file in path.glob("*.md"):
                    note = self._parse_note(file, key)
                    if note:
                        notes.append(note)
                result[key] = notes
        return result

    def _parse_note(self, file: Path, folder: str) -> Optional[VaultNote]:
        """Parse satu file markdown"""
        try:
            content = file.read_text(encoding="utf-8")
            
            # Extract title dari filename atau first heading
            title = file.stem
            if content.startswith("# "):
                title = content.split("\n")[0].replace("# ", "").strip()
            
            # Extract tags
            tags = re.findall(r'#(\w+)', content)
            
            # Get timestamps
            stat = file.stat()
            created = datetime.fromtimestamp(stat.st_ctime)
            updated = datetime.fromtimestamp(stat.st_mtime)
            
            return VaultNote(
                path=str(file),
                title=title,
                content=content[:500],  # Simpan sebagian untuk ringkasan
                tags=tags,
                created_at=created,
                updated_at=updated,
                folder=folder
            )
        except Exception as e:
            return None

    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search vault untuk topik tertentu"""
        results = []
        for file in self.vault_path.glob("**/*.md"):
            try:
                content = file.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    # Cari konteks di sekitar match
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if query.lower() in line.lower():
                            context = "\n".join(lines[max(0, i-2):min(len(lines), i+3)])
                            results.append({
                                "file": str(file.relative_to(self.vault_path)),
                                "title": file.stem,
                                "line": line.strip(),
                                "context": context[:300],
                                "score": len(re.findall(query.lower(), content.lower()))
                            })
                            break
            except:
                pass
        
        # Sort by score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:limit]

    def get_recent_notes(self, days: int = 7) -> List[VaultNote]:
        """Dapatkan notes yang diupdate dalam N hari terakhir"""
        all_notes = []
        for _, folder in self.folders.items():
            path = self.vault_path / folder
            if path.exists():
                for file in path.glob("*.md"):
                    note = self._parse_note(file, folder)
                    if note:
                        all_notes.append(note)
        
        cutoff = datetime.now() - timedelta(days=days)
        return [n for n in all_notes if n.updated_at > cutoff]

    def daily_review(self) -> str:
        """Review 7 hari terakhir — sintesis"""
        recent = self.get_recent_notes(7)
        if not recent:
            return "📝 Tidak ada notes baru dalam 7 hari terakhir."
        
        lines = [
            "📊 **DAILY VAULT REVIEW**",
            f"  {len(recent)} notes diupdate dalam 7 hari terakhir:",
            ""
        ]
        
        # Group by folder
        by_folder = {}
        for note in recent:
            by_folder.setdefault(note.folder, []).append(note)
        
        for folder, notes in by_folder.items():
            lines.append(f"📁 {folder}: {len(notes)} notes")
            for note in notes[:3]:
                lines.append(f"  • {note.title} ({note.tags[:3] if note.tags else 'no tags'})")
            if len(notes) > 3:
                lines.append(f"  ... dan {len(notes)-3} lainnya")
            lines.append("")
        
        return "\n".join(lines)

    def weekly_review(self) -> str:
        """Review 30 hari — cari kontradiksi & pola"""
        recent = self.get_recent_notes(30)
        if not recent:
            return "📝 Tidak ada notes dalam 30 hari terakhir."
        
        # Cari kontradiksi: notes dengan tags/ide yang berlawanan
        lines = [
            "📊 **WEEKLY VAULT REVIEW**",
            f"  {len(recent)} notes dalam 30 hari terakhir:",
            ""
        ]
        
        # Cari pola (tags yang sering muncul)
        tag_count = {}
        for note in recent:
            for tag in note.tags:
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        if tag_count:
            lines.append("🏷️ **Top Tags:**")
            for tag, count in sorted(tag_count.items(), key=lambda x: x[1], reverse=True)[:5]:
                lines.append(f"  #{tag}: {count} notes")
            lines.append("")
        
        # Cari kontradiksi (sederhana: notes dengan kata "tapi" atau "kontradiksi")
        contradictions = []
        for note in recent:
            if "tapi" in note.content.lower() or "kontradiksi" in note.content.lower():
                contradictions.append(note)
        
        if contradictions:
            lines.append("⚠️ **Potensi Kontradiksi Terdeteksi:**")
            for note in contradictions[:3]:
                lines.append(f"  • {note.title}")
        
        return "\n".join(lines)

    def before_decision(self, topic: str) -> str:
        """Search vault sebelum ambil keputusan"""
        results = self.search(topic, limit=5)
        if not results:
            return f"🔍 Tidak ada catatan tentang '{topic}' di vault."
        
        lines = [
            f"🔍 **VAULT CHECK: {topic}**",
            f"  {len(results)} catatan ditemukan:",
            ""
        ]
        for r in results:
            lines.append(f"📄 {r['file']}")
            lines.append(f"  {r['context']}")
            lines.append("")
        
        return "\n".join(lines)
