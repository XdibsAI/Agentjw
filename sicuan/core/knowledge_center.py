"""
Knowledge Center — Pusat pengetahuan terpusat
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class KnowledgeCenter:
    """Pusat pengetahuan untuk semua agent"""

    def __init__(self):
        self.root = Path("/home/dibs/agentjw/knowledge")
        self.root.mkdir(parents=True, exist_ok=True)
        self.categories = [
            "trading", "youtube", "marketing", "sales", "customer",
            "finance", "coding", "architecture", "telegram", "solana",
            "prompt", "roadmap"
        ]
        self._cache = {}

    def get_knowledge(self, category: str, key: str) -> Optional[Dict]:
        """Ambil knowledge dari kategori tertentu"""
        cache_key = f"{category}:{key}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        file_path = self.root / category / f"{key}.json"
        if file_path.exists():
            try:
                data = json.loads(file_path.read_text())
                self._cache[cache_key] = data
                return data
            except:
                return None
        return None

    def save_knowledge(self, category: str, key: str, data: Dict) -> Dict:
        """Simpan knowledge ke kategori tertentu"""
        category_dir = self.root / category
        category_dir.mkdir(parents=True, exist_ok=True)
        file_path = category_dir / f"{key}.json"
        
        data["updated_at"] = datetime.now().isoformat()
        file_path.write_text(json.dumps(data, indent=2))
        self._cache[f"{category}:{key}"] = data
        return {"status": "saved", "category": category, "key": key}

    def list_knowledge(self, category: str) -> List[str]:
        """List semua knowledge dalam kategori"""
        category_dir = self.root / category
        if not category_dir.exists():
            return []
        return [f.stem for f in category_dir.glob("*.json")]

    def search(self, query: str, category: str = None) -> List[Dict]:
        """Search knowledge"""
        results = []
        categories = [category] if category else self.categories
        
        for cat in categories:
            for key in self.list_knowledge(cat):
                data = self.get_knowledge(cat, key)
                if data:
                    text = json.dumps(data).lower()
                    if query.lower() in text:
                        results.append({
                            "category": cat,
                            "key": key,
                            "data": data
                        })
        return results

    def get_context(self, category: str, query: str = "") -> str:
        """Dapatkan context dari knowledge"""
        keys = self.list_knowledge(category)
        if not keys:
            return f"Tidak ada knowledge di kategori {category}"
        
        lines = [f"📚 **Knowledge: {category.capitalize()}**"]
        for key in keys[:5]:
            data = self.get_knowledge(category, key)
            if data:
                summary = data.get("summary", str(data)[:100])
                lines.append(f"  - {key}: {summary}")
        return "\n".join(lines)


_center = None


def get_knowledge_center() -> KnowledgeCenter:
    global _center
    if _center is None:
        _center = KnowledgeCenter()
    return _center
