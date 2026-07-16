"""
Knowledge on Demand — Load knowledge when needed
"""
import json
from pathlib import Path
from typing import Dict, Optional, List


class KnowledgeLoader:
    """Load knowledge on demand — tidak semua di-load di awal"""

    def __init__(self, knowledge_dir: Path = Path("/home/dibs/agentjw/sicuan/knowledge")):
        self.knowledge_dir = knowledge_dir
        self._cache = {}

    def list_available(self) -> List[str]:
        """List semua knowledge yang tersedia"""
        if not self.knowledge_dir.exists():
            return []
        return [f.stem for f in self.knowledge_dir.glob("*.json")]

    def load(self, name: str) -> Optional[Dict]:
        """Load knowledge by name"""
        if name in self._cache:
            return self._cache[name]

        file_path = self.knowledge_dir / f"{name}.json"
        if not file_path.exists():
            return None

        try:
            data = json.loads(file_path.read_text())
            self._cache[name] = data
            return data
        except:
            return None

    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """Search knowledge berdasarkan query"""
        results = []
        for name in self.list_available():
            data = self.load(name)
            if not data:
                continue
            # Simple keyword search
            text = json.dumps(data).lower()
            if query.lower() in text:
                results.append({
                    "name": name,
                    "data": data,
                    "matched": True
                })
                if len(results) >= limit:
                    break
        return results

    def get_context(self, query: str) -> str:
        """Dapatkan context dari knowledge yang relevan"""
        results = self.search(query, limit=3)
        if not results:
            return ""

        lines = ["=== KNOWLEDGE RELEVAN ==="]
        for r in results:
            lines.append(f"📚 {r['name']}:")
            # Ambil 500 karakter pertama
            text = json.dumps(r['data'], indent=2)[:500]
            lines.append(text)
            lines.append("")
        return "\n".join(lines)


_loader = None


def get_knowledge_loader() -> KnowledgeLoader:
    global _loader
    if _loader is None:
        _loader = KnowledgeLoader()
    return _loader
