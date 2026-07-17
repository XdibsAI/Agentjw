import sys
"""
SiCuan Chat Interface - Wajah & Kepribadian SiCuan
"""

import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional

import sys
sys.path.insert(0, '/home/dibs/agentjw/core')
from core.logger import logger, console
from rich.panel import Panel
from rich.text import Text

from sicuan.brain import SiCuanBrain
from sicuan.core.routing_integration import get_routing
from sicuan.core.personality import Personality
from sicuan.core.conversation_memory import ConversationMemory
from sicuan.core.conversation_state import ConversationState
from sicuan.core.intent_classifier import IntentClassifier
from sicuan.core.semantic_query import SemanticQuery
from sicuan.core.multimodel_orchestrator import get_multimodel_orchestrator
from sicuan.core.semantic_router import get_semantic_router
from sicuan.core.context_memory import get_context_memory
from sicuan.core.conversation_context import ConversationContext
from sicuan.core.goal_engine import GoalEngine
from sicuan.core.shadow_mode import ShadowMode
from sicuan.core.provenance_engine import ProvenanceEngine
from sicuan.core.state_persistence import load_state, state_exists
from sicuan.core.execution_state import ExecutionState
from sicuan.core.artifact_event import ArtifactEvent, OutcomeEvent
from sicuan.core.artifact_subscribers import ArtifactSubscriberRegistry


class SiCuanChat:

    def _safe_get(self, data, key, default=None):
        """Safe get dari dict atau list"""
        if isinstance(data, dict):
            return data.get(key, default)
        return default

    """Wajah dan kepribadian SiCuan"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.history: List[Dict] = []
        self.brain = SiCuanBrain()
        self.personality = Personality()
        self.memory = ConversationMemory()
        
        # Load state dari file
        print("[STATE] Checking for existing state...")
        if state_exists():
            print("[STATE] State file exists, loading...")
            loaded = load_state()
            if loaded:
                self.state = loaded
                print("[STATE] ✅ Loaded existing state")
            else:
                self.state = ConversationState()
                print("[STATE] ⚠️ Load failed, using new state")
        else:
            self.state = ConversationState()
            print("[STATE] ℹ️ No state file, using new state")
        
        # Execution state
        self.execution = ExecutionState()
        self.context = ConversationContext()
        self.goal_engine = GoalEngine()
        self.shadow = ShadowMode()
        self.provenance = ProvenanceEngine()
        self._load_context()
        self._current_user_id = None
    
    def chat(self, user_message: str, image_path: str = None, user_id: int = None, workspace_id: str = None) -> str:
        # Set workspace_id ke brain
        if workspace_id:
            self.brain._current_workspace_id = workspace_id
        # Set workspace_id ke brain
        if workspace_id:
            self.brain._current_workspace_id = workspace_id
        # Set user context jika ada
        if user_id:
            self._current_user_id = user_id
            # Set user context
            from pathlib import Path
            import json
            self._user_context_file = Path(f"/home/dibs/agentjw/memory/users/{user_id}_conversation.json")
            if self._user_context_file.exists():
                try:
                    self._user_context = json.loads(self._user_context_file.read_text())
                except Exception as e:
                    self._user_context = {"topics": [], "actions": []}
            else:
                self._user_context = {"topics": [], "actions": []}
            from sicuan.core.user_manager import get_user_manager
            self._user_manager = get_user_manager()
            self._user_data = self._user_manager.get_user_data(user_id)
        else:
            self._user_manager = None
            self._user_data = None
        """Main entry - semua pesan langsung ke brain (semantic routing).
        LLM yang decide intent dan action, bukan keyword matching.
        Jika ada image_path, proses gambar dulu."""
        
        # Jika ada gambar, proses dulu
        if image_path:
            print(f"[CHAT] 📸 Processing image: {image_path}")
            return self.brain.process_image(image_path, user_message)
        
        print("[CHAT] Received:", user_message[:60])
        
        # === SHORTCUT: AUTO-REPAIR ===
        if "plan" in user_message.lower() or "buat plan" in user_message.lower():
            try:
                from sicuan.core.planning import create_plan
                plan = create_plan(user_message)
                # Extract steps
                steps = user_message.split(":")[1].split(",") if ":" in user_message else ["Analisis", "Eksekusi", "Verifikasi"]
                for step in steps:
                    plan.add_step(step.strip())
                return plan.to_string()
            except Exception as e:
                return f"❌ Error creating plan: {str(e)}"
        
        if "auto-repair" in user_message.lower() or "repair godmeme" in user_message.lower():
            try:
                from sicuan.core.generalized_repair import get_generalized_repair
                from pathlib import Path
                repair = get_generalized_repair()
                project_dir = Path("/home/dibs/agentjw/projects/godmeme_bot")
                log_file = project_dir / "trading_bot_live.log"
                error = repair.detect_error(log_file)
                if error:
                    result = repair.repair(project_dir, error)
                    return f"🔧 Auto-repair: {result.get('message', 'Done')}\n\nRestart bot..."
                return "✅ No error detected in logs"
            except Exception as e:
                return f"❌ Auto-repair failed: {str(e)}"

        # Update memory
        self.memory.add_interaction(user_message, "")

        # Shortcut: pesan sangat pendek (1-2 karakter) → tanya balik
        if len(user_message.strip()) <= 2:
            return "Halo! Ada yang bisa aku bantu?"

        # === SEMANTIC ROUTER - PRIORITAS ===
        try:
            # Convert history ke format yang diharapkan semantic router
            history_for_router = []
            if self.history:
                for h in self.history:
                    if isinstance(h, dict):
                        history_for_router.append(h)
                    else:
                        history_for_router.append({"topic": str(h)})
            
            router = get_semantic_router()
            context_summary = self.brain.load_context(user_message) if hasattr(self.brain, 'load_context') else ""
            route_result = router.route(user_message, context_summary, history_for_router)
            # route_result bisa string (dari llm.chat) atau dict
            if isinstance(route_result, dict):
                routed_action = route_result.get("action", "")
                if routed_action and routed_action != "null" and routed_action != "":
                    print(f"[ROUTER] Semantic routing: {routed_action} ({route_result.get('confidence', 0)})")
                    self.brain._routed_action = routed_action
                    self.brain._routed_target = ""
            elif isinstance(route_result, str):
                # Jika route_result adalah string, coba parse atau fallback
                print(f"[ROUTER] Semantic router returned string: {route_result[:100]}")
                # Fallback: cari action di string
                if "auto" in route_result.lower() and "repair" in route_result.lower():
                    self.brain._routed_action = "auto_repair_project"
                    self.brain._routed_target = ""
                elif "godmeme" in route_result.lower():
                    self.brain._routed_action = "godmeme_status"
                    self.brain._routed_target = ""
                elif "project" in route_result.lower():
                    self.brain._routed_action = "list_projects"
                    self.brain._routed_target = ""
            else:
                print(f"[ROUTER] Invalid route_result type: {type(route_result)}")
        except Exception as e:
            print(f"[ROUTER] Semantic error: {e}")
        
        # Fallback: orchestrator
        # Semua pesan → brain (LLM decide intent + action)
        try:
            # Route to appropriate model via orchestrator
            orchestrator = get_multimodel_orchestrator()
            
            # Check context for continuation keywords
            continuation_keywords = ["perbaiki", "lanjutkan", "ringkas", "hasilnya", "sekarang", "terus"]
            if any(kw in user_message.lower() for kw in continuation_keywords) and len(self.history) > 2:
                # Use last action to determine role
                last_action = self.brain._last_action if hasattr(self.brain, '_last_action') else None
                if last_action in ["analyze_project", "analyzer"]:
                    role = "analyzer"
                elif last_action in ["modify_logic", "repair_project", "coder"]:
                    role = "coder"
                elif last_action in ["review", "reviewer"]:
                    role = "reviewer"
                else:
                    role = orchestrator.route_task(user_message)
                logger.info(f"[CHAT] Context-aware routing: {role} (last_action: {last_action})")
            else:
                role = orchestrator.route_task(user_message)
                logger.info(f"[CHAT] Orchestrator selected: {role}")
        
            # === INTERCEPT: List project ===
            if "list project" in user_message.lower() or "daftar project" in user_message.lower():
                if not workspace_id and hasattr(self, 'brain') and hasattr(self.brain, '_current_workspace_id'):
                    workspace_id = self.brain._current_workspace_id
                if workspace_id:
                    from sicuan.platform.project_manager import get_project_manager
                    pm = get_project_manager()
                    projects = pm.list_projects(workspace_id)
                    if projects:
                        lines = ["📂 PROJECTS IN YOUR WORKSPACE:"]
                        for p in projects[:10]:
                            lines.append(f"• {p['name']}")
                            lines.append(f"  Status: {p.get('status', 'active')}")
                        return "\n".join(lines)
                    else:
                        return "📂 Belum ada project di workspace ini.\n\nKetik 'buat project <nama>' untuk memulai."
                else:
                    return "📂 Workspace tidak ditemukan. Kirim pesan ke bot terlebih dahulu."
            
            # === INTERCEPT: Create project ===
            if "buat project" in user_message.lower() or "create project" in user_message.lower():
                if not workspace_id and hasattr(self, 'brain') and hasattr(self.brain, '_current_workspace_id'):
                    workspace_id = self.brain._current_workspace_id
                if workspace_id:
                    from sicuan.platform.project_manager import get_project_manager
                    import re
                    pm = get_project_manager()
                    match = re.search(r'(?:buat|create)\s+project\s+(\w+)', user_message.lower())
                    if match:
                        project_name = match.group(1).capitalize()
                        projects = pm.list_projects(workspace_id)
                        for p in projects:
                            if p["name"].lower() == project_name.lower():
                                return f"❌ Project '{project_name}' sudah ada."
                        project = pm.create_project(workspace_id, project_name)
                        return f"✅ Project '{project_name}' berhasil dibuat!\n\n📂 ID: {project['id']}"
                    else:
                        return "❌ Format salah.\n\nGunakan: buat project <nama>"
                else:
                    return "📂 Workspace tidak ditemukan."
            
            # Pass selected model to brain directly
            selected_model = None
            if hasattr(self, '_selected_model'):
                selected_model = self._selected_model
            result = self.brain.think_and_respond(user_message, self.history, force_model=selected_model, user_id=str(user_id) if user_id else None)
            # Normalisasi result
            if isinstance(result, list):
                result = result[0] if result else {}
            if not isinstance(result, dict):
                result = {"response": str(result), "action": None}
        except Exception as e:
            import traceback
            print(f"[CHAT] Brain error full trace:")
            traceback.print_exc()
            return "Waduh, ada yang ga beres sebentar. Coba lagi ya Mas."

        action = self._safe_get(result, "action")
        intent = self._safe_get(result, "intent", "unknown")
        print(f"[CHAT] Brain decided: action={action}")

        # === PROVENANCE: Catat keputusan ===
        try:
            if hasattr(self, 'provenance') and action and action != "null":
                self.provenance.record_decision(
                    action=action,
                    target=self.state.project or "unknown",
                    source_type="llm",
                    source_details={
                        "intent": intent,
                        "confidence": result.get('confidence', 0.9) if isinstance(result, dict) else 0.9
                    },
                    input_data={"user_message": user_message[:200]},
                    output_data={"action": action, "target": self.state.project or "unknown"},
                    reasoning=[f"LLM decided: {action} with intent {intent}"],
                    confidence=result.get('confidence', 0.9) if isinstance(result, dict) else 0.9,
                    session_id=self.session_id
                )
                print(f"[PROVENANCE] ✅ Recorded: {action}")
        except Exception as e:
            print(f"[PROVENANCE] Error: {e}")

        # === HANDLE MEMORY/CONTEXT QUERY ===
        if action == "memory_query" or action == "context_query":
            try:
                ctx = self.context.get_context()
                if ctx:
                    last_topic = ctx.get('last_topic', 'N/A')
                    response = "Dari percakapan sebelumnya: " + str(last_topic)
                    if hasattr(self.context, 'topics') and self.context.topics:
                        recent = self.context.topics[-3:]
                        response = response + "\n\nTopik terakhir: " + ", ".join(recent)
                else:
                    response = "Belum ada percakapan sebelumnya."
                return response
            except Exception as e:
                print("[MEMORY] Error:", e)
                return "Maaf, aku tidak bisa mengakses memory saat ini."
        
        # Normalisasi result: brain kadang return list bukan dict
        if isinstance(result, list):
            result = result[0] if result else {}
        if not isinstance(result, dict):
            result = {"response": str(result), "action": None}

        # Execute dan format response
        response = self._execute_and_format(result, user_message)

        # Update memory dan state
        self.memory.add_interaction(user_message, response)
        if action and action != "null" and isinstance(result, dict):
            project = self._extract_project(user_message)
            if project:
                self.state.project = project
        
        # === UPDATE CONTEXT ===
        try:
            if action and action != "null":
                # Extract entity/target dari result
                target = result.get("target", "") if isinstance(result, dict) else ""
                self.context.update(
                    topic=user_message[:100],
                    action=action,
                    entity=target if target else None,
                    intent=result.get("intent", "unknown") if isinstance(result, dict) else None,
                    result=response[:200] if response else None
                )
                print(f"[CONTEXT] Updated: action={action}, topic={self.context.last_topic}")
            else:
                # Untuk greeting/small talk, update topic saja
                self.context.update(topic=user_message[:100])
                print(f"[CONTEXT] Updated topic: {self.context.last_topic}")
            
            # Save context ke disk
            self._save_context()
        except Exception as e:
            print(f"[CONTEXT] Failed to update: {e}")
            self.state.last_action = action
            self.state.status = "completed"
            self.state.add_completed_task(action)
            try:
                from sicuan.core.state_persistence import save_state
                save_state(self.state)
            except Exception:
                pass

            self._save_context()
        return response

    def _handle_knowledge_query(self, user_message: str) -> str:
        """Forward ke brain — LLM jawab dari context nyata."""
        try:
            # Route to appropriate model via orchestrator
            orchestrator = get_multimodel_orchestrator()
            
            # Check context for continuation keywords
            continuation_keywords = ["perbaiki", "lanjutkan", "ringkas", "hasilnya", "sekarang", "terus"]
            if any(kw in user_message.lower() for kw in continuation_keywords) and len(self.history) > 2:
                # Use last action to determine role
                last_action = self.brain._last_action if hasattr(self.brain, '_last_action') else None
                if last_action in ["analyze_project", "analyzer"]:
                    role = "analyzer"
                elif last_action in ["modify_logic", "repair_project", "coder"]:
                    role = "coder"
                elif last_action in ["review", "reviewer"]:
                    role = "reviewer"
                else:
                    role = orchestrator.route_task(user_message)
                logger.info(f"[CHAT] Context-aware routing: {role} (last_action: {last_action})")
            else:
                role = orchestrator.route_task(user_message)
                logger.info(f"[CHAT] Orchestrator selected: {role}")
        
            # === INTERCEPT: List project ===
            if "list project" in user_message.lower() or "daftar project" in user_message.lower():
                if not workspace_id and hasattr(self, 'brain') and hasattr(self.brain, '_current_workspace_id'):
                    workspace_id = self.brain._current_workspace_id
                if workspace_id:
                    from sicuan.platform.project_manager import get_project_manager
                    pm = get_project_manager()
                    projects = pm.list_projects(workspace_id)
                    if projects:
                        lines = ["📂 PROJECTS IN YOUR WORKSPACE:"]
                        for p in projects[:10]:
                            lines.append(f"• {p['name']}")
                            lines.append(f"  Status: {p.get('status', 'active')}")
                        return "\n".join(lines)
                    else:
                        return "📂 Belum ada project di workspace ini.\n\nKetik 'buat project <nama>' untuk memulai."
                else:
                    return "📂 Workspace tidak ditemukan. Kirim pesan ke bot terlebih dahulu."
            
            # === INTERCEPT: Create project ===
            if "buat project" in user_message.lower() or "create project" in user_message.lower():
                if not workspace_id and hasattr(self, 'brain') and hasattr(self.brain, '_current_workspace_id'):
                    workspace_id = self.brain._current_workspace_id
                if workspace_id:
                    from sicuan.platform.project_manager import get_project_manager
                    import re
                    pm = get_project_manager()
                    match = re.search(r'(?:buat|create)\s+project\s+(\w+)', user_message.lower())
                    if match:
                        project_name = match.group(1).capitalize()
                        projects = pm.list_projects(workspace_id)
                        for p in projects:
                            if p["name"].lower() == project_name.lower():
                                return f"❌ Project '{project_name}' sudah ada."
                        project = pm.create_project(workspace_id, project_name)
                        return f"✅ Project '{project_name}' berhasil dibuat!\n\n📂 ID: {project['id']}"
                    else:
                        return "❌ Format salah.\n\nGunakan: buat project <nama>"
                else:
                    return "📂 Workspace tidak ditemukan."
            
            # Pass selected model to brain directly
            selected_model = None
            if hasattr(self, '_selected_model'):
                selected_model = self._selected_model
            result = self.brain.think_and_respond(user_message, self.history, force_model=selected_model, user_id=str(user_id) if user_id else None)
            response = self._execute_and_format(result, user_message)
            self.memory.add_interaction(user_message, response)
            self._save_context()
            return response
        except Exception as e:
            return f"Tidak bisa mengambil informasi saat ini. ({e})"

    def _extract_project(self, user_message: str) -> Optional[str]:
        """Extract project dari user message"""
        match = re.search(r'(godmeme|flask|video)', user_message.lower())
        if match:
            return match.group(1)
        return None
        
    def _extract_file(self, result: dict) -> Optional[str]:
        """Extract file dari result"""
        target = result.get("action_target", "")
        if target and ":" in target:
            return target.split(":")[1].strip()
        return None
    
    
        """Handle progress query"""
        return self.state.get_summary() if self.state else "Belum ada pekerjaan yang dimulai."
    
    def _handle_summary_query(self, user_message: str) -> str:
        """Handle summary query - dengan Response Composer"""
        from sicuan.core.response_composer_final import ResponseComposerFinal
        return ResponseComposer.compose_summary({
            "project": self.state.project if self.state else None,
            "current_task": self.state.current_task if self.state else None,
            "completed_tasks": self.state.completed_tasks if self.state else [],
            "pending_tasks": self.state.pending_tasks if self.state else []
        })
    
    def _handle_decision_query(self, user_message: str) -> str:
        from sicuan.core.decision_query import DecisionQuery
        query = DecisionQuery()
        action = "scan_project"
        if "analyze" in user_message.lower():
            action = "analyze_project"
        elif "repair" in user_message.lower():
            action = "repair_project"
        decision = query.get_latest(action)
        if not decision:
            return f"Belum ada keputusan tentang {action}."
        reason_code = decision.get("reason", "")
        confidence = decision.get("confidence", 0)
        if reason_code == "PROJECT_NOT_SCANNED":
            return f"Aku memilih {action} karena project belum memiliki hasil scan yang valid. Kalau langsung masuk ke tahap analisis, ada risiko analisis dilakukan berdasarkan struktur project yang belum diverifikasi. Keyakinan keputusan: {confidence:.0f}%."
        elif reason_code == "SCAN_COMPLETED":
            return f"Aku memilih {action} karena scan sudah selesai dan hasilnya valid. Langkah ini melanjutkan alur kerja. Keyakinan keputusan: {confidence:.0f}%."
        else:
            return f"Aku memilih {action} berdasarkan alur kerja yang sudah direncanakan. Keyakinan keputusan: {confidence:.0f}%."
    
    def _handle_resume_query(self, user_message: str) -> str:
        """Handle resume query - dengan Response Composer"""
        from sicuan.core.response_composer_final import ResponseComposerFinal
        return ResponseComposer.compose_resume({
            "project": self.state.project if self.state else None,
            "current_task": self.state.current_task if self.state else None,
            "completed_tasks": self.state.completed_tasks if self.state else [],
            "pending_tasks": self.state.pending_tasks if self.state else []
        })
    def _detect_intent(self, user_message: str) -> str:
        """Deteksi intent dari pesan user"""
        message_lower = user_message.lower()
        
        if not message_lower:
            return "unknown"
        
        # Memory query - HARUS PERTAMA (sebelum small_talk)
        memory_patterns = ["masih ingat", "ingat", "terakhir", "kemarin", "sebelumnya", "yang tadi", "tadi", "besok", "nanti", "lanjut dari", "mulai dari", "ingat gak", "apa terakhir"]
        for pattern in memory_patterns:
            if pattern in message_lower:
                return "memory_query"
        
        # Small talk
        small_talk_patterns = [
            "halo", "hai", "hi", "hello", "selamat", "apa kabar",
            "cuaca", "bagaimana", "terima kasih", "makasih",
            "pagi", "siang", "malam", "salam", "terima kasih"
        ]
        for pattern in small_talk_patterns:
            if pattern in message_lower:
                return "small_talk"
        
        # Progress query - "sampai mana", "progress", "sejauh mana", "perkembangan"
        progress_patterns = ["sampai mana", "progress", "sejauh mana", "perkembangan", "status", "pending"]
        for pattern in progress_patterns:
            if pattern in message_lower:
                return "progress_query"
        
        # Summary query - "ringkas", "rangkum", "resume", "intisari"
        summary_patterns = ["ringkas", "rangkum", "resume", "intisari", "kesimpulan"]
        for pattern in summary_patterns:
            if pattern in message_lower:
                return "summary_query"
        
        # Decision query - "kenapa", "mengapa", "alasan"
        decision_patterns = ["kenapa", "mengapa", "alasan", "kok"]
        for pattern in decision_patterns:
            if pattern in message_lower:
                return "decision_query"
        
        # Knowledge query - "berapa", "jumlah", "total"
        knowledge_patterns = ["berapa", "jumlah", "total", "ada berapa"]
        for pattern in knowledge_patterns:
            if pattern in message_lower:
                return "knowledge_query"
        
        # Task/Execution
        task_patterns = [
            "scan", "analyze", "analisa", "trace", "modify", "repair",
            "build", "run", "cek", "lihat", "tampilkan", "perbaiki",
            "godmeme", "flask", "project", "bot", "trading",
            "log", "file", "code", "debug", "test", "deploy",
            "lanjut", "next", "continue", "gas", "ayo", "oke",
            # prioritas & fokus — supaya "apa prioritas sekarang" tidak jatuh ke unknown
            "prioritas", "fokus", "tugas", "task", "antrian", "kerjakan",
            "agenda", "rencana", "jadwal", "target"
        ]
        for pattern in task_patterns:
            if pattern in message_lower:
                # Cek apakah ini pertanyaan (bukan perintah)
                if "?" in user_message or any(p in message_lower for p in ["apa", "bagaimana", "kenapa"]):
                    return "knowledge_query"
                return "task"
        
        return "unknown"
    
    def _is_continuation(self, user_message: str) -> bool:
        """Cek apakah user meminta lanjut"""
        words = user_message.lower().split()
        if len(words) > 3:
            return False
        
        patterns = ["lanjut", "teruskan", "next", "continue", "gas", "ayo", "oke", "ya"]
        return any(p in user_message.lower() for p in patterns)
    
    def _execute_task(self, action: str) -> str:
        """Eksekusi task tertentu"""
        try:
            # Validasi action ada di registry
            if not self.brain.registry.has(action):
                available = ', '.join(self.brain.registry.list_actions()[:10])
                return f"❌ Action '{action}' tidak dikenal. Action yang tersedia: {available}..."
            
            print(f"[TASK] Executing: {action}")
            result = self.brain.execute_action(
                action,
                self.state.project or "",
                f"Execute {action}",
                self.session_id
            )
            # Mark task as completed
            self.state.add_completed_task(action)
            if action in self.state.pending_tasks:
                self.state.pending_tasks.remove(action)
            
            # Update current_task ke task berikutnya atau None
            if self.state.pending_tasks:
                self.state.current_task = self.state.pending_tasks[0]
            else:
                self.state.current_task = None
            print(f"[TASK] Current task updated to: {self.state.current_task}")
            
            # Save state ke file
            try:
                from sicuan.core.state_persistence import save_state
                save_state(self.state)
                print(f"[STATE] ✅ State saved after {action}")
            except Exception as e:
                print(f"[STATE] ❌ Failed to save state: {e}")
            
            # Save artifact
            try:
                event = ArtifactEvent(
                    session_id=self.session_id,
                    project=self.state.project or "",
                    action=action,
                    target=self.state.project or ""
                )
                event.outcome = OutcomeEvent(
                    success=True,
                    result=str(result)[:500],
                    duration=0
                )
                registry = ArtifactSubscriberRegistry()
                registry.publish(event)
                print(f"[ARTIFACT] Saved for {action}")
            except Exception as e:
                print(f"[ARTIFACT] Error: {e}")
            
            # Advance to next task
            next_task = self.state.advance_task()
            if next_task:
                print(f"[TASK] Next task: {next_task}")
            else:
                print("[TASK] No more pending tasks")
            print(f"[TASK] Remaining: {self.state.pending_tasks}")
            return result or f"✅ {action} selesai"
        except Exception as e:
            return f"❌ Gagal menjalankan {action}: {e}"
    
    def _execute_and_format(self, result: dict, user_message: str) -> str:
        """Eksekusi dan format response"""
        # Guard: pastikan result selalu dict
        if isinstance(result, list):
            result = result[0] if result and isinstance(result[0], dict) else {}
        if not isinstance(result, dict):
            result = {"response": str(result) if result else "Task selesai", "action": None}
        action = result.get("action")
        response = result.get("response", "Task selesai")
        
        if action and action != "null":
            try:
                exec_result = self.brain.execute_action(
                    action,
                    result.get("action_target", ""),
                    user_message,
                    self.session_id
                )
                return f"{response}\n\n{exec_result}"
            except Exception as e:
                return f"{response}\n\n⚠️ Gagal menjalankan action: {e}"
        
            self._save_context()
        return response
    
    def _handle_small_talk(self, user_message: str) -> str:
        """Handle small talk"""
        message_lower = user_message.lower()
        
        if any(w in message_lower for w in ["halo", "hai", "hi"]):
            return "Halo juga! Ada yang bisa aku bantu hari ini?"
        
        if "apa kabar" in message_lower:
            return "Baik-baik saja! Siap membantu kapan saja."
        
        if any(w in message_lower for w in ["terima kasih", "makasih"]):
            return "Sama-sama! Senang bisa membantu."
        
        return "Halo! Ada yang bisa aku kerjakan?"
    
    def get_context(self) -> str:
        """Dapatkan konteks percakapan"""
        return self.memory.get_context()
    
    def reset(self):
        """Reset chat"""
        self.memory = ConversationMemory()
        self.state = ConversationState()
        self.execution = ExecutionState()
        self.context = ConversationContext()
        self.goal_engine = GoalEngine()
        self.shadow = ShadowMode()
        self.provenance = ProvenanceEngine()
        self._load_context()
        self._current_user_id = None
        self.history = []
        self._current_user_id = None

    def _handle_memory_query(self, user_message: str) -> str:
        if not self.state:
            return "Belum ada pekerjaan yang tersimpan."
        
        project = self.state.project or "Tidak ada"
        current = self.state.current_task or "Tidak ada"
        completed = self.state.completed_tasks or []
        pending = self.state.pending_tasks or []
        
        # Resume query (besok lanjut)
        if "besok" in user_message.lower() or "nanti" in user_message.lower() or "lanjut dari" in user_message.lower():
            if pending:
                return f"Kalau kita lanjut besok, aku akan mulai dari {pending[0]}. Hari ini {project} sudah selesai dikerjakan untuk {current}. Task berikutnya adalah: {', '.join(pending)}"
            elif completed:
                return f"Progress terakhir berhenti setelah {completed[-1]}. Tidak ada task pending untuk {project}."
            return "Belum ada progress yang tersimpan."
        
        # Memory query
        if completed:
            last = completed[-1]
            result = f"Terakhir kita mengerjakan {last} pada project {project}."
            if pending:
                result += f" Selanjutnya: {pending[0]}"
            if len(pending) > 1:
                result += f" Tersisa: {', '.join(pending[1:])}"
            return result
        
        return "Aku belum ingat ada pekerjaan terakhir. Ada yang mau kita kerjakan?"

    def _handle_progress_query(self, user_message: str) -> str:
        """Handle progress query"""
        if not self.state:
            return "Belum ada pekerjaan yang dimulai."
        
        # Gunakan state yang sudah ada
        project = self.state.project or "Tidak ada"
        current = self.state.current_task or "Tidak ada"
        completed = self.state.completed_tasks or []
        pending = self.state.pending_tasks or []
        
        lines = [
            f"📊 Progress untuk {project}:",
            f"  ✅ Selesai: {', '.join(completed) if completed else 'Belum ada'}",
            f"  🔄 Sedang: {current}",
            f"  📌 Tersisa: {', '.join(pending) if pending else 'Tidak ada'}"
        ]
        return "\n".join(lines)

    def _handle_semantic_query(self, user_message: str) -> str:
        """Handle query secara semantic - tidak hardcoded"""
        try:
            from sicuan.core.semantic_query import SemanticQuery
            
            context = {
                "project": self.state.project if self.state else "godmeme_bot",
                "history": self.history[-5:] if self.history else []
            }
            
            result = SemanticQuery.understand(user_message, context)
            
            # Jika result tidak valid, fallback ke brain
            if not result or not result.get("response"):
                return self.brain.think_and_respond(user_message, self.history)
            
            return result.get("response", "Maaf, aku belum bisa menjawab.")
            
        except Exception as e:
            print(f"[SEMANTIC] Error: {e}")
            # Fallback ke brain jika semantic gagal
            return self.brain.think_and_respond(user_message, self.history)

    def _save_context(self):
        """Auto-save conversation context per user"""
        print(f"[CONTEXT] SAVE: user_id={getattr(self, '_current_user_id', 'NOT_SET')}")
        try:
            import json
            from pathlib import Path
            from datetime import datetime
            
            user_id = getattr(self, '_current_user_id', None)
            if user_id:
                user_context_file = Path(f"/home/dibs/agentjw/memory/users/{user_id}_conversation.json")
                # Load existing
                if user_context_file.exists():
                    user_data = json.loads(user_context_file.read_text())
                else:
                    user_data = {"user_id": str(user_id), "topics": [], "actions": [], "updated_at": ""}
                
                # Update dengan data terakhir
                if hasattr(self, 'context'):
                    if hasattr(self.context, 'last_topic') and self.context.last_topic:
                        user_data["last_topic"] = self.context.last_topic
                        topics = user_data.get("topics", [])
                        topics.append(self.context.last_topic)
                        if len(topics) > 50:
                            topics = topics[-50:]
                        user_data["topics"] = topics
                    
                    if hasattr(self.context, 'last_action') and self.context.last_action:
                        user_data["last_action"] = self.context.last_action
                        actions = user_data.get("actions", [])
                        actions.append(self.context.last_action)
                        if len(actions) > 50:
                            actions = actions[-50:]
                        user_data["actions"] = actions
                
                user_data["updated_at"] = datetime.now().isoformat()
                user_context_file.write_text(json.dumps(user_data, indent=2))
            else:
                # Fallback ke global
                if hasattr(self, 'context') and hasattr(self.context, 'save'):
                    self.context.save("memory")
        except Exception as e:
            print(f"[CONTEXT] Failed to save: {e}")
    
    def _load_context(self):
        """Auto-load conversation context"""
        try:
            if hasattr(self, 'context') and hasattr(self.context, 'load'):
                self.context.load("memory")
        except Exception as e:
            print(f"[CONTEXT] Failed to load: {e}")

    def _handle_self_review(self, user_message: str) -> str:
        """Handle self-review request"""
        from sicuan.core.self_review import get_self_review_report
        return get_self_review_report()

    def route_message(self, user_message: str) -> dict:
        """Route message menggunakan ConversationRouter"""
        routing = get_routing()
        return routing.route_message(user_message)

# Singleton instance
_chat_session_instance = None

def get_chat_session():
    """Get singleton chat session instance"""
    global _chat_session_instance
    if _chat_session_instance is None:
        _chat_session_instance = SiCuanChat()
    return _chat_session_instance
