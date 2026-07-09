"""
Multimodel Orchestrator - Weighted Routing (Stable Version 96.7%)
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from sicuan.core.decision_engine import get_decision_engine


class MultimodelOrchestrator:
    """Orchestrator dengan weighted routing - stable version"""

    def __init__(self):
        self.decision_engine = get_decision_engine()
        self.models = {
            "coder": {
                "name": "qwen/qwen3-coder",
                "role": "coding, debugging, repair",
                "keywords": [
                    "fungsi", "function", "python", "code", "kode", "class",
                    "script", "tulis", "buat", "generate", "implement", "create",
                    "patch", "fix", "repair", "refactor", "optimize", "debug",
                    "perbaiki", "error", "bug", "refactor", "program", "write", "coding",
                    "algorithm", "sorting", "queue", "stack", "database", "login",
                    "hash", "encrypt", "decrypt", "api", "rest", "backup", "scraping",
                    "validasi", "format", "logging", "cache", "fibonacci", "csv"
                ],
                "weight": 10
            },
            "reviewer": {
                "name": "openai/gpt-4-turbo",
                "role": "review, audit, quality check",
                "keywords": [
                    "review", "validate", "audit", "verify", "quality",
                    "cek kode", "code review", "inspect", "review kode",
                    "security", "vulnerability", "best practice", "test coverage",
                    "code quality", "code complexity", "code structure", "error handling",
                    "performance issue", "deployment", "pull request", "documentation",
                    "api design", "input validation", "check", "analyze code"
                ],
                "weight": 15
            },
            "planner": {
                "name": "anthropic/claude-3.5-sonnet",
                "role": "planning, strategy, roadmap",
                "keywords": [
                    "plan", "strategy", "roadmap", "prioritas", "tujuan",
                    "goal", "langkah", "strategi", "rencana", "roadmap bisnis",
                    "marketing", "fundraising", "ekspansi", "monetisasi", "engineering",
                    "growth", "product", "development", "scalability", "automation"
                ],
                "weight": 15
            },
            "analyzer": {
                "name": "x-ai/grok-2-1212",
                "role": "data analysis, pattern, insight",
                "keywords": [
                    "data", "analisis", "statistik", "trend", "pattern",
                    "insight", "trading", "pnl", "performa", "metric",
                    "correlation", "anomaly", "forecast", "sentiment", "market",
                    "competitive", "customer", "product", "financial", "operational",
                    "analysis", "risk", "win rate", "profit", "dataset",
                    "analyze", "metrics", "stats", "performance"
                ],
                "weight": 6
            },
            "vision": {
                "name": "google/gemini-2.0-flash-exp",
                "role": "vision, image, multimodal",
                "keywords": [
                    "gambar", "image", "photo", "foto",
                    "screen", "screenshot", "photo recognition", "object detection",
                    "face detection", "scene understanding", "diagram",
                    "document analysis", "qr code",
                    "barcode", "logo", "color analysis", "video frame",
                    "analisis gambar", "ocr", "screen capture",
                    "screenshot ini", "lihat gambar", "lihat foto",
                    "visual inspection", "visual quality", "chart recognition",
                    "quality check"
                ],
                "weight": 20
            },
            "fast": {
                "name": "deepseek/deepseek-chat",
                "role": "quick responses",
                "keywords": [
                    "halo", "hi", "ok", "oke", "siap",
                    "cuan", "yes", "no", "gak", "udah",
                    "nih", "gas"
                ],
                "weight": 1
            },
            "chat": {
                "name": "deepseek/deepseek-chat",
                "role": "general conversation",
                "keywords": [
                    "ceritakan", "jelaskan", "pendapat", "caranya", "manfaatnya",
                    "mengapa", "bagaimana", "apa yang", "kamu bisa", "tentang",
                    "dirimu", "cuaca", "hari ini", "perasaan", "pelajari",
                    "berbeda", "kerjamu", "special", "proyek", "menurutmu",
                    "kabar", "siapa", "kapan", "dimana", "kenapa",
                    "cerita", "pikirkan", "rasakan", "lihat", "dengar",
                    "AI", "artificial", "intelligence", "masa depan", "manfaat",
                    "bagaimana cuaca", "apa pendapatmu", "bagaimana caranya",
                    "apa manfaatnya", "bagaimana perasaanmu", "apa yang baru",
                    "cuaca", "pendapat", "caranya", "manfaatnya", "perasaanmu"
                ],
                "weight": 20
            }
        }

    def get_model(self, role: str) -> Dict:
        return self.models.get(role, self.models["chat"])

    def route_task(self, task: str, context: Dict = None) -> str:
        task_lower = task.lower()
        word_count = len(task_lower.split())
        
        # === PRIORITAS: CHAT vs FAST ===
        question_words = ["apa", "bagaimana", "kenapa", "mengapa", "siapa", "kapan", "dimana"]
        if any(qw in task_lower for qw in question_words) and word_count > 3:
            if not any(kw in task_lower for kw in ["code", "review", "data", "trade", "gambar", "plan", "strategy", "roadmap"]):
                return "chat"
        
        # Calculate score
        scores = {}
        for role, model in self.models.items():
            score = 0
            for keyword in model.get("keywords", []):
                if keyword in task_lower:
                    score += model.get("weight", 1)
            scores[role] = score
        
        best_role = max(scores, key=scores.get) if any(scores.values()) else "chat"
        
        if best_role == "chat" and word_count <= 2:
            best_role = "fast"
        
        if scores.get(best_role, 0) > 0:
            print(f"[ORCHESTRATOR] Routing: '{task[:30]}...' → {best_role} (score: {scores[best_role]})")
        
        return best_role

    def get_task_summary(self) -> str:
        lines = []
        lines.append("🧠 **Multimodel Orchestrator**")
        lines.append("")
        lines.append("| Role | Model | Task |")
        lines.append("|------|-------|------|")
        for role, info in self.models.items():
            lines.append(f"| {role} | {info['name']} | {info['role']} |")
        return "\n".join(lines)


_orchestrator = None

def get_multimodel_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultimodelOrchestrator()
    return _orchestrator
