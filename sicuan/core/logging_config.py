"""Centralized logging configuration"""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(
    name: str = "agentjw",
    log_dir: Path = Path("logs"),
    level: int = logging.INFO
):
    """Setup logging with consistent configuration"""
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log file
    log_file = log_dir / f"{name}.log"
    
    # Configure root logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Prevent propagation to root
    logger.propagate = False
    
    return logger

# Create default logger
logger = setup_logging()
