# core/ipc/server.py

import socket
import threading
import json
from .protocol import HOST, PORT, MSG_CMD, MSG_SPEAK, MSG_CONFIRM, MSG_CONFIRM_RESPONSE
from core.llm import initialize_llm
from core.memory import retrieve_relevant_facts
from skills.dispatcher import command_dispatcher

MAX_HISTORY_TURNS = 3

class IPCServer:
    """
    The IPC server runs in the background service. It listens for a connection
    from the UI client, processes commands using the LLM and skills, and
    sends back actions for the client to perform (e.g., speak).
    """
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.client_conn = None
        self.llm = None
        self.conversation_history = []
        self.is_running = False
        self.confirmation_event = threading.Event()
        self.confirmation_result = False

    def _handle_client(self, conn):
        self.client_conn = conn
        print("IPC: Client connected.")
        try:
            while self.is_running:
                data = conn.recv(4096)
                if not data:
                    break  # Connection closed

                message = json.loads(data.decode('utf-8'))
                msg_type = message.get("type")
                payload = message.get("payload")

                if msg_type == MSG_CMD:
                    command = payload
                    print(f"IPC: Received command: '{command}'")

                    relevant_facts = retrieve_relevant_facts(command)
                    # Pass `self` so the dispatcher can give skills access to the server (for confirmations)
                    result = command_dispatcher(command, self.llm, self.conversation_history, relevant_facts, ipc_server=self)

                    if result == "QUIT_AIST":
                        result = "Goodbye!" # The client will handle the shutdown

                    if isinstance(result, str) and result.strip():
                        self.send_message({"type": MSG_SPEAK, "payload": result})
                        self.conversation_history.append(("user", command))
                        self.conversation_history.append(("assistant", result))

                        if len(self.conversation_history) > MAX_HISTORY_TURNS * 2:
                            self.conversation_history = self.conversation_history[-(MAX_HISTORY_TURNS * 2):]
                
                elif msg_type == MSG_CONFIRM_RESPONSE:
                    # The client has responded to a confirmation request
                    self.confirmation_result = payload.get("confirmed", False)
                    self.confirmation_event.set() # Unblock the waiting skill

        except (ConnectionResetError, BrokenPipeError):
            print("IPC: Client disconnected.")
        finally:
            print("IPC: Closing client connection.")
            conn.close()
            self.client_conn = None

    def send_message(self, message):
        if self.client_conn:
            try:
                self.client_conn.sendall(json.dumps(message).encode('utf-8'))
            except (ConnectionResetError, BrokenPipeError):
                print("IPC: Failed to send message, client disconnected.")

    def request_confirmation_from_client(self, prompt_text: str) -> bool:
        """Sends a confirmation request to the client and waits for a response."""
        if not self.client_conn:
            print("IPC: Cannot request confirmation, no client connected.")
            return False # Default to 'no' for safety

        self.confirmation_event.clear()
        self.send_message({"type": MSG_CONFIRM, "payload": {"prompt": prompt_text}})

        # Wait for the client to respond, with a 60-second timeout
        event_was_set = self.confirmation_event.wait(timeout=60.0)

        if not event_was_set:
            print("IPC: Confirmation request timed out.")
            return False

        return self.confirmation_result

    def start(self):
        self.is_running = True
        print("IPC Server: Initializing LLM...")
        self.llm = initialize_llm()
        if not self.llm:
            print("FATAL: Could not start IPC Server, LLM failed to load.")
            self.is_running = False
            return

        self.server_socket.listen()
        print(f"IPC Server: Listening on {HOST}:{PORT}")

        while self.is_running:
            conn, addr = self.server_socket.accept()
            threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def stop(self):
        print("IPC Server: Shutting down...")
        self.is_running = False
        self.server_socket.close()