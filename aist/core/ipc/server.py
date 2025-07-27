import json
import zmq
import logging
import threading
from aist.core.log_setup import console_log, Colors
from aist.skills.dispatcher import command_dispatcher # type: ignore
from aist.core.llm import initialize_llm

log = logging.getLogger(__name__)

class IPCServer:
    """
    The ZMQ server that listens for frontend requests.
    It processes commands using the skill dispatcher and returns JSON responses.
    """
    def __init__(self, host="tcp://*:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(host)
        self.is_running = False
        self.thread = None
        self.llm = None

    def start(self):
        """Starts the IPC server and loads the LLM model. Returns True on success, False on failure."""
        console_log("Initializing LLM...", prefix="INIT")
        self.llm = initialize_llm()
        if self.llm is None:
            log.fatal("Failed to initialize LLM. IPC Server will not start.")
            return False
        self.is_running = True
        self.thread = threading.Thread(target=self._serve_forever, daemon=True)
        self.thread.start()
        console_log("IPC Server started and listening for requests.", prefix="INIT", color=Colors.GREEN)
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
                    message = self.socket.recv_string()
                    request = json.loads(message)
                    command_text = request.get("text", "")
                    state = request.get("state", "DORMANT")
                    console_log(f"'{command_text}' (State: {state})", prefix="RECV", color=Colors.CYAN)

                    # For simplicity, conversation history and relevant facts are empty here
                    response = command_dispatcher(command_text, state, self.llm, [], [])
                    speak_text = response.get('speak', 'None') if response else 'None'
                    console_log(f"Action: {response.get('action') if response else 'None'}, Speak: '{speak_text}'", prefix="SEND", color=Colors.MAGENTA)
                    response_json = json.dumps(response)
                    self.socket.send_string(response_json)
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
