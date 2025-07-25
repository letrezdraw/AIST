# run_backend.py
# A simple script to run the AIST backend server in a console window.
# This replaces the need for a Windows Service for simpler use cases.

import os
import sys
import logging

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
    
    ipc_server = IPCServer()
    
    log.info("Backend is running. Press Ctrl+C to stop.")
    try:
        ipc_server.start()
    except KeyboardInterrupt:
        log.info("Ctrl+C received. Shutting down backend server.")

if __name__ == "__main__":
    main()