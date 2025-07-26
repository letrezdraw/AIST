# core/log_setup.py
import logging
import logging.handlers
import os
import sys

LOG_FOLDER = "data/logs"
LOG_FILENAME = "aist.log"

def setup_logging():
    """
    Configures the root logger for the entire application.
    This will log to both a rotating file and the console.
    This function is idempotent and can be called multiple times safely.
    """
    # Get the root logger
    logger = logging.getLogger()
    
    # If handlers are already configured, do nothing.
    if logger.hasHandlers():
        return

    # Set the root logger level to the lowest possible level to capture all messages.
    logger.setLevel(logging.DEBUG)

    # Ensure the log directory exists
    os.makedirs(LOG_FOLDER, exist_ok=True)
    log_filepath = os.path.join(LOG_FOLDER, LOG_FILENAME)

    # Define the log format
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)-8s - %(name)-22s - %(message)s'
    )

    # --- File Handler (captures EVERYTHING - DEBUG level and up) ---
    # Rotates logs, keeping 5 files of up to 5MB each.
    file_handler = logging.handlers.RotatingFileHandler(
        log_filepath, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG) # Set file handler to capture debug messages
    logger.addHandler(file_handler)

    # --- Console Handler (captures INFO level and up) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO) # Set console handler to show only INFO and higher
    logger.addHandler(console_handler)