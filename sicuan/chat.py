"""
SiCuan Chat Interface - Wajah & Kepribadian SiCuan
"""

import uuid
import re
from pathlib import Path
from typing import List, Dict, Optional, Any

from core.logger import logger, console
from rich.panel import Panel
from rich.text import Text

from sicuan.brain import SiCuanBrain
from sicuan.core.personality import Personality
from sicuan.core.conversation_memory import ConversationMemory
from sicuan.core.conversation_state import ConversationState
from sicuan.core.conversation_reasoner import ConversationReasoner, IntentType
from sicuan.core.execution_state import ExecutionState
from sicuan.core.state_persistence import load_state, state_exists


class SiCuanChat:
    """Wajah dan kepribadian SiCuan"""
    
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.history: List[Dict] = []
        self.brain = SiCuanBrain()
        self.personality = Personality()
        self.memory = ConversationMemory()
        
        # Load state dari file
        try:
            from sicuan.core.state_persistence import load_state, state_exists
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
        except Exception as e:
            print(f"[STATE] ❌ Error loading state: {e}")
            self.state = ConversationState()
        
        # Execution state
        self.execution = ExecutionState()
        self.reasoner = ConversationReasoner(self.state, self.execution, None)

    def chat(self, user_message: str) -> str:
        """Main entry - user kirim pesan, SiCuan respond"""
        
        print("[CHAT DEBUG] Step 1: Received message:", user_message[:50])
        
        # Update memory
        self.memory.add_interaction(user_message, "")
        
        # Deteksi intent
        intent = self._detect_intent(user_message)
        print(f"[CHAT DEBUG] Step 2: intent = {intent}")
        
        # Gunakan Conversation Reasoner
        intent = self.reasoner.classify(user_message)
        print(f"[REASONER] Intent: {intent.intent.value} (confidence: {intent.confidence})")
        
        # Jika intent bukan action, generate response dari reasoner
        if intent.intent != IntentType.ACTION and intent.intent != IntentType.FALLBACK:
            response = self.reasoner.generate_response(intent, user_message)
            if response:
                return response
        if reference_response:
            return reference_response
        
        # Handle natural commands
        command_response = self._handle_natural_command(user_message)
        if reference_response:
            return reference_response
        
        # Small talk
        if intent == "small_talk":
            response = self._handle_small_talk(user_message)
            self.memory.add_interaction(user_message, response)
            print("[CHAT DEBUG] Small talk response")
            return response
        
        # Task
        if intent == "task":
            print("[CHAT DEBUG] Processing task...")
            
            # Continuation
            if self._is_continuation(user_message):
                print("[CHAT DEBUG] Continuation detected")
                print(f"[TASK] Current pending: {self.state.pending_tasks}")
                next_task = self.state.advance_task()
                if next_task:
                    print(f"[TASK] Advancing to: {next_task}")
                    response = self._execute_task(next_task)
                    return response
                else:
                    return "Tidak ada task yang sedang berjalan. Ada yang bisa aku bantu?"
            
            # Proses dengan brain
            print("[CHAT DEBUG] Calling brain...")
            result = self.brain.think_and_respond(user_message, self.history)
            action = result.get("action")
            print(f"[CHAT DEBUG] Brain action: {action}")
            
            # Update state SEBELUM eksekusi
            if action and action != "null":
                print("[CHAT DEBUG] Updating state before execution...")
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
                
                # Update execution state
                self.execution.start(action, 1)
                self.execution.current_step = action
                self.execution.progress(action)  # Progress 1/1
                print(f"[CHAT DEBUG] Execution started: {action}")
            
            # Eksekusi
            print("[CHAT DEBUG] Executing...")
            response = self._execute_and_format(result, user_message)
            print(f"[CHAT DEBUG] Response: {response[:100]}")
            
            # Update state SETELAH eksekusi
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
                
                # Update execution state
                self.execution.complete()
                self.execution.current_step = action
                print(f"[CHAT DEBUG] Execution completed: {action}")
            
            self.memory.update(
                last_action=result.get("action"),
                last_file=self._extract_file(result)
            )
            self.memory.add_interaction(user_message, response)
            
            return response
        
        return "Maaf, aku belum paham maksudnya. Bisa dijelaskan lagi?"
    

    def _handle_reference(self, user_message: str) -> Optional[str]:
        """Handle referensi seperti 'yang tadi', 'itu', 'kemarin'"""
        message_lower = user_message.lower()
        
        # Referensi ke hasil terakhir
        if any(k in message_lower for k in ["yang tadi", "tadi", "itu", "kemarin"]):
            if self.state.last_result:
                return f"Hasil terakhir: {self.state.last_result[:200]}"
            elif self.state.last_action:
                return f"Kamu terakhir menjalankan: {self.state.last_action}"
            else:
                return "Belum ada hasil terakhir yang tersimpan."
        
        return None
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
    
    def _detect_intent(self, user_message: str) -> str:
        """Deteksi intent dari pesan user"""
        message_lower = user_message.lower()
        
        if not message_lower:
            return "unknown"
        
        small_talk_patterns = [
            "halo", "hai", "hi", "hello", "selamat", "apa kabar",
            "cuaca", "bagaimana", "terima kasih", "makasih",
            "pagi", "siang", "malam", "salam"
        ]
        
        for pattern in small_talk_patterns:
            if pattern in message_lower:
                return "small_talk"
        
        task_patterns = [
            "scan", "analyze", "analisa", "trace", "modify", "repair",
            "build", "run", "cek", "lihat", "tampilkan", "perbaiki",
            "godmeme", "flask", "project", "bot", "trading", "status",
            "log", "file", "code", "debug", "test", "deploy",
            "lanjut", "next", "continue", "gas", "ayo", "oke"
        ]
        
        for pattern in task_patterns:
            if pattern in message_lower:
                return "task"
        
        return "unknown"
    
    def _is_continuation(self, user_message: str) -> bool:
        """Cek apakah user meminta lanjut"""
        message_lower = user_message.lower()
        
        # Deteksi kata kunci lanjut
        keywords = ["lanjut", "terus", "next", "continue", "gas", "ayo", "oke"]
        if any(k in message_lower for k in keywords):
            return True
        
        # Deteksi "lagi" dalam konteks lanjut
        if "lagi" in message_lower:
            # Cek apakah ada kata "lanjut" atau "terus" sebelumnya
            if "lanjut" in message_lower or "terus" in message_lower:
                return True
            # Atau jika pesan pendek (1-2 kata) dan mengandung "lagi"
            words = message_lower.split()
            if len(words) <= 2 and "lagi" in message_lower:
                return True
        
        return False
    
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
            # Mark task as completed in state
            self.state.add_completed_task(action)
            if action in self.state.pending_tasks:
                self.state.pending_tasks.remove(action)
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
        self.reasoner = ConversationReasoner(self.state, self.execution, None)
        self.history = []

    def _handle_natural_command(self, user_message: str) -> Optional[str]:
        """Handle natural commands seperti 'kenapa', 'sudah sampai mana', 'ringkas'"""
        message_lower = user_message.lower()
        
        # 1. "kenapa" / "mengapa" / "alasan"
        if any(k in message_lower for k in ["kenapa", "mengapa", "alasan"]):
            if self.state.last_action:
                return f"Alasan saya memilih {self.state.last_action}:\n\nKarena berdasarkan analisis state, langkah ini adalah yang paling sesuai untuk mencapai tujuan. Saya melihat {self.state.last_action} sebagai prioritas karena:\n1. Ini adalah langkah yang diperlukan untuk melanjutkan pekerjaan\n2. Task queue menunjukkan ini adalah langkah berikutnya\n3. Hasil sebelumnya ({self.state.last_result[:100]}...) menunjukkan bahwa ini adalah arah yang tepat."
            else:
                return "Belum ada tindakan yang saya lakukan sebelumnya."
        
        # 2. "sudah sampai mana" / "progress"
        if any(k in message_lower for k in ["sampai mana", "progress", "sejauh mana"]):
            if self.state.completed_tasks:
                return f"Progress saat ini:\n\n✅ Selesai: {', '.join(self.state.completed_tasks)}\n\n📋 Sedang: {self.state.current_task or 'Tidak ada task aktif'}\n\n📌 Tersisa: {', '.join(self.state.pending_tasks) or 'Tidak ada'}"
            else:
                return "Belum ada task yang dikerjakan."
        
        # 3. "ringkas" / "rangkum" / "summary"
        if any(k in message_lower for k in ["ringkas", "rangkum", "summary"]):
            if self.state.completed_tasks:
                return f"Ringkasan pekerjaan:\n\n📋 Project: {self.state.project}\n✅ Selesai: {len(self.state.completed_tasks)} task\n📌 Tersisa: {len(self.state.pending_tasks)} task\n\nHasil terakhir: {self.state.last_result[:200]}..."
            else:
                return "Belum ada pekerjaan yang bisa diringkas."
        
        return None
