# aist/core/gui_logging_handler.py
import logging
import zmq
import json
from aist.core.config_manager import config

class GUILoggingHandler(logging.Handler):
    """
    A custom logging handler that broadcasts log records over a ZMQ PUB socket.
    This allows the GUI or other components to subscribe to live log events.
    """
    def __init__(self, host="tcp://*"):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        port = config.get('ipc.log_broadcast_port', 5558)
        self.socket.bind(f"{host}:{port}")

    def emit(self, record):
        """Formats and broadcasts a log record."""
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