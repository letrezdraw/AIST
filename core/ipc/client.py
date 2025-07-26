# core/ipc/client.py

import zmq
import logging
import threading
from typing import Callable

log = logging.getLogger(__name__)

class IPCClient:
    """
    The ZMQ client that connects to the backend server.
    It sends user commands and receives responses in a blocking request-reply pattern.
    """
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect("tcp://localhost:5555")
        self.is_running = False
        # Callback to be set by the main application to handle responses (e.g., speak them).
        self.on_response_received: Callable[[str], None] | None = None

    def send_command(self, command_text: str):
        """Sends a command and waits for a response."""
        if not self.is_running:
            log.warning("IPC client is not running. Cannot send command.")
            return

        if not command_text:
            return

        try:
            log.info(f"Sending command to backend: '{command_text}'")
            self.socket.send_string(command_text)
            response = self.socket.recv_string()
            log.info(f"Received response from backend: '{response}'")

            if self.on_response_received and response:
                # The response handling (speaking) is done via the callback.
                self.on_response_received(response)
        except zmq.ZMQError as e:
            log.error(f"ZMQ error while communicating with backend: {e}")
            if self.on_response_received:
                self.on_response_received("I'm having trouble connecting to my brain.")
        except Exception as e:
            log.error(f"Unexpected error in IPC client: {e}", exc_info=True)
            if self.on_response_received:
                self.on_response_received("I've encountered an unexpected error.")

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