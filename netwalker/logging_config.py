"""
Logging configuration for NetWalker
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(logs_directory="./logs", log_level=logging.INFO):
    """
    Set up logging infrastructure with configurable output directory
    
    Args:
        logs_directory (str): Directory for log files
        log_level: Logging level (default: INFO)
    """
    # Create logs directory if it doesn't exist
    Path(logs_directory).mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp-based filename (YYYYMMDD-HH-MM format)
    timestamp = datetime.now().strftime("%Y%m%d-%H-%M")
    log_filename = f"netwalker_{timestamp}.log"
    log_path = os.path.join(logs_directory, log_filename)
    
    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_path}")
    
    return logger