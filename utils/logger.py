"""logger.py - Structured logging with Rich."""
import logging
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def get_logger(name: str = "ai-content-machine") -> logging.Logger:
    """Get a configured logger with Rich handler."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            show_path=False,
            markup=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s", datefmt="[%X]"))
        logger.addHandler(handler)
    return logger
