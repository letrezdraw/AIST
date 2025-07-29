# aist/core/ipc/event_bus.py
import zmq
import json
import logging
from aist.core.config_manager import config

log = logging.getLogger(__name__)

class EventBroadcaster:
    """
    A ZMQ PUB socket to broadcast events to any listening subscribers (like the GUI).
    """
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        port = config.get('ipc.event_bus_port', 5556)
        self.socket.bind(f"tcp://*:{port}")
        log.info(f"Event broadcaster started on tcp://*:{port}")

    def broadcast(self, event_type: str, payload: dict):
        """
        Broadcasts an event message.
        The message is sent as two parts: the event type (topic) and the JSON payload.
        """
        try:
            message = [event_type.encode('utf-8'), json.dumps(payload).encode('utf-8')]
            self.socket.send_multipart(message)
        except Exception as e:
            log.error(f"Failed to broadcast event '{event_type}': {e}")

    def stop(self):
        """Stops the broadcaster socket."""
        self.socket.close()
        self.context.term()
        log.info("Event broadcaster stopped.")