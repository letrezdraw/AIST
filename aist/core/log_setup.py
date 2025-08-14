# core/log_setup.py
import logging
import logging.handlers
import os
import sys
from aist.core.config_manager import config
from aist.core.gui_logging_handler import GUILoggingHandler
import multiprocessing # Add this import

# This is now configured in config.yaml
LOG_FILENAME = "aist.log"

# ANSI color codes for a more professional console output
class Colors:
    RESET = "\033[0m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"

def console_log(message: str, prefix: str = "STATUS", color: str = Colors.WHITE):
    """
    Prints a colored and formatted message directly to the console.
    This is used for critical status updates that the user should see even
    if console logging is disabled in the config.
    """
    # Using a distinct, padded prefix makes the output align neatly.
    print(f"{color}[{prefix:<8}]{Colors.RESET} {message}", file=sys.stdout)
    sys.stdout.flush()

def setup_logging(is_frontend=False):
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

    # Get log folder path from the central configuration
    log_folder = config.get('logging.folder', 'data/logs')

    # Ensure the log directory exists
    os.makedirs(log_folder, exist_ok=True)
    log_filepath = os.path.join(log_folder, LOG_FILENAME)

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

    # --- Console Handler (captures INFO level and up, if enabled) ---
    # Disable console logging for child processes to avoid potential issues
    # with multiple processes writing to the same console on Windows.
    is_main_process = (multiprocessing.current_process().name == 'MainProcess')
    if config.get('logging.console_enabled', True) and is_main_process:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO) # Set console handler to show only INFO and higher
        logger.addHandler(console_handler)

    # --- GUI Handler (broadcasts logs for the GUI to display) ---
    if is_frontend:
        gui_handler = GUILoggingHandler()
        gui_handler.setFormatter(formatter)
        gui_handler.setLevel(logging.INFO)
        logger.addHandler(gui_handler)

