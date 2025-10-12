import logging
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Define custom theme for better visual hierarchy
ASANTIYA_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "red",
        "success": "green",
        "debug": "dim white",
        "deployment": "bold blue",
        "container": "bold magenta",
        "config": "bold green",
    }
)


def setup_logging(
    verbose: bool = False,
    log_file: Optional[Path] = None,
    log_level: Optional[str] = None,
) -> logging.Logger:
    """
    Configure structured logging with Rich handler for pretty output.

    Args:
        verbose: Enable debug logging
        log_file: Optional file to write logs to
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    # Determine log level
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = logging.DEBUG if verbose else logging.INFO

    # Create console with custom theme
    console = Console(theme=ASANTIYA_THEME, stderr=True)

    # Create formatters
    console_format = "[%(name)s] %(message)s"
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create handlers
    handlers = []

    # Console handler with Rich
    console_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=False,
        show_path=False,
        log_time_format="[%X]",
        show_time=True,
    )
    console_handler.setFormatter(logging.Formatter(console_format))
    handlers.append(console_handler)

    # File handler if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(file_format))
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,  # Override any existing configuration
    )

    # Get logger for this module
    logger = logging.getLogger("asantiya")

    # Silence noisy third-party loggers
    logging.getLogger("docker").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("paramiko").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"asantiya.{name}")


class DeploymentLogger:
    """Context manager for deployment-specific logging."""

    def __init__(self, operation: str, logger: Optional[logging.Logger] = None):
        self.operation = operation
        self.logger = logger or get_logger("deployment")
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"🚀 Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(f"❌ {self.operation} failed: {exc_val}")
        else:
            duration = time.time() - self.start_time if self.start_time else 0
            self.logger.info(f"✅ {self.operation} completed in {duration:.2f}s")


def log_deployment_step(step: str, logger: Optional[logging.Logger] = None):
    """Decorator to log deployment steps."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger_instance = logger or get_logger("deployment")
            logger_instance.info(f"📦 {step}")
            try:
                result = func(*args, **kwargs)
                logger_instance.info(f"✓ {step} completed")
                return result
            except Exception as e:
                logger_instance.error(f"✗ {step} failed: {e}")
                raise

        return wrapper

    return decorator
