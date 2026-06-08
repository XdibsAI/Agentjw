"""
core/logger.py - Rich-powered logging system
"""
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from pathlib import Path
from datetime import datetime
from core.config import config

custom_theme = Theme({
    "agent.orchestrator": "bold cyan",
    "agent.planner": "bold yellow",
    "agent.coder": "bold green",
    "agent.reviewer": "bold blue",
    "agent.repair": "bold red",
    "agent.memory": "bold magenta",
    "agent.critic": "bold orange1",
    "status.success": "bold green",
    "status.error": "bold red",
    "status.warning": "bold yellow",
    "status.info": "bold white",
})

console = Console(theme=custom_theme)

def get_logger(name: str) -> logging.Logger:
    log_file = config.LOGS_DIR / f"{datetime.now().strftime('%Y%m%d')}_agentjw.log"
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=console, rich_tracebacks=True, show_path=False),
            logging.FileHandler(log_file),
        ]
    )
    return logging.getLogger(name)

logger = get_logger("agentjw")
