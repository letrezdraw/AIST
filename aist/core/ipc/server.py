import json
import zmq
import logging
import threading
from aist.core.conversation import ConversationManager
from aist.core.config_manager import config
from aist.core.log_setup import console_log, Colors
from aist.skills.dispatcher import command_dispatcher # type: ignore
from aist.core.llm import initialize_llm

log = logging.getLogger(__name__)

class IPCServer:
    """
    The ZMQ server that listens for frontend requests.
    It processes commands using the skill dispatcher and returns JSON responses.
    """
    def __init__(self, event_broadcaster):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        port = config.get('ipc.command_port', 5555)
        self.socket.bind(f"tcp://*:{port}")
        self.is_running = False
        self.thread = None
        self.llm = None
        self.conversation_manager = ConversationManager()
        self.event_broadcaster = event_broadcaster # Store the broadcaster

    def start(self):
        """Starts the IPC server and loads the LLM model. Returns True on success, False on failure."""
        console_log("Initializing LLM...", prefix="INIT")
        self.llm = initialize_llm(event_broadcaster=self.event_broadcaster) # Pass broadcaster
        if self.llm is None:
            log.fatal("Failed to initialize LLM. IPC Server will not start.")
            return False
        self.is_running = True
        self.thread = threading.Thread(target=self._serve_forever, daemon=False)
        self.thread.start()
        port = config.get('ipc.command_port', 5555)
        console_log(f"IPC Server started and listening on tcp://*:{port}", prefix="INIT", color=Colors.GREEN)
        return True

    def _serve_forever(self):
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        while self.is_running:
            try:
                # Poll for events with a timeout (e.g., 100ms)
                # This makes the loop non-blocking and allows it to check self.is_running
                socks = dict(poller.poll(100))
                if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                    try:
                        message = self.socket.recv_string()
                        request = json.loads(message)
                    except json.JSONDecodeError:
                        log.error(f"Failed to decode JSON from request: {message}")
                        self.socket.send_string(json.dumps({"error": "Invalid JSON format"}))
                        continue
                    command_text = request.get("text", "")
                    state = request.get("state", "DORMANT")

                    # --- Handle Special GUI Commands ---
                    if command_text == "__AIST_CLEAR_CONVERSATION__":
                        log.info("Received special command to clear conversation history.")
                        self.conversation_manager.clear()
                        self.socket.send_string(json.dumps({})) # Send an empty ack
                        continue # Skip normal processing

                    console_log(f"'{command_text}' (State: {state})", prefix="RECV", color=Colors.CYAN)

                    # Add user's message to history and get the current context
                    self.conversation_manager.add_message(role="user", text=command_text)
                    history = self.conversation_manager.get_history()

                    # The dispatcher will handle retrieving relevant facts from long-term memory.
                    # We pass the conversation history to it for context.
                    response = command_dispatcher(command_text, state, self.llm, history)
                    
                    if response is None:
                        # If the dispatcher returns None (e.g., ignored command in DORMANT state),
                        # send a valid but empty JSON object back to the client to prevent errors.
                        response = {}

                    speak_text = response.get("speak") if response else None
                    console_log(f"Action: {response.get('action') if response else 'None'}, Speak: '{speak_text or 'None'}'", prefix="SEND", color=Colors.MAGENTA)
                    response_json = json.dumps(response)
                    self.socket.send_string(response_json)

                    if speak_text:
                        self.conversation_manager.add_message(role="assistant", text=speak_text)
            except Exception as e:
                log.error(f"Error processing request: {e}", exc_info=True)
                error_response = {"action": "COMMAND", "speak": "An error occurred processing your request."}
                self.socket.send_string(json.dumps(error_response))

    def stop(self):
        """Stops the IPC server gracefully."""
        log.info("Stopping IPC Server...")
        self.is_running = False
        if self.thread:
            self.thread.join()
        self.socket.close()
        self.context.term()
        log.info("IPC Server stopped.")



