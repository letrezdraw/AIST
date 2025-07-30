# aist/gui/main_window.py
import customtkinter as ctk
import threading
import queue
import logging
import zmq
from aist.core.ipc.client import IPCClient
from aist.core.log_setup import setup_logging
from aist.core.gui_logging_handler import GUILoggingHandler
from aist.core.config_manager import config

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AIST - AI Assistant")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.log_queue = queue.Queue()
        self.ipc_client = IPCClient()

        self._setup_gui_logging()
        self._create_widgets()
        self._start_services()

        # Ensure graceful shutdown when the window is closed via the 'X' button
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_gui_logging(self):
        """
        Sets up logging for the GUI process.
        This includes the GUI handler that broadcasts logs to this window.
        """
        # 1. Set up base logging (file, console)
        setup_logging()

        # 2. Add the GUI-specific handler to broadcast logs
        # This is a cleaner separation of concerns than the previous implementation.
        formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(name)-22s - %(message)s')
        gui_handler = GUILoggingHandler()
        gui_handler.setFormatter(formatter)
        gui_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(gui_handler)

        # 3. Start a thread to listen for broadcasted logs
        log_thread = threading.Thread(target=self._log_listener, daemon=True)
        log_thread.start()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Main Frame ---
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # --- Log/Output Text Box ---
        self.log_textbox = ctk.CTkTextbox(main_frame, state="disabled", wrap="word")
        self.log_textbox.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="nsew")

        # --- Command Entry ---
        self.command_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter command...")
        self.command_entry.grid(row=1, column=0, padx=(10, 5), pady=(5, 10), sticky="ew")
        self.command_entry.bind("<Return>", self._on_send_command)

        # --- Send Button ---
        self.send_button = ctk.CTkButton(main_frame, text="Send", command=self._on_send_command)
        self.send_button.grid(row=1, column=1, padx=(5, 10), pady=(5, 10), sticky="ew")

    def _start_services(self):
        """Start the IPC client and begin processing the log queue."""
        self.ipc_client.start()
        self.after(100, self._process_log_queue)

    def _log_listener(self):
        """Listens for log messages on the ZMQ SUB socket and puts them in a queue."""
        context = zmq.Context()
        socket = context.socket(zmq.SUB)
        port = config.get('ipc.log_broadcast_port', 5558)
        socket.connect(f"tcp://localhost:{port}")
        socket.setsockopt_string(zmq.SUBSCRIBE, "") # Subscribe to all messages

        while True:
            try:
                log_message = socket.recv_string()
                self.log_queue.put(log_message)
            except zmq.ZMQError:
                break # Context was terminated

    def _process_log_queue(self):
        """Processes messages from the log queue and updates the GUI."""
        try:
            while not self.log_queue.empty():
                message = self.log_queue.get_nowait()
                self.log_textbox.configure(state="normal")
                self.log_textbox.insert("end", message + "\n")
                self.log_textbox.configure(state="disabled")
                self.log_textbox.see("end")
        finally:
            self.after(100, self._process_log_queue)

    def _on_send_command(self, event=None):
        """Handles the send command action."""
        command_text = self.command_entry.get()
        if not command_text:
            return

        # For now, we'll assume the state is always LISTENING when using the GUI
        # A more advanced GUI could have a visual state indicator.
        state = "LISTENING"

        # Clear the entry box
        self.command_entry.delete(0, "end")

        # Run the command in a separate thread to avoid blocking the GUI
        threading.Thread(target=self._send_command_thread, args=(command_text, state), daemon=True).start()

    def _send_command_thread(self, command_text, state):
        """Sends the command to the backend and handles the response."""
        response = self.ipc_client.send_command(command_text, state)
        if response:
            # You can add more logic here to handle different response actions
            # For example, updating a status label, showing an image, etc.
            action = response.get("action")
            speak_text = response.get("speak")

            if action == "EXIT":
                self.after(100, self.destroy) # Schedule GUI shutdown

            if speak_text:
                # In a real application, you might have the TTS engine play this.
                # For now, we'll just log it to the GUI.
                log_message = f"AIST: {speak_text}"
                self.log_queue.put(log_message)

    def on_closing(self):
        self.ipc_client.stop()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()