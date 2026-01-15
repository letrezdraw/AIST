# AIST - Main Entry Point

# --- Core Libraries ---
import logging
from pystray import MenuItem as item, Icon as icon # type: ignore
from PIL import Image
import threading
import time
from typing import Callable, Dict, Any

# --- AIST Imports ---
from aist.core.audio import audio_manager
import keyboard
import zmq
from aist.core.events import bus, STT_TRANSCRIBED, TTS_SPEAK, STATE_CHANGED, VAD_STATUS_CHANGED
from aist.core.tts import initialize_tts_engine, subscribe_to_events
from aist.core.stt import initialize_stt_engine
from aist.core.ipc.client import IPCClient
from aist.core.ipc.protocol import STATE_DORMANT, STATE_LISTENING
from aist.core.log_setup import setup_logging, console_log, Colors
from aist.core.config_manager import config

log = logging.getLogger(__name__)

# --- Application State ---
class AppState:
    """A simple class to hold shared application state."""
    def __init__(self):
        """Initializes the application state."""
        self.is_running = True
        self._lock = threading.Lock()
    
    def stop(self):
        """Thread-safe way to signal shutdown."""
        with self._lock:
            self.is_running = False
    
    def is_active(self) -> bool:
        """Thread-safe way to check if still running."""
        with self._lock:
            return self.is_running

class FrontendEventProxy:
    """A proxy to send events from the frontend to the backend via IPC."""
    def __init__(self, ipc_client: IPCClient):
        self.ipc_client = ipc_client

    def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Sends the event to the backend."""
        log.debug(f"Forwarding event '{event_type}' to backend.")
        self.ipc_client.send_event(event_type, payload)

    def stop(self):
        """No-op to match the real broadcaster's interface."""
        pass

def main():
    """
    Sets up the IPC client, system tray icon, global hotkey, and starts the
    user-facing assistant thread.
    """
    print("---- EXECUTING main.py ----")
    setup_logging(is_frontend=True)

    # Initialize and start the IPC client to connect to the backend service
    ipc_client = IPCClient()
    ipc_client.start()

    # This proxy will forward events to the backend instead of broadcasting directly
    event_broadcaster = FrontendEventProxy(ipc_client)

    # --- State Machine ---
    assistant_state = STATE_DORMANT
    app_state = AppState()
    state_lock = threading.Lock()  # Thread-safe state updates
    
    # --- Icon Loading ---
    try:
        image = Image.open("icon.png")
    except Exception as e:
        log.warning(f"Could not load 'icon.png': {e}. Using default icon.")
        image = None

    tray_icon = None
    def shutdown_app():
        """Signals all parts of the application to shut down gracefully."""
        log.info("--- SHUTDOWN_APP CALLED --- Shutdown signal received. Terminating.")
        app_state.stop()  # Use thread-safe stop method
        ipc_client.stop()
        event_broadcaster.stop()

        p = audio_manager.get_pyaudio()
        if p:
            p.terminate()
            log.info("Shared PyAudio instance terminated.")

        if tray_icon:
            tray_icon.stop()

    # --- State Management Helper ---
    def set_assistant_state(new_state: str):
        """Updates, logs, and broadcasts the assistant's state (thread-safe)."""
        nonlocal assistant_state
        with state_lock:
            if new_state != assistant_state:
                assistant_state = new_state
                log.info(f"State changed to {assistant_state}.")
                event_broadcaster.broadcast("state:changed", {"state": assistant_state})
            
    menu = (item('Quit AIST', lambda icon, item: shutdown_app()),)
    tray_icon = icon("AIST", image, "AIST Assistant", menu)

    # --- Event Handler for Transcribed Text ---
    def _handle_transcription(text: str):
        nonlocal assistant_state
        if not app_state.is_active():  # Use thread-safe check
            return

        console_log(f"'{text}'", prefix="HEARD", color=Colors.CYAN)
        
        # The frontend no longer makes decisions. It just sends the input and its state to the backend.
        response = ipc_client.send_command(text, assistant_state)

        if not response:
            log.info("Received an empty or null response from backend (e.g., ignored command). Continuing.")
            return

        action = response.get("action")
        text_to_speak = response.get("speak")

        intent_info = response.get("intent")
        if intent_info:
            bus.sendMessage("intent:matched", data=intent_info) # Pass intent_info as keyword argument

        if text_to_speak:
            bus.sendMessage(TTS_SPEAK, text=text_to_speak)

        if action == "ACTIVATE":
            set_assistant_state(STATE_LISTENING)
        elif action == "DEACTIVATE":
            set_assistant_state(STATE_DORMANT)
        elif action == "EXIT":
            time.sleep(1.5)
            shutdown_app()

    def _handle_vad_status(status: str):
        """Broadcasts the VAD status to the GUI."""
        event_broadcaster.broadcast("vad:status_changed", {"status": status.upper()})
    
    def setup_services(icon):
        icon.visible = True

        quit_hotkey = config.get('hotkeys.quit', 'ctrl+win+x')
        log.info(f"Registering global quit hotkey: {quit_hotkey.upper()}")
        try:
            keyboard.add_hotkey(quit_hotkey, shutdown_app)
        except Exception as e:
            log.warning(f"Failed to register quit hotkey: {e}")

        def _text_command_listener():
            context = zmq.Context()
            socket = context.socket(zmq.PULL)
            port = config.get('ipc.text_command_port', 5557)
            socket.bind(f"tcp://*:{port}")
            log.info(f"Text command listener started on tcp://*:{port}")

            while app_state.is_active():  # Use thread-safe check
                try:
                    if socket.poll(1000):
                        command_text = socket.recv_string()
                        log.info(f"Received text command: '{command_text}'")
                        _handle_transcription(command_text)
                except zmq.ZMQError as e:
                    if e.errno == zmq.ETERM:
                        break
                    else:
                        log.error(f"ZMQ Error in text command listener: {e}")
                except Exception as e:
                    log.error(f"Error in text command listener: {e}", exc_info=True)
            
            socket.close()
            context.term()
            log.info("Text command listener stopped.")
        threading.Thread(target=_text_command_listener, daemon=True).start()

        stt_ready_event = threading.Event()

        # Initialize TTS
        tts_provider = initialize_tts_engine(event_broadcaster)
        subscribe_to_events()

        initialize_stt_engine(app_state, stt_ready_event, event_broadcaster)
        bus.subscribe(_handle_transcription, STT_TRANSCRIBED)
        bus.subscribe(_handle_vad_status, VAD_STATUS_CHANGED)

        console_log("Waiting for STT engine to be ready...", prefix="INIT")
        stt_ready_event.wait()

        console_log(f"--- AIST is {STATE_DORMANT} ---", prefix="STATE", color=Colors.YELLOW)
        bus.sendMessage(TTS_SPEAK, text="Assistant is online.")
    tray_icon.run(setup=setup_services)

    keyboard.remove_all_hotkeys()
    log.info("Global hotkeys unregistered.")

if __name__ == "__main__":
    main()