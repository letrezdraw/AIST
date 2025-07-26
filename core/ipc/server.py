# core/ipc/server.py - The "Brain" of the assistant

import json
import logging
import zmq
import threading

# AIST Core Imports
from core.llm import initialize_llm
from core.memory import retrieve_relevant_facts
from skills.dispatcher import command_dispatcher

log = logging.getLogger(__name__)

class IPCServer:
    """
    The backend server that listens for commands from the frontend,
    processes them using the LLM and skill dispatcher, and sends back a response.
    """
    def __init__(self):
        self.log = logging.getLogger(__name__)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:5555")

        # Initialize the core components of the "Brain"
        self.llm = initialize_llm()
        if not self.llm:
            raise RuntimeError("Failed to initialize the Language Model. Backend cannot start.")

        # For now, we assume a single client and have one session history.
        self.conversation_history = []

        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        """The main loop that waits for and handles requests."""
        self.log.info("IPC Server is listening on tcp://*:5555")
        while self.is_running:
            try:
                # Wait for the next request from the client
                request_json = self.socket.recv_string()
                request_data = json.loads(request_json)
                command = request_data.get("text")
                state = request_data.get("state")
                self.log.info(f"Received request from frontend: '{command}' (State: {state})")

                # 1. Retrieve relevant facts from memory
                facts = retrieve_relevant_facts(command)

                # 2. Call the command dispatcher to get a response
                # The dispatcher is the core logic that decides whether to chat or use a skill.
                response_dict = command_dispatcher(
                    command=command,
                    state=state,
                    llm=self.llm,
                    conversation_history=self.conversation_history,
                    relevant_facts=facts
                )

                # 3. Update conversation history
                # Only add to history if it was a successful command interaction.
                if response_dict.get("action") == "COMMAND":
                    self.conversation_history.append(('user', command))
                    self.conversation_history.append(('assistant', response_dict.get("speak")))

                # 4. Send the response back to the client
                self.socket.send_string(json.dumps(response_dict))

            except zmq.ZMQError as e:
                if e.errno == zmq.ETERM:
                    self.log.info("ZMQ context terminated, shutting down server loop.")
                    break
                else:
                    self.log.error(f"ZMQ Error in server loop: {e}", exc_info=True)
            except Exception as e:
                self.log.error(f"Unhandled exception in IPC server loop: {e}", exc_info=True)
                self.socket.send_string("I'm sorry, I encountered an internal error.")

    def start(self):
        """Starts the server loop in a background thread."""
        self.thread.start()

    def stop(self):
        """Stops the server gracefully."""
        self.log.info("Stopping IPC server...")
        self.is_running = False
        self.context.term() # This unblocks the blocking `recv()` call
        self.thread.join(timeout=2.0)
        self.log.info("IPC server stopped.")