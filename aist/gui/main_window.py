# aist/gui/main_window.py
import customtkinter as ctk
import threading
import queue
import logging
import zmq
import json # New import
from aist.core.ipc.client import IPCClient
from aist.core.log_setup import setup_logging
from aist.core.gui_logging_handler import GUILoggingHandler
from aist.core.config_manager import config
from aist.core.ipc.protocol import INIT_STATUS_UPDATE # New import

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AIST - AI Assistant")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.log_queue = queue.Queue()
        self.ipc_client = IPCClient()

        self.llm_status = ctk.StringVar(value="LLM: Initializing...")
        self.tts_status = ctk.StringVar(value="TTS: Initializing...")
        self.stt_status = ctk.StringVar(value="STT: Initializing...")
        self.skills_status = ctk.StringVar(value="Skills: Initializing...") # New status variable

        self._setup_gui_logging()
        self._create_widgets()
        self._start_services()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_gui_logging(self):
        # The GUI process is a listener, not a broadcaster.
        # It just needs to start the thread that listens for logs.
        log_thread = threading.Thread(target=self._log_listener, daemon=True)
        log_thread.start()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Initialization Frame ---
        self.init_frame = ctk.CTkFrame(self)
        self.init_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.init_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.init_frame, text="Initializing Backend Services...", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        ctk.CTkLabel(self.init_frame, textvariable=self.llm_status, font=ctk.CTkFont(size=14)).grid(row=1, column=0, pady=5)
        ctk.CTkLabel(self.init_frame, textvariable=self.tts_status, font=ctk.CTkFont(size=14)).grid(row=2, column=0, pady=5)
        ctk.CTkLabel(self.init_frame, textvariable=self.stt_status, font=ctk.CTkFont(size=14)).grid(row=3, column=0, pady=5)
        ctk.CTkLabel(self.init_frame, textvariable=self.skills_status, font=ctk.CTkFont(size=14)).grid(row=4, column=0, pady=5) # New status label

        # --- Main Chat Frame ---
        self.chat_frame = ctk.CTkFrame(self)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_textbox = ctk.CTkTextbox(self.chat_frame, state="disabled", wrap="word")
        self.chat_textbox.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nsew")

        self.command_entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Enter command...")
        self.command_entry.grid(row=1, column=0, padx=(10, 5), pady=(5, 10), sticky="ew")
        self.command_entry.bind("<Return>", self._on_send_command)

        self.send_button = ctk.CTkButton(self.chat_frame, text="Send", command=self._on_send_command)
        self.send_button.grid(row=1, column=1, padx=(5, 10), pady=(5, 10), sticky="ew")

    def _start_services(self):
        self.ipc_client.start()
        self.after(100, self._process_log_queue)

    def _log_listener(self):
        context = zmq.Context()
        log_socket = context.socket(zmq.SUB)
        log_port = config.get('ipc.log_broadcast_port', 5558)
        log_socket.connect(f"tcp://localhost:{log_port}")
        log_socket.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all log messages

        event_socket = context.socket(zmq.SUB)
        event_port = config.get('ipc.event_bus_port', 5556)
        event_socket.connect(f"tcp://localhost:{event_port}")
        event_socket.setsockopt_string(zmq.SUBSCRIBE, INIT_STATUS_UPDATE.encode('utf-8')) # Subscribe to init status updates

        poller = zmq.Poller()
        poller.register(log_socket, zmq.POLLIN)
        poller.register(event_socket, zmq.POLLIN)

        while True:
            try:
                socks = dict(poller.poll(100)) # Poll with a timeout

                if log_socket in socks and socks[log_socket] == zmq.POLLIN:
                    log_message = log_socket.recv_string()
                    self.log_queue.put({"type": "log", "data": log_message})

                if event_socket in socks and socks[event_socket] == zmq.POLLIN:
                    event_type, payload_json = event_socket.recv_multipart()
                    payload = json.loads(payload_json.decode('utf-8'))
                    self.log_queue.put({"type": event_type.decode('utf-8'), "data": payload})

            except zmq.ZMQError as e:
                logging.error(f"ZMQ error in log listener: {e}")
                break
            except Exception as e:
                logging.error(f"Unexpected error in log listener: {e}", exc_info=True)
                break

    def _process_log_queue(self):
        try:
            while not self.log_queue.empty():
                item = self.log_queue.get_nowait()
                message_type = item["type"]
                data = item["data"]

                if message_type == "log":
                    # Original log message handling
                    self._update_status_from_log(data) # Keep for now, will refactor
                    if self.chat_frame.winfo_ismapped():
                        self.chat_textbox.configure(state="normal")
                        self.chat_textbox.insert("end", data + "\n")
                        self.chat_textbox.configure(state="disabled")
                        self.chat_textbox.see("end")
                elif message_type == INIT_STATUS_UPDATE:
                    self._handle_init_status_update(data)

        finally:
            self.after(100, self._process_log_queue)

    def _handle_init_status_update(self, data):
        component = data.get("component")
        status = data.get("status")
        error = data.get("error", "")
        provider = data.get("provider", "")
        count = data.get("count", 0)

        display_status = f"{status.capitalize()}"
        if error: display_status += f" (Error: {error})"
        if provider: display_status += f" ({provider})"
        if count: display_status += f" ({count} loaded)"

        if component == "llm":
            self.llm_status.set(f"LLM: {display_status}")
        elif component == "tts":
            self.tts_status.set(f"TTS: {display_status}")
        elif component == "stt":
            self.stt_status.set(f"STT: {display_status}")
        elif component == "skills":
            self.skills_status.set(f"Skills: {display_status}")

        self._check_all_initialized()

    def _check_all_initialized(self):
        # Check if all components are initialized (or failed, but not still initializing)
        all_ready = (
            "Initializing" not in self.llm_status.get() and
            "Initializing" not in self.tts_status.get() and
            "Initializing" not in self.stt_status.get() and
            "Initializing" not in self.skills_status.get()
        )

        if all_ready:
            self.after(1000, self._show_chat_frame)

    def _update_status_from_log(self, message):
        # This method is now deprecated for init status, but kept for general log parsing if needed.
        # It will be removed or refactored if all status updates come via INIT_STATUS_UPDATE.
        pass # No longer needed for init status, handled by _handle_init_status_update

    def _show_chat_frame(self):
        self.init_frame.grid_forget()
        self.chat_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _on_send_command(self, event=None):
        command_text = self.command_entry.get()
        if not command_text:
            return

        state = "LISTENING"
        self.command_entry.delete(0, "end")
        threading.Thread(target=self._send_command_thread, args=(command_text, state), daemon=True).start()

    def _send_command_thread(self, command_text, state):
        self.log_queue.put({"type": "log", "data": f"You: {command_text}"})
        response = self.ipc_client.send_command(command_text, state)
        if response:
            action = response.get("action")
            speak_text = response.get("speak")

            if action == "EXIT":
                self.after(100, self.destroy)

            if speak_text:
                log_message = f"AIST: {speak_text}"
                self.log_queue.put({"type": "log", "data": log_message})

    def on_closing(self):
        self.ipc_client.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()
