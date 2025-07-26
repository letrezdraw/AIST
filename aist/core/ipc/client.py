# core/ipc/client.py

import json
import zmq
import logging
from typing import Dict, Any

log = logging.getLogger(__name__)

class IPCClient:
    """
    The ZMQ client that connects to the backend server.
    It sends user commands and state, and receives structured JSON responses.
    """
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        self.is_running = False

    def send_command(self, command_text: str, state: str) -> Dict[str, Any] | None:
        """Sends a command and state to the backend and returns the response dictionary."""
        if not self.is_running:
            log.warning("IPC client is not running. Cannot send command.")
            return None

        if not command_text:
            return None

        try:
            request_data = {"text": command_text, "state": state}
            request_json = json.dumps(request_data)
            log.debug(f"Sending request to backend: {request_json}")
            self.socket.send_string(request_json)
            
            response_json = self.socket.recv_string()
            log.debug(f"Received response from backend: {response_json}")
            
            response_dict = json.loads(response_json)
            return response_dict

        except zmq.ZMQError as e:
            log.error(f"ZMQ error while communicating with backend: {e}")
            # Return a dictionary that the frontend can handle, indicating an error.
            return {"action": "COMMAND", "speak": "I'm having trouble connecting to my brain."}
        except Exception as e:
            log.error(f"Unexpected error in IPC client: {e}", exc_info=True)
            return {"action": "COMMAND", "speak": "I've encountered an unexpected error."}

    def start(self):
        """Starts the client, allowing it to send messages."""
        log.info("IPC Client started and connected to tcp://localhost:5555")
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