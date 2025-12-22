"""
Logging configuration module for thumbnail_generator.

Provides a centralized logging setup that works across Windows and Linux.
Supports both file and console output with appropriate formatting.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: int = logging.INFO,
    log_dir: Optional[Path] = None,
    log_file: str = "thumbnail_generator.log",
) -> logging.Logger:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (default: logging.INFO)
        log_dir: Directory for log files (default: ./logs)
        log_file: Name of the log file (default: thumbnail_generator.log)
    
    Returns:
        Configured root logger instance
    """
    # Set default log directory
    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    else:
        log_dir = Path(log_dir)
    
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Get root logger and configure it
    logger = logging.getLogger("thumbnail_generator")
    logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    simple_formatter = logging.Formatter(
        fmt="%(levelname)-8s - %(message)s"
    )
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation (all levels)
    log_file_path = log_dir / log_file
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8"
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    except (OSError, IOError) as e:
        # If file handler fails, log warning to console
        console_handler.setFormatter(detailed_formatter)
        logger.warning(f"Could not create file handler at {log_file_path}: {e}")
    
    # Log initialization
    logger.info(f"Logging initialized - Level: {logging.getLevelName(log_level)}, Log dir: {log_dir}")
    
    return logger


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        module_name: Explicit module name (e.g., 'thumbnail_gen', 'update_youtube_videos').
                     Use a descriptive name for CLI modules to avoid '__main__' issues.
                     If None, returns the root thumbnail_generator logger.
    
    Returns:
        Logger instance with module-specific name for filtering and tracking
    """
    if module_name is None:
        return logging.getLogger("thumbnail_generator")
    
    # Create hierarchical logger names like "thumbnail_generator.module_name"
    # Use the module_name directly or extract the last part if it's a full path
    if '.' in module_name:
        logger_name = f"thumbnail_generator.{module_name.split('.')[-1]}"
    else:
        logger_name = f"thumbnail_generator.{module_name}"
    return logging.getLogger(logger_name)
