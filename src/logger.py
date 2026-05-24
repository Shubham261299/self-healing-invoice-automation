"""Centralized logging with file + rich console output."""
import logging
from pathlib import Path
from rich.logging import RichHandler
from src.config import LOGS_DIR

LOG_FILE = LOGS_DIR / "automation.log"


def get_logger(name: str = "invoice_bot") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console (pretty)
    console_handler = RichHandler(rich_tracebacks=True, show_path=False, markup=True)
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # File (plain, for dashboard parsing)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s",
                          datefmt="%Y-%m-%d %H:%M:%S")
    )

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger