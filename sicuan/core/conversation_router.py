"""
Conversation Router - Menentukan jalur yang tepat untuk setiap pesan
Versi 2.0 — Data-driven, scalable
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from enum import Enum


class RouteType(Enum):
    MEMORY_QUERY = "memory_query"
    KNOWLEDGE_QUERY = "knowledge_query"
    DECISION_QUERY = "decision_query"
    ARTIFACT_QUERY = "artifact_query"
    PROGRESS_QUERY = "progress_query"
    PLANNING_QUERY = "planning_query"
    EXECUTION = "execution"
    SMALL_TALK = "small_talk"
    FALLBACK = "fallback"


class ConversationRouter:
    """Menentukan jalur yang tepat untuk setiap pesan — Data-driven"""

    def __init__(self, state=None):
        self.state = state
        self.rules = []
        self.default_action = "analyze_project"
        self.fallback_action = "chat"
        self._load_rules()

    def _load_rules(self):
        """Load rules dari JSON"""
        rules_file = Path("sicuan/config/routing_rules.json")
        if rules_file.exists():
            try:
                data = json.loads(rules_file.read_text())
                self.rules = data.get("rules", [])
                self.default_action = data.get("default_action", "analyze_project")
                self.fallback_action = data.get("fallback_action", "chat")
                print(f"[ROUTER] Loaded {len(self.rules)} rules from {rules_file}")
            except Exception as e:
                print(f"[ROUTER] Error loading rules: {e}")
                self.rules = []
                self._load_fallback_rules()
        else:
            print(f"[ROUTER] Rules file not found, using fallback")
            self._load_fallback_rules()

    def _load_fallback_rules(self):
        """Fallback rules (hardcoded) jika JSON tidak ada"""
        self.rules = [
            {"id": "memory_query", "patterns": ["masih ingat", "ingat", "terakhir", "kemarin", "sebelumnya", "yang tadi"], "action": "memory_query", "priority": 9},
            {"id": "decision_query", "patterns": ["kenapa", "mengapa", "alasan", "kok"], "action": "decision_query", "priority": 8},
            {"id": "knowledge_query", "patterns": ["berapa", "jumlah", "total", "ada berapa"], "action": "knowledge_query", "priority": 7},
            {"id": "progress_query", "patterns": ["sampai mana", "progress", "pending", "sejauh mana"], "action": "progress_query", "priority": 6},
            {"id": "execution", "patterns": ["scan", "analyze", "analisa", "repair", "build", "run", "perbaiki"], "action": "execution", "priority": 5},
            {"id": "small_talk", "patterns": ["halo", "hai", "hi", "apa kabar"], "action": "small_talk", "priority": 3},
        ]

    def route(self, user_message: str) -> Tuple[RouteType, Dict]:
        """Tentukan jalur berdasarkan pesan — Data-driven"""
        message_lower = user_message.lower()

        # Sort by priority (descending)
        sorted_rules = sorted(self.rules, key=lambda x: x.get("priority", 0), reverse=True)

        for rule in sorted_rules:
            patterns = rule.get("patterns", [])
            if not patterns:
                continue

            # Check if any pattern matches
            for pattern in patterns:
                if pattern.lower() in message_lower:
                    action = rule.get("action", self.fallback_action)
                    
                    # Map action to RouteType
                    route_type = self._map_action_to_route(action)
                    
                    return route_type, {
                        "query": user_message,
                        "rule_id": rule.get("id"),
                        "action": action,
                        "priority": rule.get("priority", 0)
                    }

        # Check for URL
        if "http" in message_lower or "https" in message_lower:
            return RouteType.EXECUTION, {
                "query": user_message,
                "action": "analyze_url",
                "is_url": True
            }

        # Default fallback
        return RouteType.FALLBACK, {"query": user_message}

    def _map_action_to_route(self, action: str) -> RouteType:
        """Map action string ke RouteType"""
        mapping = {
            "memory_query": RouteType.MEMORY_QUERY,
            "knowledge_query": RouteType.KNOWLEDGE_QUERY,
            "decision_query": RouteType.DECISION_QUERY,
            "artifact_query": RouteType.ARTIFACT_QUERY,
            "progress_query": RouteType.PROGRESS_QUERY,
            "planning_query": RouteType.PLANNING_QUERY,
            "analyze_project": RouteType.EXECUTION,
            "analyze_url": RouteType.EXECUTION,
            "modify_logic": RouteType.EXECUTION,
            "list_projects": RouteType.EXECUTION,
            "godmeme_status": RouteType.EXECUTION,
            "execution": RouteType.EXECUTION,
            "small_talk": RouteType.SMALL_TALK,
        }
        return mapping.get(action, RouteType.FALLBACK)

    def should_use_query(self, route: RouteType) -> bool:
        """Apakah route ini harus menggunakan Query Layer?"""
        return route in [
            RouteType.MEMORY_QUERY,
            RouteType.KNOWLEDGE_QUERY,
            RouteType.DECISION_QUERY,
            RouteType.ARTIFACT_QUERY,
            RouteType.PROGRESS_QUERY,
            RouteType.PLANNING_QUERY
        ]

    def should_use_executor(self, route: RouteType) -> bool:
        """Apakah route ini harus menggunakan Executor?"""
        return route in [
            RouteType.EXECUTION
        ]

    def should_use_brain(self, route: RouteType) -> bool:
        """Apakah route ini harus menggunakan Brain?"""
        return route in [
            RouteType.EXECUTION,
            RouteType.PLANNING_QUERY
        ]

    def reload_rules(self):
        """Reload rules dari JSON (untuk hot-reload)"""
        self._load_rules()
