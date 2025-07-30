# gui.py
import multiprocessing
import logging
import time
from aist.core.log_setup import setup_logging, console_log, Colors
from aist.core.ipc.server import IPCServer
from aist.gui.main_window import App

def run_backend():
    """
    This function runs in a separate process.
    It sets up logging for the backend and starts the IPC server.
    """
    # is_frontend=False ensures logs are not broadcast from this process
    setup_logging()
    server = IPCServer()
    if not server.start():
        console_log("Failed to start backend server. Exiting.", color=Colors.YELLOW)
        return
    
    # Keep the backend process alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    multiprocessing.freeze_support() # For PyInstaller compatibility

    # Start the backend server in a separate process
    backend_process = multiprocessing.Process(target=run_backend, daemon=True)
    backend_process.start()

    # The main process will run the GUI
    # The GUI will set up its own logging, including the broadcast handler
    app = App()
    app.mainloop()