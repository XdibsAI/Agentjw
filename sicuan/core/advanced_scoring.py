"""
Advanced Scoring Engine — Dynamic scoring dengan weights, cooldown, rate-limit
"""

import time
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, field

@dataclass
class ScoringConfig:
    weights: Dict[str, float] = field(default_factory=lambda: {
        "health": 0.40,
        "latency": 0.25,
        "cost": 0.15,
        "priority": 0.10,
        "availability": 0.05,
        "rate_limit": 0.05
    })
    cooldown_duration: int = 300
    failure_threshold: int = 3
    rate_limit_penalty_threshold: float = 10.0

@dataclass
class ProviderHealth:
    success_rate: float = 90.0
    avg_latency: float = 1.0
    total_calls: int = 0
    failed_calls: int = 0
    last_call: float = 0.0

class AdvancedScoringEngine:
    """
    Advanced scoring dengan cooldown, rate-limit, dan capability-level health
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("sicuan/config/scoring_config.yaml")
        self.config = self._load_config()
        
        self._cooldowns: Dict[str, float] = {}
        self._rate_limits: Dict[str, Dict] = {}
        self._health: Dict[str, ProviderHealth] = {}
        self._failure_counts: Dict[str, int] = {}
    
    def _load_config(self) -> Dict:
        """Load scoring configuration"""
        try:
            import yaml
            if self.config_path.exists():
                return yaml.safe_load(self.config_path.read_text())
        except:
            pass
        return {
            "weights": {
                "health": 0.40,
                "latency": 0.25,
                "cost": 0.15,
                "priority": 0.10,
                "availability": 0.05,
                "rate_limit": 0.05
            },
            "cooldown": {"duration": 300, "failure_threshold": 3},
            "rate_limit": {"penalty_threshold": 10, "recovery_threshold": 30}
        }
    
    def calculate_score(self, provider_name: str, capability: str,
                       priority: int, cost: float,
                       health_override: Dict = None) -> float:
        """Calculate dynamic score"""
        weights = self.config.get("weights", {})
        
        # Get health
        health_key = f"{provider_name}.{capability}"
        health = health_override or self._get_health(health_key)
        
        # Factors
        health_score = health.get("success_rate", 90) * weights.get("health", 0.40)
        latency_score = max(0, 100 - (health.get("avg_latency", 1.0) * 10)) * weights.get("latency", 0.25)
        cost_score = max(0, 100 - (cost * 1000)) * weights.get("cost", 0.15)
        priority_score = priority * weights.get("priority", 0.10)
        
        # Availability penalty (cooldown)
        avail_score = 100
        if self.is_in_cooldown(provider_name):
            avail_score = 0
        avail_score = avail_score * weights.get("availability", 0.05)
        
        # Rate limit penalty
        rate_score = self._get_rate_limit_score(provider_name) * weights.get("rate_limit", 0.05)
        
        total = health_score + latency_score + cost_score + priority_score + avail_score + rate_score
        return round(total, 2)
    
    def _get_health(self, key: str) -> Dict:
        """Get health for a capability"""
        if key in self._health:
            h = self._health[key]
            return {
                "success_rate": h.success_rate,
                "avg_latency": h.avg_latency,
                "total_calls": h.total_calls,
                "failed_calls": h.failed_calls
            }
        return {"success_rate": 90, "avg_latency": 1.0, "total_calls": 0, "failed_calls": 0}
    
    def record_call(self, provider: str, capability: str, success: bool, latency: float):
        """Record a call result"""
        key = f"{provider}.{capability}"
        
        if key not in self._health:
            self._health[key] = ProviderHealth()
        
        health = self._health[key]
        health.total_calls += 1
        if not success:
            health.failed_calls += 1
        
        # Update success rate
        success_count = health.total_calls - health.failed_calls
        health.success_rate = (success_count / max(1, health.total_calls)) * 100
        health.avg_latency = (health.avg_latency * (health.total_calls - 1) + latency) / health.total_calls
        health.last_call = time.time()
        
        # Track failures for cooldown
        if not success:
            self._failure_counts[provider] = self._failure_counts.get(provider, 0) + 1
            threshold = self.config.get("cooldown", {}).get("failure_threshold", 3)
            if self._failure_counts[provider] >= threshold:
                duration = self.config.get("cooldown", {}).get("duration", 300)
                self.set_cooldown(provider, duration)
        else:
            self._failure_counts[provider] = 0
    
    def set_cooldown(self, provider: str, duration: int = 300):
        """Set cooldown for provider"""
        self._cooldowns[provider] = time.time() + duration
        print(f"[COOLDOWN] {provider} cooldown until {self._cooldowns[provider]}")
    
    def is_in_cooldown(self, provider: str) -> bool:
        """Check if provider is in cooldown"""
        if provider not in self._cooldowns:
            return False
        return time.time() < self._cooldowns[provider]
    
    def update_rate_limit(self, provider: str, remaining: int, limit: int):
        """Update rate limit info"""
        self._rate_limits[provider] = {
            "remaining": remaining,
            "limit": limit,
            "updated_at": time.time()
        }
    
    def _get_rate_limit_score(self, provider: str) -> float:
        """Calculate rate limit score"""
        if provider not in self._rate_limits:
            return 100
        info = self._rate_limits[provider]
        ratio = info["remaining"] / max(1, info["limit"])
        return ratio * 100
    
    def get_health_summary(self) -> Dict:
        """Get health summary for all providers"""
        result = {}
        for key, health in self._health.items():
            provider, capability = key.split(".", 1)
            if provider not in result:
                result[provider] = {}
            result[provider][capability] = {
                "success_rate": round(health.success_rate, 2),
                "avg_latency": round(health.avg_latency, 2),
                "total_calls": health.total_calls,
                "failed_calls": health.failed_calls
            }
        return result

# Singleton
_engine = None

def get_scoring_engine() -> AdvancedScoringEngine:
    global _engine
    if _engine is None:
        _engine = AdvancedScoringEngine()
    return _engine
