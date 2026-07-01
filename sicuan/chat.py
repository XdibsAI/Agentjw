"""
SiCuan Chat Interface - Wajah & Kepribadian SiCuan
"""

import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional

from core.logger import logger, console
from rich.panel import Panel
from rich.text import Text

from sicuan.brain import SiCuanBrain
from sicuan.core.personality import Personality
from sicuan.core.conversation_memory import ConversationMemory
from sicuan.core.conversation_state import ConversationState
from sicuan.core.conversation_context import ConversationContext
from sicuan.core.state_persistence import load_state, state_exists
from sicuan.core.execution_state import ExecutionState
from sicuan.core.artifact_event import ArtifactEvent, OutcomeEvent
from sicuan.core.artifact_subscribers import ArtifactSubscriberRegistry


class SiCuanChat:
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
    
    def chat(self, user_message: str) -> str:
        """Main entry - user kirim pesan, SiCuan respond"""
        
        print("[CHAT DEBUG] Step 1: Received message:", user_message[:50])
        
        # Update memory
        self.memory.add_interaction(user_message, "")
        
        # Deteksi intent
        intent = self._detect_intent(user_message)
        print(f"[CHAT DEBUG] Step 2: intent = {intent}")
        
        # Small talk
        if intent == "small_talk":
            response = self._handle_small_talk(user_message)
            self.memory.add_interaction(user_message, response)
            print("[CHAT DEBUG] Small talk response")
            return response
        
        # Memory Query
        if intent == "memory_query":
            return self._handle_memory_query(user_message)
        
        # Progress Query
        if intent == "progress_query":
            return self._handle_progress_query(user_message)
        
        # Summary Query
        if intent == "summary_query":
            return self._handle_summary_query(user_message)
        
        # Decision Query
        if intent == "decision_query":
            return self._handle_decision_query(user_message)
        
        # Knowledge Query
        if intent == "knowledge_query":
            return self._handle_knowledge_query(user_message)
        
        # Resume Query - untuk "besok lanjut", "nanti lanjut"
        if "besok" in user_message.lower() or "nanti" in user_message.lower() or "lanjut dari" in user_message.lower():
            return self._handle_resume_query(user_message)
        
        # Task
        if intent == "task":
            print("[CHAT DEBUG] Processing task...")
            
            # Check continuation
            if self._is_continuation(user_message):
                print("[CHAT DEBUG] Continuation detected")
                next_task = self.state.advance_task()
                if next_task:
                    print(f"[TASK] Advancing to: {next_task}")
                    response = self._execute_task(next_task)
                    return response
                else:
                    return "Tidak ada task yang sedang berjalan. Ada yang bisa aku bantu?"
            
            # New task - proses dengan brain
            print("[CHAT DEBUG] New task, calling brain...")
            result = self.brain.think_and_respond(user_message, self.history)
            action = result.get("action")
            print(f"[CHAT DEBUG] Brain action: {action}")
            
            # Update state sebelum eksekusi
            if action and action != "null":
                project = self._extract_project(user_message)
                if project:
                    self.state.project = project
                elif not self.state.project:
                    self.state.project = "godmeme_bot"
                self.state.last_action = action
                self.state.status = "running"
                self.state.current_task = action
                if action not in self.state.completed_tasks and action not in self.state.pending_tasks:
                    self.state.add_pending_task(action)
                print(f"[CHAT DEBUG] State before: {self.state.get_summary()[:100]}")
            
            # Eksekusi
            print("[CHAT DEBUG] Executing...")
            response = self._execute_and_format(result, user_message)
            print(f"[CHAT DEBUG] Response: {response[:100]}")
            
            # Update state setelah eksekusi
            if action and action != "null":
                print("[CHAT DEBUG] Updating state after execution...")
                self.state.last_result = response[:200] if response else "Selesai"
                self.state.status = "completed"
                self.state.add_completed_task(action)
                if action in self.state.pending_tasks:
                    self.state.pending_tasks.remove(action)
                if action == "scan_project":
                    self.state.add_pending_task("analyze_project")
                    self.state.add_pending_task("review_strategy")
                elif action == "analyze_project":
                    self.state.add_pending_task("repair_project")
                    self.state.add_pending_task("run_bot")
                elif action == "repair_project":
                    self.state.add_pending_task("run_bot")
                    self.state.add_pending_task("analyze_project")
                print(f"[CHAT DEBUG] State after: {self.state.get_summary()[:100]}")
                
                # Save artifact - publish akan otomatis save
                try:
                    from sicuan.core.artifact_event import KnowledgeEvent, DecisionEvent, CandidateAction
                    
                    event = ArtifactEvent(
                        session_id=self.session_id,
                        project=self.state.project or "",
                        action=action,
                        target=self.state.project or ""
                    )
                    
                    # Tambahkan knowledge dari result
                    if result:
                        # Extract knowledge dari result
                        knowledge_items = [
                            ("project", self.state.project or ""),
                            ("action", action),
                            ("status", "completed")
                        ]
                        for entity, value in knowledge_items:
                            if value:
                                event.knowledge.append(
                                    KnowledgeEvent(
                                        entity=entity,
                                        attribute="status",
                                        value=value,
                                        confidence=0.95,
                                        source=action
                                    )
                                )
                        print(f"[KNOWLEDGE] Added {len(event.knowledge)} knowledge items")
                    
                    # Tambahkan decision
                    event.decision = DecisionEvent(
                        selected_action=action,
                        candidate_actions=[
                            CandidateAction(action, 0.95, "Selected based on state")
                        ],
                        reason_code="TASK_EXECUTED",
                        confidence=0.95
                    )
                    print(f"[DECISION] Added decision for {action}")
                    
                    event.outcome = OutcomeEvent(
                        success=True,
                        result=str(response)[:500],
                        duration=0
                    )
                    
                    # Publish akan otomatis save ke disk
                    event.publish()
                    print(f"[ARTIFACT] Published and saved for {action}")
                except Exception as e:
                    print(f"[ARTIFACT] Error: {e}")
            
            # Update memory
            self.context.update(action=action, entity=self.state.project, intent=action, result=response[:100])
            self.memory.update(
                last_action=result.get("action"),
                last_file=self._extract_file(result)
            )
            self.memory.add_interaction(user_message, response)
            
            return response
        
        # Fallback: daripada return template "tidak paham", forward ke brain.
        # LLM punya full context (load_context) dan bisa jawab apapun
        # yang tidak dikenali routing keyword-based di atas.
        print("[CHAT DEBUG] Unknown intent — forwarding to brain as general query")
        try:
            result = self.brain.think_and_respond(user_message, self.history)
            action = result.get("action")
            response = self._execute_and_format(result, user_message)
            self.memory.add_interaction(user_message, response)
            return response
        except Exception as _e:
            print(f"[CHAT DEBUG] Brain fallback error: {_e}")
            # Fallback: daripada return template "tidak paham", forward ke brain.
        # LLM punya full context (load_context) dan bisa jawab apapun
        # yang tidak dikenali routing keyword-based di atas.
        print("[CHAT DEBUG] Unknown intent — forwarding to brain as general query")
        try:
            result = self.brain.think_and_respond(user_message, self.history)
            action = result.get("action")
            response = self._execute_and_format(result, user_message)
            self.memory.add_interaction(user_message, response)
            return response
        except Exception as _e:
            print(f"[CHAT DEBUG] Brain fallback error: {_e}")
            return "Maaf, aku belum paham maksudnya. Bisa dijelaskan lagi?"
    
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
    
    def _handle_knowledge_query(self, user_message: str) -> str:
        from sicuan.core.knowledge_query import KnowledgeQuery
        query = KnowledgeQuery()
        entity = "godmeme_bot"
        if "flask" in user_message.lower():
            entity = "flask_todo_api"
        elif "video" in user_message.lower():
            entity = "video"
        data = query.get_entity(entity)
        if not data:
            return f"Belum ada pengetahuan tentang {entity}."
        files = data.get("total_files", {}).get("value")
        functions = data.get("functions", {}).get("value")
        if "risiko" in user_message.lower() or "resiko" in user_message.lower():
            if files:
                return f"Kalau langsung melakukan analyze, risikonya adalah analisis dilakukan pada struktur project yang belum dipastikan valid. Pada scan terakhir ditemukan {files} file dalam kondisi valid, sehingga scan dipilih lebih dulu agar proses analyze menggunakan data yang sudah diverifikasi."
            return "Belum ada data scan yang cukup untuk menganalisis risiko."
        if files:
            return f"Dari scan terakhir, ditemukan {files} file dalam kondisi valid." + (f" Total fungsi: {functions}." if functions else "")
        return "Belum ada data scan yang cukup."
    
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
        self.history = []

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
