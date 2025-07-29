# AIST - Main Entry Point

# --- Core Libraries ---
import logging
from pystray import MenuItem as item, Icon as icon # type: ignore
from PIL import Image
import threading
import time
from typing import Callable

# --- AIST Imports ---
from aist.core.audio import audio_manager
import keyboard
import zmq
from aist.core.events import bus, STT_TRANSCRIBED, TTS_SPEAK, STATE_CHANGED, VAD_STATUS_CHANGED
from aist.core.tts import initialize_tts_engine, subscribe_to_events
from aist.core.stt import initialize_stt_engine
from aist.core.ipc.client import IPCClient
from aist.core.ipc.event_bus import EventBroadcaster
from aist.core.log_setup import setup_logging, console_log, Colors
from aist.core.config_manager import config

# --- Application State ---
class AppState:
    """A simple class to hold shared application state."""
    def __init__(self):
        """Initializes the application state."""
        self.is_running = True

def main():
    """
    Sets up the IPC client, system tray icon, global hotkey, and starts the
    user-facing assistant thread.

    This is the main entry point of the AIST frontend application. It is responsible for:
    1. Setting up the logging system.
    2. Initializing the shared AppState.
    3. Creating the IPC client to connect to the backend.
    4. Setting up the system tray icon and its menu.
    5. Registering the global exit hotkey.
    6. Starting the `run_assistant` loop in a background thread.
    7. Running the system tray icon's event loop, which blocks the main thread.
    """
    setup_logging()
    log = logging.getLogger(__name__)

    # --- State Machine ---
    # 'DORMANT': Listening only for activation or exit phrases.
    # 'LISTENING': Actively listening for commands, deactivation, or exit phrases.
    assistant_state = 'DORMANT'
    app_state = AppState()
    # --- Icon Loading ---
    # We'll try to load the icon, but fall back to a default if it fails.
    # This makes the app more robust and helps debug startup issues.
    try:
        image = Image.open("icon.png")
    except Exception as e:
        log.warning(f"Could not load 'icon.png': {e}. Using default icon.")
        image = None # pystray will use a default icon

    # Initialize and start the IPC client to connect to the backend service
    ipc_client = IPCClient()
    # The main loop now handles responses synchronously, so the callback is no longer needed.
    ipc_client.start()

    # Initialize the event broadcaster for the GUI
    event_broadcaster = EventBroadcaster()

    # This will be our single point of shutdown logic, accessible to the tray and hotkey.
    tray_icon = None
    def shutdown_app():
        """Signals all parts of the application to shut down gracefully."""
        # Added extra logging to be certain when this function is called.
        log.info("--- SHUTDOWN_APP CALLED --- Shutdown signal received. Terminating.")
        app_state.is_running = False
        ipc_client.stop()
        event_broadcaster.stop()

        # Terminate the shared PyAudio instance gracefully.
        p = audio_manager.get_pyaudio()
        if p:
            p.terminate()
            log.info("Shared PyAudio instance terminated.")

        if tray_icon:
            tray_icon.stop()

    menu = (item('Quit AIST', lambda icon, item: shutdown_app()),)
    tray_icon = icon("AIST", image, "AIST Assistant", menu)

    # --- Event Handler for Transcribed Text ---
    def _handle_transcription(text: str):
        """
        This function is called when the STT engine publishes a transcription.
        It sends the text to the backend and handles the response.
        """
        nonlocal assistant_state
        if not app_state.is_running:
            return

        # Show the user exactly what the AI heard.
        console_log(f"'{text}'", prefix="HEARD", color=Colors.CYAN)
        event_broadcaster.broadcast("stt:heard", {"text": text})

        # Broadcast that the assistant is thinking
        event_broadcaster.broadcast("state:changed", {"state": "THINKING"})

        # The frontend no longer makes decisions. It just sends the input and its state to the backend.
        response = ipc_client.send_command(text, assistant_state)

        if not response:
            # If something went wrong, revert state to LISTENING
            event_broadcaster.broadcast("state:changed", {"state": "LISTENING"})
            log.info("Received an empty or null response from backend (e.g., ignored command). Continuing.")
            return

        # The backend now drives the state machine.
        action = response.get("action")
        text_to_speak = response.get("speak")

        intent_info = response.get("intent")
        if intent_info:
            event_broadcaster.broadcast("intent:matched", intent_info)

        if text_to_speak:
            event_broadcaster.broadcast("tts:speak", {"text": text_to_speak})
            bus.sendMessage(TTS_SPEAK, text=text_to_speak)

        if action == "ACTIVATE":
            assistant_state = 'LISTENING'
            log.info("State changed to LISTENING.")
            event_broadcaster.broadcast("state:changed", {"state": "LISTENING"})
            bus.sendMessage(STATE_CHANGED, state=assistant_state)
        elif action == "DEACTIVATE":
            assistant_state = 'DORMANT'
            log.info("State changed to DORMANT.")
            event_broadcaster.broadcast("state:changed", {"state": "DORMANT"})
            bus.sendMessage(STATE_CHANGED, state=assistant_state)
        elif action == "EXIT":
            # Give the "Goodbye" message time to play before shutting down.
            time.sleep(1.5)
            shutdown_app()

    def _handle_vad_status(status: str):
        """Broadcasts the VAD status to the GUI."""
        event_broadcaster.broadcast("vad:status", {"status": status.upper()})
    
    # --- Setup function for pystray ---
    # This function is run in a separate thread after the icon has been set up.
    # It's the recommended way to start background tasks.
    def setup_services(icon):
        icon.visible = True # Make the icon visible after setup

        # Broadcast component statuses now that all components are initializing.
        event_broadcaster.broadcast("component:status", {"name": "Event Bus", "status": "Broadcasting"})
        # Broadcast the backend status now that all components are initializing.
        event_broadcaster.broadcast("component:status", {"name": "Backend", "status": "Connected"})

        # --- Hotkey Listener Thread ---
        # We run the hotkey listener in its own thread to prevent it from
        # blocking or conflicting with the pystray event loop on the main thread.
        def _hotkey_listener():
            quit_hotkey = config.get('hotkeys.quit', 'ctrl+win+x')
            log.info(f"Registering global quit hotkey: {quit_hotkey.upper()}")
            try:
                keyboard.wait(quit_hotkey)
                log.info(f"Global quit hotkey ({quit_hotkey.upper()}) detected. Shutting down.")
                shutdown_app()
            except Exception as e:
                log.warning(f"Hotkey listener failed: {e}")
        threading.Thread(target=_hotkey_listener, daemon=True).start()

        def _text_command_listener():
            context = zmq.Context()
            socket = context.socket(zmq.PULL)
            port = config.get('ipc.text_command_port', 5557)
            socket.bind(f"tcp://*:{port}")
            log.info(f"Text command listener started on tcp://*:{port}")

            while app_state.is_running:
                try:
                    if socket.poll(1000): # 1 second timeout
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

        # Initialize TTS and broadcast its status
        tts_provider = initialize_tts_engine()
        subscribe_to_events()
        event_broadcaster.broadcast("component:status", {"name": "TTS", "status": "Ready" if tts_provider else "Failed"})

        initialize_stt_engine(app_state, stt_ready_event)
        bus.subscribe(_handle_transcription, STT_TRANSCRIBED)
        bus.subscribe(_handle_vad_status, VAD_STATUS_CHANGED)

        console_log("Waiting for STT engine to be ready...", prefix="INIT")
        stt_ready_event.wait() # This blocks until the STT provider signals it's ready
        event_broadcaster.broadcast("component:status", {"name": "STT", "status": "Ready"})

        console_log("--- AIST is DORMANT ---", prefix="STATE", color=Colors.YELLOW)
        event_broadcaster.broadcast("state:changed", {"state": "DORMANT"})
        # Provide an audio confirmation that the assistant is ready.
        bus.sendMessage(TTS_SPEAK, text="Assistant is online.")

    # The main thread is now blocked by the system tray icon's run() method.
    # All other work happens in background threads (STT) or via event handlers.
    tray_icon.run(setup=setup_services)

    # Cleanup hotkey when the application exits gracefully
    keyboard.remove_all_hotkeys()
    log.info("Global hotkeys unregistered.")

if __name__ == "__main__":
    main()