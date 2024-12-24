import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(log_file='app.log', max_bytes=1 * 1024 * 1024, backup_count=5):
    """
    Configures logging to a file with rotation.
    :param log_file: Path to the log file
    :param max_bytes: Maximum size of a log file in bytes before rotation
    :param backup_count: Number of backup log files to keep
    """
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Create file handler with rotation
    handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setLevel(logging.DEBUG)

    # Create formatter and add it to the handler
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Add handler to the logger
    logger.addHandler(handler)

    # Optional: Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
