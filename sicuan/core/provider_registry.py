"""
Provider Registry — Multiple providers per capability dengan priority & fallback
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

class ProviderStatus(Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    UNKNOWN = "unknown"

@dataclass
class ProviderDefinition:
    name: str
    capability: str
    priority: int = 100
    timeout: int = 60
    retry: int = 2
    cost_per_call: float = 0.0
    status: ProviderStatus = ProviderStatus.UNKNOWN
    metadata: Dict[str, Any] = field(default_factory=dict)

class ProviderRegistry:
    """
    Registry untuk semua provider per capability dengan dynamic scoring
    """
    
    def __init__(self):
        self._providers: Dict[str, List[ProviderDefinition]] = {}
        self._init_defaults()
    
    def _init_defaults(self):
        """Initialize default providers per capability"""
        # Search providers
        self.add_provider(ProviderDefinition(
            name="hermes",
            capability="search",
            priority=100,
            timeout=60,
            retry=2,
            cost_per_call=0.001,
            metadata={"type": "llm_based"}
        ))
        self.add_provider(ProviderDefinition(
            name="tavily",
            capability="search",
            priority=80,
            timeout=30,
            retry=2,
            cost_per_call=0.002,
            metadata={"type": "api_based"}
        ))
        self.add_provider(ProviderDefinition(
            name="firecrawl",
            capability="search",
            priority=70,
            timeout=60,
            retry=3,
            cost_per_call=0.003,
            metadata={"type": "api_based"}
        ))
        
        # Vision providers
        self.add_provider(ProviderDefinition(
            name="hermes",
            capability="vision",
            priority=100,
            timeout=120,
            retry=2,
            cost_per_call=0.005,
            metadata={"type": "llm_based"}
        ))
        self.add_provider(ProviderDefinition(
            name="gemini",
            capability="vision",
            priority=90,
            timeout=60,
            retry=2,
            cost_per_call=0.003,
            metadata={"type": "api_based"}
        ))
        self.add_provider(ProviderDefinition(
            name="claude_vision",
            capability="vision",
            priority=85,
            timeout=120,
            retry=2,
            cost_per_call=0.008,
            metadata={"type": "llm_based"}
        ))
        
        # Browser providers
        self.add_provider(ProviderDefinition(
            name="hermes",
            capability="browser",
            priority=100,
            timeout=180,
            retry=3,
            cost_per_call=0.01,
            metadata={"type": "llm_based"}
        ))
        self.add_provider(ProviderDefinition(
            name="playwright",
            capability="browser",
            priority=90,
            timeout=120,
            retry=2,
            cost_per_call=0.0,
            metadata={"type": "local"}
        ))
        
        # Messaging providers
        self.add_provider(ProviderDefinition(
            name="openclaw",
            capability="messaging",
            priority=100,
            timeout=30,
            retry=2,
            cost_per_call=0.0,
            metadata={"type": "gateway"}
        ))
    
    def add_provider(self, provider: ProviderDefinition):
        """Add a provider for a capability"""
        if provider.capability not in self._providers:
            self._providers[provider.capability] = []
        self._providers[provider.capability].append(provider)
        print(f"✅ Registered provider: {provider.name} for {provider.capability}")
    
    def get_providers(self, capability: str) -> List[ProviderDefinition]:
        """Get all providers for a capability"""
        return self._providers.get(capability, [])
    
    def get_best_provider(self, capability: str, prefer: str = None) -> Optional[ProviderDefinition]:
        """Get best provider for a capability (legacy)"""
        providers = self.get_providers(capability)
        if not providers:
            return None
        
        if prefer:
            for p in providers:
                if p.name == prefer and p.status != ProviderStatus.OFFLINE:
                    return p
        
        providers.sort(key=lambda x: x.priority, reverse=True)
        for p in providers:
            if p.status != ProviderStatus.OFFLINE:
                return p
        
        return providers[0] if providers else None
    
    def calculate_score(self, provider: ProviderDefinition, health_data: Dict = None) -> float:
        """Calculate dynamic score based on multiple factors"""
        health_data = health_data or {}
        provider_health = health_data.get(provider.name, {})
        
        # Factors
        priority_score = provider.priority * 0.3
        health_score = provider_health.get("success_rate", 90) * 0.25
        latency_score = max(0, 100 - (provider_health.get("avg_latency", 1.0) * 10)) * 0.2
        cost_score = max(0, 100 - (provider.cost_per_call * 1000)) * 0.15
        availability_score = 100 if provider.status != ProviderStatus.OFFLINE else 0
        availability_score = availability_score * 0.1
        
        total = priority_score + health_score + latency_score + cost_score + availability_score
        return round(total, 2)
    
    def get_best_provider_dynamic(self, capability: str, prefer: str = None, health_data: Dict = None) -> Optional[ProviderDefinition]:
        """Get best provider using dynamic scoring"""
        providers = self.get_providers(capability)
        if not providers:
            return None
        
        if prefer:
            for p in providers:
                if p.name == prefer and p.status != ProviderStatus.OFFLINE:
                    return p
        
        scored = []
        for p in providers:
            score = self.calculate_score(p, health_data)
            scored.append((p, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0] if scored else None
    
    def update_status(self, capability: str, provider: str, status: ProviderStatus):
        """Update provider status"""
        for p in self._providers.get(capability, []):
            if p.name == provider:
                p.status = status
                break
    
    def get_all_providers(self) -> Dict:
        """Get all providers grouped by capability"""
        result = {}
        for capability, providers in self._providers.items():
            result[capability] = [
                {
                    "name": p.name,
                    "priority": p.priority,
                    "status": p.status.value,
                    "cost_per_call": p.cost_per_call,
                    "timeout": p.timeout,
                    "retry": p.retry,
                    "metadata": p.metadata
                }
                for p in providers
            ]
        return result

# Singleton
_registry = None

def get_provider_registry() -> ProviderRegistry:
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
