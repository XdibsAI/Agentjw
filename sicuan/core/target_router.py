"""
Target Router — Routing berbasis target dengan scoring
"""

from typing import Dict, List, Optional
from sicuan.core.target_resolver import get_target_resolver


def resolve_target(user_request: str, candidates: List[Dict]) -> Optional[Dict]:
    """Resolve target dengan scoring"""
    resolver = get_target_resolver()
    return resolver.resolve(user_request, candidates)
