"""
Text Utilities - Safe text formatting for various outputs
"""
import re
from typing import Optional


def escape_markdown(text: str) -> str:
    """
    Escape markdown special characters for Telegram.
    Only escape characters that actually cause parse errors.
    """
    if not text:
        return ""
    
    text = str(text)
    
    # Characters that break Telegram MarkdownV2 parsing
    # Escaped with backslash
    special_chars = r'([_*\[\]()~`>#+\-=|{}.!\\])'
    return re.sub(special_chars, r'\\\1', text)


def safe_text(text: str, max_length: int = 4000) -> str:
    """Prepare text for safe output"""
    if not text:
        return ""
    
    # Escape markdown
    safe = escape_markdown(text)
    
    # Truncate if needed
    if len(safe) > max_length:
        safe = safe[:max_length-3] + "..."
    
    return safe
