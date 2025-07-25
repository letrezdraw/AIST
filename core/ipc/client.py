# core/ipc/client.py

import socket
import threading
import json
import time
from .protocol import HOST, PORT, MSG_CMD, MSG_SPEAK, MSG_CONFIRM, MSG_CONFIRM_RESPONSE
from core.tts import speak
from core.user_interaction import ask_for_confirmation

class IPCClient:
    """
    The IPC client runs in the main user-facing application. It connects to the
    background service, sends user commands, and listens for instructions
    from the service (e.g., text to speak).
    """
    def __init__(self):
        self.client_socket = None
        self.is_running = False
        self.listener_thread = None

    def connect(self):
        while self.is_running:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((HOST, PORT))
                print("IPC Client: Connected to server.")
                # Start listening for messages from the server
                self.listener_thread = threading.Thread(target=self._listen_for_messages, daemon=True)
                self.listener_thread.start()
                return True
            except ConnectionRefusedError:
                print("IPC Client: Connection refused. Is the AIST service running? Retrying in 5 seconds...")
                time.sleep(5)
            except Exception as e:
                print(f"IPC Client: An unexpected error occurred during connection: {e}")
                time.sleep(5)
        return False

    def _listen_for_messages(self):
        try:
            while self.is_running:
                data = self.client_socket.recv(4096)
                if not data:
                    print("IPC Client: Server closed the connection.")
                    break
                
                message = json.loads(data.decode('utf-8'))
                msg_type = message.get("type")
                payload = message.get("payload")

                if msg_type == MSG_SPEAK:
                    print(f"AIST: {payload}")
                    speak(payload)
                elif msg_type == MSG_CONFIRM:
                    prompt = payload.get("prompt")
                    threading.Thread(target=self._handle_confirmation_request, args=(prompt,), daemon=True).start()

        except (ConnectionResetError, BrokenPipeError, OSError):
            print("IPC Client: Connection lost.")
        finally:
            self.client_socket.close()
            self.client_socket = None
            # If the loop was broken but we are supposed to be running, try to reconnect.
            if self.is_running:
                self.connect()

    def _handle_confirmation_request(self, prompt: str):
        """Handles showing the confirmation dialog and sending the response back to the server."""
        if not prompt:
            return
        user_response = ask_for_confirmation(prompt)
        self.send_message({"type": MSG_CONFIRM_RESPONSE, "payload": {"confirmed": user_response}})

    def send_message(self, message: dict):
        """Sends a JSON message to the server."""
        if self.client_socket:
            try:
                self.client_socket.sendall(json.dumps(message).encode('utf-8'))
            except (ConnectionResetError, BrokenPipeError, OSError):
                print("IPC Client: Failed to send command, connection lost.")
        elif not self.client_socket:
            print("IPC Client: Cannot send command, not connected to server.")

    def send_command(self, command_text: str):
        if command_text:
            self.send_message({"type": MSG_CMD, "payload": command_text})

    def start(self):
        self.is_running = True
        threading.Thread(target=self.connect, daemon=True).start()

    def stop(self):
        self.is_running = False
        if self.client_socket:
            self.client_socket.close()
        print("IPC Client: Stopped.")