"""
Chat Orchestration Pipeline — Intent → Decision → Knowledge → Planning → Tool → Response
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, field

class Intent(Enum):
    CHAT = "chat"
    KNOWLEDGE = "knowledge"
    TOOL = "tool"
    PLANNING = "planning"
    MEMORY = "memory"
    UNKNOWN = "unknown"

@dataclass
class PipelineContext:
    """Context yang melewati pipeline"""
    user_message: str
    user_id: Optional[str] = None
    memory_context: str = ""
    intent: Intent = Intent.UNKNOWN
    decision: Optional[Dict] = None
    knowledge_result: Optional[str] = None
    tool_result: Optional[Dict] = None
    plan_result: Optional[str] = None
    final_response: str = ""
    should_search: bool = False
    should_execute_tool: bool = False
    confidence: float = 0.0

class OrchestrationPipeline:
    """
    Pipeline lengkap: Intent → Decision → Knowledge → Planning → Tool → Response
    """
    
    def __init__(self):
        self._init_components()
    
    def _init_components(self):
        """Initialize all components lazily"""
        self._knowledge_router = None
        self._capability_router = None
        self._execution_manager = None
    
    @property
    def knowledge_router(self):
        if self._knowledge_router is None:
            from sicuan.core.knowledge_router import get_knowledge_router
            self._knowledge_router = get_knowledge_router()
        return self._knowledge_router
    
    @property
    def capability_router(self):
        if self._capability_router is None:
            from sicuan.core.capability_router import get_capability_router
            self._capability_router = get_capability_router()
        return self._capability_router
    
    @property
    def execution_manager(self):
        if self._execution_manager is None:
            from sicuan.core.execution_manager import get_execution_manager
            self._execution_manager = get_execution_manager()
        return self._execution_manager
    
    def detect_intent(self, message: str) -> Intent:
        """Detect intent dari pesan user"""
        msg = message.lower()
        
        # Tool intent
        tool_keywords = ["kirim", "edit", "buat", "hapus", "ubah", "jalankan", "execute"]
        if any(kw in msg for kw in tool_keywords):
            return Intent.TOOL
        
        # Knowledge intent
        knowledge_keywords = ["informasi", "cari", "tentang", "apa itu", "siapa", "dimana", "kapan", "berapa", "bagaimana", "mengapa"]
        if any(kw in msg for kw in knowledge_keywords):
            return Intent.KNOWLEDGE
        
        # Planning intent
        planning_keywords = ["rencana", "plan", "strategi", "langkah", "cara", "buat plan"]
        if any(kw in msg for kw in planning_keywords):
            return Intent.PLANNING
        
        # Memory intent
        memory_keywords = ["ingat", "sebelumnya", "kemarin", "tadi", "project", "proyek"]
        if any(kw in msg for kw in memory_keywords):
            return Intent.MEMORY
        
        # Default: chat
        return Intent.CHAT
    
    def process(self, message: str, user_id: str = None, memory_context: str = "") -> Dict:
        """
        Main pipeline: process message through all stages
        """
        ctx = PipelineContext(
            user_message=message,
            user_id=user_id,
            memory_context=memory_context
        )
        
        # Stage 1: Intent Detection
        ctx.intent = self.detect_intent(message)
        print(f"[PIPELINE] Intent: {ctx.intent.value}")
        
        # Stage 2: Decision
        ctx.decision = self._make_decision(ctx)
        print(f"[PIPELINE] Decision: {ctx.decision}")
        
        # Stage 3: Knowledge (if needed)
        if ctx.decision.get("should_search"):
            ctx.knowledge_result = self._search_knowledge(ctx)
            print(f"[PIPELINE] Knowledge search performed")
        
        # Stage 4: Memory (if needed)
        if ctx.decision.get("should_use_memory") and memory_context:
            ctx.knowledge_result = memory_context
            print(f"[PIPELINE] Memory used")
        
        # Stage 5: Tool (if needed)
        if ctx.intent == Intent.TOOL or ctx.decision.get("should_execute_tool"):
            ctx.tool_result = self._execute_tool(ctx)
            print(f"[PIPELINE] Tool executed")
        
        # Stage 6: Planning (if needed)
        if ctx.intent == Intent.PLANNING:
            ctx.plan_result = self._create_plan(ctx)
            print(f"[PIPELINE] Plan created")
        
        # Stage 7: Compose Response
        ctx.final_response = self._compose_response(ctx)
        print(f"[PIPELINE] Response composed")
        
        return {
            "response": ctx.final_response,
            "intent": ctx.intent.value,
            "confidence": ctx.confidence,
            "sources": {
                "memory_used": bool(ctx.knowledge_result),
                "search_performed": ctx.decision.get("should_search", False),
                "tool_executed": bool(ctx.tool_result),
                "plan_created": bool(ctx.plan_result)
            }
        }
    
    def _make_decision(self, ctx: PipelineContext) -> Dict:
        """Make decision based on intent and context"""
        # Use Knowledge Router for decision
        decision = self.knowledge_router.should_search(
            ctx.user_message, 
            ctx.memory_context
        )
        
        return {
            "should_search": decision.should_search,
            "should_use_memory": decision.should_use_memory,
            "should_execute_tool": ctx.intent == Intent.TOOL,
            "source": decision.source,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning
        }
    
    def _search_knowledge(self, ctx: PipelineContext) -> str:
        """Execute search"""
        try:
            # Use Capability Router for search
            result = self.capability_router.route("search", {"query": ctx.user_message})
            if result.get("status") == "success":
                return result.get("result", "")
            return ""
        except Exception as e:
            print(f"[PIPELINE] Search error: {e}")
            return ""
    
    def _execute_tool(self, ctx: PipelineContext) -> Optional[Dict]:
        """Execute tool"""
        try:
            # Extract tool and params from message
            # Simple implementation: use Capability Router
            result = self.capability_router.route("tool", {
                "message": ctx.user_message,
                "user_id": ctx.user_id
            })
            return result if result.get("status") == "success" else None
        except Exception as e:
            print(f"[PIPELINE] Tool error: {e}")
            return None
    
    def _create_plan(self, ctx: PipelineContext) -> str:
        """Create plan"""
        # Simple plan creation
        return f"Rencana untuk: {ctx.user_message[:100]}..."
    
    def _compose_response(self, ctx: PipelineContext) -> str:
        """Compose final response"""
        # Priority: tool result > knowledge > memory > planning > fallback
        if ctx.tool_result:
            return ctx.tool_result.get("result", "Tool executed successfully.")
        
        if ctx.knowledge_result:
            return ctx.knowledge_result
        
        if ctx.plan_result:
            return ctx.plan_result
        
        # Fallback
        return "Saya siap membantu. Ada yang bisa saya bantu?"

# Singleton
_pipeline = None

def get_pipeline() -> OrchestrationPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = OrchestrationPipeline()
    return _pipeline
