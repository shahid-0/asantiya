import logging
from rich.logging import RichHandler

def setup_logging(verbose: bool = False):
    """Configure logging with Rich handler for pretty output."""
    level = logging.DEBUG if verbose else logging.INFO
    log_format = "%(message)s"
    date_format = "[%X]"
    
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[RichHandler(
            rich_tracebacks=True,
            markup=False,
            show_path=False,
            log_time_format=date_format
        )]
    )
    
    # Silence noisy loggers
    logging.getLogger("docker").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)