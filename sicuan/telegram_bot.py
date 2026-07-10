"""
Telegram Bot - Group Mode with Mention Detection
"""

import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, Optional

sys.path.insert(0, '/home/dibs/agentjw')
sys.path.insert(0, '/home/dibs/agentjw/core')
sys.path.insert(0, '/home/dibs/agentjw/sicuan')

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from telegram.constants import ParseMode

from sicuan.chat import SiCuanChat
from sicuan.platform.workspace_resolver import get_workspace_resolver
from sicuan.platform.runtime import get_runtime_manager
from core.logger import logger


class TelegramBot:
    """Telegram bot dengan group mode"""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.bot_name = "SiCuan"
        
        # Group mode settings
        self.group_mode = True
        self.mention_only = False  # Respond to all messages in group for testing
        self.bot_username = "godmemeku_bot"
        
        # Permission levels
        self.owners = [int(os.getenv("TELEGRAM_CHAT_ID", 0))]
        self.admins = self.owners.copy()
        self.allowed_users = self.owners.copy()
        
        # Metrics
        self.metrics = {
            "total_messages": 0,
            "total_responses": 0,
            "errors": 0,
            "response_times": [],
            "tokens_used": 0,
        }
        
        self.sicuan = None

    def init_sicuan(self):
        """Initialize SiCuan brain"""
        if self.sicuan is None:
            self.sicuan = SiCuanChat()
            logger.info("🤖 SiCuan initialized for Telegram")

    def is_mentioned(self, text: str) -> bool:
        """Check if bot is mentioned in message"""
        if not text:
            return False
        mention_patterns = [
            f"@{self.bot_username}",
            f"@{self.bot_username.lower()}",
            "cu",
            "cuan",
            "cucu",
            "Cuan",
            "SiCuan",
            "sicuan",
            "SICUAN",
        ]
        return any(pattern in text for pattern in mention_patterns)

    def is_owner(self, user_id: int) -> bool:
        """Check if user is owner"""
        return user_id in self.owners

    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use bot"""
        # Check user memory
        from sicuan.core.user_memory import get_user_memory
        user_mem = get_user_memory()
        if user_mem.get_user_preference(user_id, "allowed", False):
            return True
        return user_id in self.allowed_users or self.is_owner(user_id)

    def get_permission_level(self, user_id: int) -> str:
        """Get user permission level"""
        if self.is_owner(user_id):
            return "owner"
        if user_id in self.admins:
            return "admin"
        if user_id in self.allowed_users:
            return "user"
        return "guest"

    def should_respond(self, update: Update) -> bool:
        """Determine if bot should respond to message"""
        if not update.message:
            return False
        
        text = update.message.text or ""
        user_id = update.message.from_user.id
        
        # Always respond to owners
        if self.is_owner(user_id):
            return True
        
        # In group mode, only respond when mentioned
        if self.mention_only:
            return self.is_mentioned(text)
        
        # Otherwise, respond to allowed users
        return self.is_allowed(user_id)

    def record_metrics(self, response_time: float, tokens: int = 0, error: bool = False):
        """Record metrics"""
        self.metrics["total_messages"] += 1
        if not error:
            self.metrics["total_responses"] += 1
            self.metrics["response_times"].append(response_time)
            self.metrics["tokens_used"] += tokens
        else:
            self.metrics["errors"] += 1
        
        # Keep last 1000 response times
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]

    def get_metrics_summary(self) -> str:
        """Get metrics summary"""
        times = self.metrics["response_times"]
        avg_time = sum(times) / len(times) if times else 0
        
        return f"""
📊 **SiCuan Metrics**

- Messages: {self.metrics["total_messages"]}
- Responses: {self.metrics["total_responses"]}
- Errors: {self.metrics["errors"]}
- Avg Response: {avg_time:.2f}s
- Tokens Used: {self.metrics["tokens_used"]}
"""

    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle incoming message"""
        if not update.message:
            return
        
        user_id = update.message.from_user.id
        username = update.message.from_user.username or "unknown"
        text = update.message.text or ""
        from_user_id = user_id
        
        # AUTO-REGISTER: Simpan user ke memory saat pertama kali chat
        from sicuan.core.user_memory import get_user_memory
        user_mem = get_user_memory()
        if not user_mem.get_user_preference(user_id, "registered", False):
            user_mem.set_user_preference(user_id, "registered", True)
            user_mem.set_user_preference(user_id, "username", username)
            user_mem.set_user_preference(user_id, "private_mode", True)
            user_mem.set_user_preference(user_id, "allowed", True)
            print(f"📝 Auto-registered user: {username} (ID: {user_id})")
        
        # WORKSPACE RESOLVER: Map chat ke workspace
        chat_id = update.message.chat.id
        chat_type = update.message.chat.type
        resolver = get_workspace_resolver()
        workspace_id = resolver.resolve(chat_id)
        
        if not workspace_id:
            # Auto-create workspace for new chat
            from sicuan.platform.workspace import get_workspace
            ws = get_workspace()
            workspace_name = f"Workspace_{chat_id}"
            workspace = ws.create(user_id, workspace_name)
            workspace_id = workspace["id"]
            resolver.register_chat(chat_id, workspace_id, chat_type)
            print(f"🏢 Created workspace {workspace_id} for chat {chat_id}")
        
        # Start runtime untuk workspace
        runtime = get_runtime_manager()
        if not runtime.get_status(workspace_id)["is_running"]:
            runtime.start(workspace_id)
            print(f"🚀 Started runtime for workspace {workspace_id}")
        
        # Check if should respond
        # DEBUG: Log all messages
        print(f"[DEBUG] Message from {update.message.from_user.username}: {text[:50]}")
        
        # DEBUG: Log all messages
        print(f"[DEBUG] Message from {update.message.from_user.username}: {text[:50]}")
        
        if not self.should_respond(update):
            return
        
        # Check permission - auto allow for registered users
        permission = self.get_permission_level(user_id)
        if permission == "guest":
            # Auto-allow registered users
            if user_mem.get_user_preference(user_id, "allowed", False):
                permission = "user"
            else:
                await update.message.reply_text(
                    "❌ Maaf, Anda belum memiliki akses ke SiCuan. "
                    "Kirim /start untuk mendaftar."
                )
                return
        
        # Check for commands
        if text.startswith("/"):
            await self.handle_command(update, context)
            return
        
        # Process message
        start_time = time.time()
        
        try:
            # Initialize SiCuan if needed
            self.init_sicuan()
            
            # Process with SiCuan
            response = self.sicuan.chat(text, user_id=user_id, workspace_id=workspace_id)
            response_time = time.time() - start_time
            
            # Record metrics
            self.record_metrics(response_time)
            
            # Send response
            if response:
                # Split long messages
                if len(response) > 4000:
                    for i in range(0, len(response), 4000):
                        await update.message.reply_text(
                            response[i:i+4000],
                            parse_mode=ParseMode.MARKDOWN
                        )
                else:
                    await update.message.reply_text(
                        response,
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                await update.message.reply_text("Maaf, saya tidak bisa memproses permintaan saat ini.")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.record_metrics(time.time() - start_time, error=True)
            await update.message.reply_text(
                f"❌ Error: {str(e)[:200]}\n\nCoba lagi nanti."
            )

    async def handle_command(self, update: Update, context: CallbackContext):
        """Handle commands"""
        if not update.message:
            return
        
        text = update.message.text
        user_id = update.message.from_user.id
        
        if text == "/start":
            user_id = update.message.from_user.id
            username = update.message.from_user.username or "unknown"
            
            # Cek apakah user adalah owner
            from sicuan.core.user_manager import get_user_manager
            user_mgr = get_user_manager()
            is_owner = user_mgr.is_owner(user_id)
            
            if is_owner:
                welcome_msg = f"👋 Halo Mas Gen! **{self.bot_name}** siap membantu.\n\n"
                welcome_msg += f"**User ID:** `{user_id}`\n"
                welcome_msg += f"**Username:** @{username}\n\n"
                welcome_msg += f"**Fitur Owner:**\n"
                welcome_msg += f"- 📂 Kelola Project\n"
                welcome_msg += f"- 🔧 Review & Repair Code\n"
                welcome_msg += f"- 📊 Trading Analysis\n"
                welcome_msg += f"- 📚 Context Memory\n\n"
                welcome_msg += f"Gunakan @{self.bot_username} di grup untuk memanggil saya.\n\n"
                welcome_msg += f"*Powered by SiCuan v2.0*"
            else:
                welcome_msg = f"👋 Hello! I'm **{self.bot_name}** - Your AI Business Partner.\n\n"
                welcome_msg += f"I'm here to help you with:\n"
                welcome_msg += f"- 💬 Chat & Consultation\n"
                welcome_msg += f"- 📊 Data Analysis\n"
                welcome_msg += f"- 🔧 Code Review\n"
                welcome_msg += f"- 📚 Context Memory\n\n"
                welcome_msg += f"Just send me your questions or commands!\n\n"
                welcome_msg += f"*Powered by SiCuan v2.0*"
            
            await update.message.reply_text(
                welcome_msg,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        elif text == "/metrics" and self.is_owner(user_id):
            await update.message.reply_text(
                self.get_metrics_summary(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif text == "/status":
            status = """
🤖 **SiCuan Status**

✅ Active
✅ Memory Loaded
✅ Database Connected
✅ LLM Ready

Mode: Group
Mention-only: Yes
"""
            await update.message.reply_text(status, parse_mode=ParseMode.MARKDOWN)


def run_bot():
    """Run the bot"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not set")
        return
    
    bot = TelegramBot()
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.handle_command))
    application.add_handler(CommandHandler("metrics", bot.handle_command))
    application.add_handler(CommandHandler("status", bot.handle_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    # Start bot
    print("🤖 SiCuan Telegram Bot started")
    print(f"   Group Mode: {bot.group_mode}")
    print(f"   Mention-only: {bot.mention_only}")
    print(f"   Bot Username: @{bot.bot_username}")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run_bot()
