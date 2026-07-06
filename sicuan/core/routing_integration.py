"""
Routing Integration - Menghubungkan ConversationRouter dengan chat
"""

from sicuan.core.conversation_router import ConversationRouter

class RoutingIntegration:
    def __init__(self):
        self.router = ConversationRouter()
    
    def route_message(self, user_message: str) -> dict:
        route, data = self.router.route(user_message)
        return {
            "route": route.value,
            "data": data,
            "action": data.get("action", "analyze_project")
        }

# Singleton
_routing = None

def get_routing():
    global _routing
    if _routing is None:
        _routing = RoutingIntegration()
    return _routing
