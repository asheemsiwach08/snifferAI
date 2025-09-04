"""
This module contains the logger configuration for the application.
"""

import sys
import logging
from typing import Optional

def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup the loggin configuration for the application.

    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name (str): The name of the logger.
    """
    logger = logging.getLogger(name)
    return logger

# Setup default logging
setup_logging()

# Create default logger instance for easy import 
logger = get_logger(__name__)