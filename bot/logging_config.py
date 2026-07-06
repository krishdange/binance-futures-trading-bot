"""Logging configuration for the trading bot."""

import logging
import sys
from pathlib import Path

from bot.config import DEFAULT_LOG_FILE, LOGS_DIR


def setup_logging(log_file: Path | None = None) -> logging.Logger:
    """
    Configure application-wide logging to file and console.

    Args:
        log_file: Optional custom log file path.

    Returns:
        Configured root logger for the trading bot.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    target_log = log_file or DEFAULT_LOG_FILE

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(target_log, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
