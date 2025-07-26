# run_backend.py
# A simple script to run the AIST backend server in a console window.
# This replaces the need for a Windows Service for simpler use cases.

import os
import sys
import logging
import time

# Ensure the script's directory is in the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from core.log_setup import setup_logging
from core.ipc.server import IPCServer

def main():
    # Set up logging for the backend process
    setup_logging()
    log = logging.getLogger(__name__)

    log.info("--- AIST Backend Console ---")
    log.info("Starting IPC Server... This may take a moment to load the AI model.")
    
    ipc_server = None # Define before try block
    try:
        ipc_server = IPCServer()
        ipc_server.start()
        log.info("Backend is running. Press Ctrl+C to stop.")
        # Keep the main thread alive to listen for KeyboardInterrupt
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log.info("Ctrl+C received. Shutting down backend server.")
    finally:
        if ipc_server:
            ipc_server.stop()

if __name__ == "__main__":
    main()