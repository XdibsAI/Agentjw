"""
SiCuan Chat Interface
Terima pesan, think, respond, execute — semua dari LLM
"""
import uuid
import re
from pathlib import Path
from typing import List, Dict
from core.logger import logger, console
from rich.panel import Panel
from rich.text import Text

BASE = Path(__file__).parent


class SiCuanChat:
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.history: List[Dict] = []
        self._brain = None

    @property
    def brain(self):
        if self._brain is None:
            from sicuan.brain import sicuan_brain
            self._brain = sicuan_brain
        return self._brain

    def chat(self, user_message: str) -> str:
        """Main entry — user kirim pesan, SiCuan respond + execute"""

        # Deteksi kalau user kirim API key
        # Format: "ini keynya: sk-or-v1-xxx" atau "OPENROUTER_API_KEY=sk-or-v1-xxx"
        api_key_pattern = re.search(
            r'([A-Z_]+(?:API_KEY|TOKEN|SECRET)[A-Z_]*)[\s=:]+([^\s]+)',
            user_message.upper()
        )
        if api_key_pattern:
            key_name = api_key_pattern.group(1)
            # Get actual value (case sensitive)
            val_match = re.search(
                key_name + r'[\s=:]+(\S+)',
                user_message, re.IGNORECASE
            )
            if val_match:
                response = self.brain.handle_api_key_submission(
                    key_name, val_match.group(1)
                )
                self._save_history(user_message, response)
                return response

        # Cek kalau user cuma kirim value setelah diminta API key
        last_assistant = self.history[-1]["content"] if self.history and self.history[-1]["role"] == "assistant" else ""
        if "kirimkan ke sini" in last_assistant.lower() or "paste di sini" in last_assistant.lower():
            # Extract key name yang diminta
            key_match = re.search(r'\b([A-Z_]+(?:KEY|TOKEN|SECRET))\b', last_assistant)
            if key_match and len(user_message.strip()) > 10 and " " not in user_message.strip():
                key_name = key_match.group(1)
                response = self.brain.handle_api_key_submission(key_name, user_message.strip())
                self._save_history(user_message, response)
                return response

        # Normal flow — LLM decide everything
        result = self.brain.think_and_respond(user_message, self.history)

        response_text = result.get("response", "...")
        action = result.get("action")
        action_target = result.get("action_target", "")

        # Action yang FAKTUAL — hasil eksekusi WAJIB menggantikan total response
        # LLM sebelumnya, karena LLM bisa mengarang detail (nama file, isi kode,
        # angka) sebelum action benar-benar dijalankan. Jangan pernah digabung,
        # supaya karangan tidak nempel di depan data asli.
        FACTUAL_OVERRIDE_ACTIONS = {
            "scan_project", "get_file", "show_log", "video_info",
            "list_projects", "gallery", "godmeme_status", "project_summary",
            "trace_code",
        }

        # Action yang sudah punya verifikasi sendiri (lewat auditor_agent) —
        # response auditor JUGA wajib full-override, bukan digabung.
        AUDITED_ACTIONS = {
            "repair_project", "modify_logic", "modify_project",
        }

        # PLAN EXECUTOR:
        # Multi-step plan adalah source of truth.
        # Eksekusi dikelola oleh brain.execute_plan()
        # agar seluruh planner logic berada di satu tempat.

        action_result = None

        plan = result.get("plan", [])

        if isinstance(plan, list) and len(plan) > 0:
            try:
                logger.info(
                    f"Executing planner: {len(plan)} steps"
                )

                action_result = self.brain.execute_plan(
                    plan,
                    user_message,
                    self.session_id
                )

                if action_result:
                    response_text = action_result

            except Exception as e:
                logger.error(f"Plan execute error: {e}")
                response_text += f"\n\nAda error Mas: {str(e)[:100]}"

        elif action and action not in ("null", None, "request_api_key"):
            try:
                action_result = self.brain.execute_action(
                    action,
                    action_target,
                    user_message,
                    self.session_id
                )

                if action_result:
                    if "Sebentar Mas" in action_result and ".env" in action_result:
                        response_text = action_result
                    elif action in FACTUAL_OVERRIDE_ACTIONS or action in AUDITED_ACTIONS:
                        response_text = action_result
                    elif action_result not in response_text:
                        response_text += "\n\n" + action_result

            except Exception as e:
                logger.error(f"Action execute error: {e}")
                response_text += f"\n\nAda error Mas: {str(e)[:100]}"

        # REFLECTION: cek apakah hasil action sudah jawab tuntas pertanyaan user.
        # Cuma jalan kalau ada action_result faktual (bukan untuk "null" action /
        # obrolan biasa, dan bukan untuk action yang sudah ada audit sendiri).
        if (
            action_result
            and action in FACTUAL_OVERRIDE_ACTIONS
            and not plan
        ):
            try:
                followup = self.brain.reflect_and_maybe_continue(
                    user_message=user_message,
                    first_action=action,
                    first_action_result=action_result,
                    history=self.history,
                )
                if followup:
                    response_text = followup
            except Exception as e:
                logger.error(f"Reflection error: {e}")

        self._save_history(user_message, response_text)
        return response_text

    def _save_history(self, user_msg: str, assistant_msg: str):
        self.history.append({"role": "user", "content": user_msg})
        self.history.append({"role": "assistant", "content": assistant_msg})
        if len(self.history) > 40:
            self.history = self.history[-40:]

        # Persist to memory
        try:
            from memory.memory_store import memory_store
            memory_store.save_chat(self.session_id, "user", user_msg)
            memory_store.save_chat(self.session_id, "assistant", assistant_msg)
        except Exception:
            pass


sicuan_chat = SiCuanChat()
