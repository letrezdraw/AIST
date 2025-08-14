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

from aist.core.log_setup import setup_logging, console_log, Colors
from aist.core.ipc.server import IPCServer
from aist.core.ipc.event_bus import EventBroadcaster # New import

def main():
    # Set up logging for the backend process
    setup_logging(is_frontend=False)
    log = logging.getLogger(__name__)

    console_log("--- AIST Backend Console ---", prefix="SYSTEM")
    console_log("Starting backend services...", prefix="INIT")
    
    event_broadcaster = None # Define before try block
    ipc_server = None # Define before try block
    try:
        event_broadcaster = EventBroadcaster()
        ipc_server = IPCServer(event_broadcaster=event_broadcaster) # Pass broadcaster
        if ipc_server.start():
            console_log("Backend is running. Press Ctrl+C to stop.", prefix="READY", color=Colors.GREEN)
            # Keep the main thread alive to listen for KeyboardInterrupt
            while True:
                time.sleep(1)
        else:
            log.fatal("Backend failed to start due to a critical error. Please check the logs.")
            # The application will exit here naturally.
    except KeyboardInterrupt:
        log.info("Ctrl+C received. Shutting down backend server.")
    finally:
        if ipc_server:
            ipc_server.stop()
        if event_broadcaster:
            event_broadcaster.stop()

if __name__ == "__main__":
    main()