# aist/gui/main_window.py
import customtkinter as ctk
import threading
import queue
import logging
import zmq
import json
import time
from aist.core.ipc.client import IPCClient
from aist.core.log_setup import setup_logging
from aist.core.gui_logging_handler import GUILoggingHandler
from aist.core.config_manager import config
from aist.core.ipc.protocol import INIT_STATUS_UPDATE

log = logging.getLogger(__name__)

# Define constants for event types
STATE_CHANGED = "state:changed"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_logging(is_frontend=True) # Setup logging for GUI
        log.info("AIST GUI application started.")

        self.title("AIST - AI Assistant")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.log_queue = queue.Queue()
        self.ipc_client = IPCClient()

        self.llm_status = ctk.StringVar(value="LLM: Initializing...")
        self.tts_status = ctk.StringVar(value="TTS: Initializing...")
        self.stt_status = ctk.StringVar(value="STT: Initializing...")
        self.skills_status = ctk.StringVar(value="Skills: Initializing...")

        self._create_widgets()
        log.info("GUI widgets created.")
        self._start_services()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Content row

        # --- Status Bar Frame ---
        self.status_frame = ctk.CTkFrame(self, height=30)
        self.status_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")
        self.status_frame.grid_columnconfigure(4, weight=1) # Spacer

        self.llm_led = self._create_led("LLM", 0)
        self.tts_led = self._create_led("TTS", 1)
        self.stt_led = self._create_led("STT", 2)
        self.skills_led = self._create_led("Skills", 3)
        self.state_led = self._create_led("AI State", 5, "grey")

        # --- Content Frame ---
        self.content_frame = ctk.CTkFrame(self)
        self.content_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # --- Initialization Frame ---
        self.init_frame = ctk.CTkFrame(self.content_frame)
        self.init_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.init_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.init_frame, text="Initializing Backend Services...", font=ctk.CTkFont(size=20, weight="bold")).grid(row=0, column=0, pady=(20, 10))
        ctk.CTkLabel(self.init_frame, textvariable=self.llm_status, font=ctk.CTkFont(size=14)).grid(row=1, column=0, pady=5)
        ctk.CTkLabel(self.init_frame, textvariable=self.tts_status, font=ctk.CTkFont(size=14)).grid(row=2, column=0, pady=5)
        ctk.CTkLabel(self.init_frame, textvariable=self.stt_status, font=ctk.CTkFont(size=14)).grid(row=3, column=0, pady=5)
        ctk.CTkLabel(self.init_frame, textvariable=self.skills_status, font=ctk.CTkFont(size=14)).grid(row=4, column=0, pady=5)

        # --- Main Chat Frame ---
        self.chat_frame = ctk.CTkFrame(self.content_frame)
        self.chat_frame.grid_columnconfigure(0, weight=1)
        self.chat_frame.grid_rowconfigure(0, weight=1)

        self.chat_textbox = ctk.CTkTextbox(self.chat_frame, state="disabled", wrap="word")
        self.chat_textbox.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nsew")

        self.command_entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Enter command...")
        self.command_entry.grid(row=1, column=0, padx=(10, 5), pady=(5, 10), sticky="ew")
        self.command_entry.bind("<Return>", self._on_send_command)

        self.send_button = ctk.CTkButton(self.chat_frame, text="Send", command=self._on_send_command)
        self.send_button.grid(row=1, column=1, padx=(5, 10), pady=(5, 10), sticky="ew")

    def _create_led(self, name, col, color="yellow"):
        frame = ctk.CTkFrame(self.status_frame)
        frame.grid(row=0, column=col, padx=5, pady=5)
        led = ctk.CTkFrame(frame, width=15, height=15, corner_radius=10, fg_color=color)
        led.pack(side="left", padx=(0, 5))
        label = ctk.CTkLabel(frame, text=name)
        label.pack(side="left")
        return led

    def _start_services(self):
        log.info("Starting GUI services...")
        self.ipc_client.start()
        log_thread = threading.Thread(target=self._log_listener, daemon=True)
        log_thread.start()
        self.after(100, self._process_log_queue)

    def _log_listener(self):
        log.info("GUI log listener started.")
        context = zmq.Context()
        event_socket = context.socket(zmq.SUB)
        event_port = config.get('ipc.event_bus_port', 5556)
        event_socket.connect(f"tcp://localhost:{event_port}")
        event_socket.setsockopt_string(zmq.SUBSCRIBE, INIT_STATUS_UPDATE)
        event_socket.setsockopt_string(zmq.SUBSCRIBE, STATE_CHANGED)

        while True:
            try:
                event_type, payload_json = event_socket.recv_multipart()
                payload = json.loads(payload_json.decode('utf-8'))
                log.debug(f"Received event: {event_type.decode('utf-8')} with payload: {payload}")
                self.log_queue.put({"type": event_type.decode('utf-8'), "data": payload})
            except zmq.ZMQError as e:
                log.error(f"ZMQ error in log listener: {e}")
                break
            except Exception as e:
                log.error(f"Unexpected error in log listener: {e}", exc_info=True)
                break

    def _process_log_queue(self):
        try:
            while not self.log_queue.empty():
                item = self.log_queue.get_nowait()
                message_type = item["type"]
                data = item["data"]
                log.debug(f"Processing log queue item: Type={message_type}, Data={data}")

                if message_type == INIT_STATUS_UPDATE:
                    self._handle_init_status_update(data)
                elif message_type == STATE_CHANGED:
                    self._handle_state_changed(data)
                else:
                    if self.chat_frame.winfo_ismapped():
                        self.chat_textbox.configure(state="normal")
                        self.chat_textbox.insert("end", str(data) + "\n")
                        self.chat_textbox.configure(state="disabled")
                        self.chat_textbox.see("end")
        finally:
            self.after(100, self._process_log_queue)

    def _handle_init_status_update(self, data):
        log.info(f"Handling INIT_STATUS_UPDATE: {data}")
        component = data.get("component")
        status = data.get("status")
        error = data.get("error", "")
        provider = data.get("provider", "")
        count = data.get("count", 0)

        display_status = f"{status.capitalize()}"
        if error: display_status += f" (Error: {error})"
        if provider: display_status += f" ({provider})"
        if count: display_status += f" ({count} loaded)"

        led_color = "yellow"
        if status == "initialized":
            led_color = "green"
        elif status in ["failed", "error"]:
            led_color = "red"

        if component == "llm":
            self.llm_status.set(f"LLM: {display_status}")
            self.llm_led.configure(fg_color=led_color)
        elif component == "tts":
            self.tts_status.set(f"TTS: {display_status}")
            self.tts_led.configure(fg_color=led_color)
        elif component == "stt":
            self.stt_status.set(f"STT: {display_status}")
            self.stt_led.configure(fg_color=led_color)
        elif component == "skills":
            self.skills_status.set(f"Skills: {display_status}")
            self.skills_led.configure(fg_color=led_color)

        self._check_all_initialized()

    def _handle_state_changed(self, data):
        log.info(f"Handling STATE_CHANGED: {data}")
        state = data.get("state", "DORMANT").upper()
        color = "grey"
        if state == "LISTENING":
            color = "blue"
        elif state == "THINKING":
            color = "purple"
        elif state == "SPEAKING":
            color = "cyan"
        self.state_led.configure(fg_color=color)

    def _check_all_initialized(self):
        log.info("Checking if all components are initialized...")
        all_ready = (
            "Initializing" not in self.llm_status.get() and
            "Initializing" not in self.tts_status.get() and
            "Initializing" not in self.stt_status.get() and
            "Initializing" not in self.skills_status.get()
        )

        if all_ready:
            log.info("All components reported as initialized. Transitioning to chat frame.")
            self.after(1000, self._show_chat_frame)
        else:
            log.info("Not all components are initialized yet.")

    def _show_chat_frame(self):
        log.info("Showing chat frame.")
        self.init_frame.grid_forget()
        self.chat_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

    def _on_send_command(self, event=None):
        log.info("Send command button pressed.")
        command_text = self.command_entry.get()
        if not command_text:
            log.warning("Command entry is empty.")
            return

        state = "LISTENING"
        self.command_entry.delete(0, "end")
        log.info(f"Sending command to backend: '{command_text}'")
        threading.Thread(target=self._send_command_thread, args=(command_text, state), daemon=True).start()

    def _send_command_thread(self, command_text, state):
        log.debug(f"_send_command_thread started for command: '{command_text}'")
        self.log_queue.put({"type": "log", "data": f"You: {command_text}"})
        response = self.ipc_client.send_command(command_text, state)
        if response:
            action = response.get("action")
            speak_text = response.get("speak")
            log.info(f"Received response from backend. Action: {action}, Speak: {speak_text}")

            if action == "EXIT":
                log.info("Received EXIT action. Initiating GUI shutdown.")
                self.after(100, self.on_closing)

            if speak_text:
                log_message = f"AIST: {speak_text}"
                self.log_queue.put({"type": "log", "data": log_message})

    def on_closing(self):
        log.info("GUI closing initiated.")
        # Fade out animation
        for i in range(10, -1, -1):
            self.attributes("-alpha", i/10)
            self.update_idletasks()
            time.sleep(0.03)
        self.ipc_client.stop()
        log.info("IPC Client stopped. Destroying GUI.")
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()