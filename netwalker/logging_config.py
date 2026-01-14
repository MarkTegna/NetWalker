"""
Logging configuration for NetWalker
"""

import logging
import os
import sys
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
    
    # Suppress verbose third-party library loggers
    # Paramiko logs authentication success at INFO level which clutters logs
    logging.getLogger('paramiko').setLevel(logging.WARNING)
    logging.getLogger('paramiko.transport').setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_path}")
    
    return logger


def log_startup_banner(logger, config=None):
    """
    Log startup information banner at the beginning of the log file
    
    Args:
        logger: Logger instance to use for logging
        config: Optional configuration dictionary to log
    """
    from .version import __version__, __author__, __compile_date__
    
    # Get execution information
    command_line = ' '.join(sys.argv)
    execution_path = os.getcwd()
    executable_path = sys.argv[0] if sys.argv else 'unknown'
    
    # Log startup banner
    logger.info("=" * 80)
    logger.info("NetWalker Network Topology Discovery Tool")
    logger.info("=" * 80)
    logger.info(f"Version: {__version__}")
    logger.info(f"Author: {__author__}")
    logger.info(f"Compile Date: {__compile_date__}")
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("-" * 80)
    logger.info("Execution Information:")
    logger.info(f"  Executable: {executable_path}")
    logger.info(f"  Working Directory: {execution_path}")
    logger.info(f"  Command Line: {command_line}")
    logger.info(f"  Python Version: {sys.version.split()[0]}")
    logger.info(f"  Platform: {sys.platform}")
    
    # Log configuration if provided
    if config:
        logger.info("-" * 80)
        logger.info("Active Configuration (after defaults, INI, and CLI overrides):")
        logger.info("")
        
        # Discovery settings
        logger.info("  [Discovery]")
        logger.info(f"    max_discovery_depth: {config.get('max_discovery_depth', 'NOT SET')}")
        logger.info(f"    discovery_timeout_seconds: {config.get('discovery_timeout_seconds', 'NOT SET')}")
        logger.info(f"    max_concurrent_connections: {config.get('max_concurrent_connections', 'NOT SET')}")
        logger.info(f"    connection_timeout_seconds: {config.get('connection_timeout_seconds', 'NOT SET')}")
        logger.info(f"    enable_progress_tracking: {config.get('enable_progress_tracking', 'NOT SET')}")
        logger.info("")
        
        # Filtering settings
        logger.info("  [Filtering]")
        hostname_excludes = config.get('hostname_excludes', [])
        ip_excludes = config.get('ip_excludes', [])
        logger.info(f"    hostname_excludes: {len(hostname_excludes)} patterns")
        if hostname_excludes:
            for pattern in hostname_excludes:
                logger.info(f"      - {pattern}")
        logger.info(f"    ip_excludes: {len(ip_excludes)} ranges")
        if ip_excludes:
            for ip_range in ip_excludes:
                logger.info(f"      - {ip_range}")
        logger.info("")
        
        # Exclusions settings
        logger.info("  [Exclusions]")
        platform_excludes = config.get('platform_excludes', [])
        capability_excludes = config.get('capability_excludes', [])
        logger.info(f"    platform_excludes: {len(platform_excludes)} items")
        if platform_excludes:
            for platform in platform_excludes:
                logger.info(f"      - {platform}")
        logger.info(f"    capability_excludes: {len(capability_excludes)} items")
        if capability_excludes:
            for capability in capability_excludes:
                logger.info(f"      - {capability}")
        logger.info("")
        
        # Output settings
        logger.info("  [Output]")
        logger.info(f"    reports_directory: {config.get('reports_directory', 'NOT SET')}")
        logger.info(f"    logs_directory: {config.get('logs_directory', 'NOT SET')}")
        logger.info("")
        
        # Connection settings
        logger.info("  [Connection]")
        logger.info(f"    task_timeout_seconds: {config.get('task_timeout_seconds', 'NOT SET')}")
        logger.info("")
        
        # Logging settings
        logger.info("  [Logging]")
        logger.info(f"    log_level: {config.get('log_level', 'NOT SET')}")
        logger.info(f"    console_logging: {config.get('console_logging', 'NOT SET')}")
    
    logger.info("=" * 80)