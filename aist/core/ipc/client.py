# core/ipc/client.py

import json
import zmq
import logging
from typing import Dict, Any
from aist.core.config_manager import config

log = logging.getLogger(__name__)

class IPCClient:
    """
    The ZMQ client that connects to the backend server.
    It sends user commands and state, and receives structured JSON responses.
    """
    def __init__(self):
        
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        # Set socket timeout to prevent indefinite hangs (10 second timeout)
        self.socket.setsockopt(zmq.RCVTIMEO, 10000)
        self.socket.setsockopt(zmq.SNDTIMEO, 10000)
        port = config.get('ipc.command_port', 5555)
        self.socket.connect(f"tcp://localhost:{port}")
        self.is_running = False

    def send_command(self, command_text: str, state: str) -> Dict[str, Any] | None:
        """Sends a command and state to the backend and returns the response dictionary."""
        if not self.is_running:
            log.warning("IPC client is not running. Cannot send command.")
            return None

        if not command_text:
            return None

        try:
            request_data = {"type": "command", "payload": {"text": command_text, "state": state}}
            request_json = json.dumps(request_data)
            log.debug(f"Sending request to backend: {request_json}")
            self.socket.send_string(request_json)
            
            response_json = self.socket.recv_string()
            log.debug(f"Received response from backend: {response_json}")
            
            response_dict = json.loads(response_json)
            return response_dict

        except zmq.error.Again:
            # Timeout occurred (socket.RCVTIMEO or SNDTIMEO exceeded)
            log.error("IPC timeout: Backend did not respond within 10 seconds. Backend may be unresponsive.")
            return {"action": "COMMAND", "speak": "I'm taking too long to think. Please try again."}
        except zmq.ZMQError as e:
            log.error(f"ZMQ error while communicating with backend: {e}")
            # Return a dictionary that the frontend can handle, indicating an error.
            return {"action": "COMMAND", "speak": "I'm having trouble connecting to my brain."}
        except Exception as e:
            log.error(f"Unexpected error in IPC client: {e}", exc_info=True)
            return {"action": "COMMAND", "speak": "I've encountered an unexpected error."}

    def send_event(self, event_type: str, payload: dict):
        """Sends an event to the backend for broadcasting."""
        if not self.is_running:
            log.warning("IPC client is not running. Cannot send event.")
            return

        try:
            request_data = {"type": "event", "event_type": event_type, "payload": payload}
            request_json = json.dumps(request_data)
            self.socket.send_string(request_json)
            # Wait for the empty ack from the server
            self.socket.recv_string()
        except zmq.ZMQError as e:
            log.error(f"ZMQ error while sending event to backend: {e}")
        except Exception as e:
            log.error(f"Unexpected error in IPC client sending event: {e}", exc_info=True)

    def start(self):
        """Starts the client, allowing it to send messages."""
        port = config.get('ipc.command_port', 5555)
        log.info(f"IPC Client started and connected to tcp://localhost:{port}")
        self.is_running = True

    def stop(self):
        """Stops the client gracefully."""
        if not self.is_running:
            return
        log.info("Stopping IPC client...")
        self.is_running = False
        # ZMQ sockets should be closed before terminating the context
        self.socket.close()
        self.context.term()
        log.info("IPC Client stopped.")