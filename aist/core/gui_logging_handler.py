# aist/core/gui_logging_handler.py
import logging
import zmq
import json
from aist.core.config_manager import config

class GUILoggingHandler(logging.Handler):
    """
    A custom logging handler that broadcasts log records over a ZMQ PUB/SUB socket.
    This allows the GUI or other components to subscribe to live log events.
    """
    def __init__(self, is_frontend=False, is_skill_process=False):
        super().__init__()
        self.context = zmq.Context()
        port = config.get('ipc.log_broadcast_port', 5558)
        host = "127.0.0.1" # Explicitly use localhost for connecting clients

        if is_frontend or is_skill_process: # If it's a client (frontend or skill process)
            self.socket = self.context.socket(zmq.SUB)
            self.socket.connect(f"tcp://{host}:{port}")
            self.socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.is_broadcaster = False # This socket won't broadcast
        else: # It's the main backend process, it binds
            self.socket = self.context.socket(zmq.PUB)
            self.socket.bind(f"tcp://*:{port}")
            self.is_broadcaster = True # This socket will broadcast

    def emit(self, record):
        """Formats and broadcasts a log record."""
        if self.is_broadcaster: # Only broadcast if this instance is the designated broadcaster
            try:
                # We only broadcast INFO level and above to avoid flooding the GUI.
                if record.levelno >= logging.INFO:
                    log_entry = self.format(record)
                    self.socket.send_string(log_entry)
            except Exception:
                # It's important that the logger itself doesn't crash the application.
                self.handleError(record)

    def close(self):
        self.socket.close()
        self.context.term()
        super().close()