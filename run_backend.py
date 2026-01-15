# run_backend.py
# A simple script to run the AIST backend server in a console window.

import logging
import time
import sys
import os

from aist.core.log_setup import setup_logging, console_log, Colors
from aist.core.ipc.server import IPCServer
from aist.core.ipc.event_bus import EventBroadcaster

def main():
    # Set up logging for the backend process
    setup_logging(is_frontend=False)
    log = logging.getLogger(__name__)

    console_log("--- AIST Backend Console ---", prefix="SYSTEM")
    console_log("Starting backend services...", prefix="INIT")

    event_broadcaster = None
    ipc_server = None
    try:
        event_broadcaster = EventBroadcaster()
        ipc_server = IPCServer(event_broadcaster=event_broadcaster)
        
        if ipc_server.start():
            console_log("Backend is running. Press Ctrl+C to stop.", prefix="READY", color=Colors.GREEN)
            # Keep the main thread alive to listen for KeyboardInterrupt
            while True:
                time.sleep(1)
        else:
            log.fatal("Backend failed to start. Please check the logs.")

    except KeyboardInterrupt:
        log.info("Ctrl+C received. Shutting down backend server.")
    except Exception as e:
        log.critical(f"An unhandled exception occurred: {e}", exc_info=True)
    finally:
        if ipc_server:
            ipc_server.stop()
        if event_broadcaster:
            event_broadcaster.stop()

if __name__ == "__main__":
    main()