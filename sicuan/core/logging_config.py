"""
Logging Configuration - Untuk produksi
"""

import logging
import sys
from pathlib import Path

LOG_DIR = Path("/home/dibs/agentjw/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(level=logging.INFO):
    """Setup logging untuk produksi"""
    
    # Format log
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.FileHandler(LOG_DIR / "sicuan.log")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Dapatkan logger dengan nama"""
    return logging.getLogger(name)
