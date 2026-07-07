"""
Target Resolver v2 — Pilih target berdasarkan intent, bukan hanya trace
"""

import re
from typing import Dict, List, Optional, Tuple


class TargetResolver:
    """Resolve target dengan weighted scoring"""

    def __init__(self):
        self.weights = {
            "filename": 100,   # User explicitly mentioned file
            "class": 70,       # User mentioned class name
            "method": 50,      # User mentioned method name
            "trace": 30,       # AST trace match
            "semantic": 20,    # Semantic similarity
        }

    def resolve(self, user_request: str, candidates: List[Dict]) -> Optional[Dict]:
        """
        Resolve target dengan scoring
        """
        # 1. Extract entities
        entities = self._extract_entities(user_request)
        
        # 2. Score each candidate
        scored = []
        for candidate in candidates:
            score = self._score_candidate(candidate, entities, user_request)
            scored.append((candidate, score))
        
        # 3. Sort by score
        scored.sort(key=lambda x: x[1], reverse=True)
        
        if scored:
            best = scored[0]
            print(f"[RESOLVER] Best: {best[0].get('file', 'N/A')} (score: {best[1]})")
            return best[0]
        
        return None

    def _extract_entities(self, text: str) -> Dict:
        """Extract filename, class, method dari user request"""
        entities = {
            "files": [],
            "classes": [],
            "methods": []
        }
        
        # Extract filenames (pattern: *.py)
        files = re.findall(r'([a-zA-Z_]+\.py)', text)
        entities["files"].extend(files)
        
        # Extract class names (pattern: class Xxx)
        classes = re.findall(r'class\s+([a-zA-Z_]+)', text)
        entities["classes"].extend(classes)
        
        # Extract method names (pattern: _xxx or xxx)
        methods = re.findall(r'[_a-zA-Z]+\(', text)
        entities["methods"].extend([m.rstrip('(') for m in methods])
        
        return entities

    def _score_candidate(self, candidate: Dict, entities: Dict, user_request: str) -> int:
        """Score candidate berdasarkan entities"""
        score = 0
        file_name = candidate.get("file", "")
        class_name = candidate.get("class", "")
        method_name = candidate.get("method", "")
        
        # 1. Filename match
        if file_name in entities["files"]:
            score += self.weights["filename"]
        
        # 2. Class match
        if class_name in entities["classes"]:
            score += self.weights["class"]
        
        # 3. Method match
        if method_name in entities["methods"]:
            score += self.weights["method"]
        
        # 4. Trace match (if candidate has trace)
        if candidate.get("trace_confidence", 0) > 50:
            score += self.weights["trace"]
        
        # 5. Semantic match (user_request contains file/class/method)
        if file_name and file_name.replace(".py", "") in user_request.lower():
            score += self.weights["semantic"]
        
        return score


# Singleton
_resolver = None

def get_target_resolver():
    global _resolver
    if _resolver is None:
        _resolver = TargetResolver()
    return _resolver
