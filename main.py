# AIST - Main Entry Point

# --- Core Libraries ---
import logging
from pystray import MenuItem as item, Icon as icon
from PIL import Image
import keyboard
import threading
import time
from typing import Callable

# --- AIST Imports ---
from core.tts import speak
from core.stt import listen_generator
from core.ipc.client import IPCClient
from config import ACTIVATION_PHRASES, DEACTIVATION_PHRASES, EXIT_PHRASES
from core.log_setup import setup_logging

# --- Application State ---
class AppState:
    """A simple class to hold shared application state."""
    def __init__(self):
        """Initializes the application state."""
        self.is_running = True

def run_assistant(app_state: AppState, ipc_client: IPCClient, shutdown_callback: Callable[[], None]) -> None:
    """
    The main user-facing logic loop. It handles microphone input and sends
    commands to the backend via the IPC client.

    This function initializes the STT engine, runs a state machine to handle
    DORMANT/LISTENING states, and sends commands to the backend via the IPC client.
    It's designed to run in a separate thread and will call the `shutdown_callback`
    to terminate the entire application if it exits unexpectedly.

    Args:
        app_state (AppState): The shared object holding the application's running state.
        ipc_client (IPCClient): The client instance for communicating with the backend.
        shutdown_callback (Callable[[], None]): A zero-argument function to be called to
                                               initiate a graceful shutdown of the application.
    """
    log = logging.getLogger(__name__)

    # Provide an audio confirmation that the voice is ready and the assistant thread has started.
    # This is better placed here than in main() to ensure it's in the correct thread context.
    speak("Assistant is online.")

    # This outer try/finally ensures that if the assistant thread crashes for any reason,
    # it triggers a full application shutdown, preventing a "zombie" state.
    try:
        # --- State Machine ---
        # 'DORMANT': Listening only for activation or exit phrases.
        # 'LISTENING': Actively listening for commands, deactivation, or exit phrases.
        assistant_state = 'DORMANT'
        log.info("--- AIST is DORMANT. Listening for wake word. ---")

        # The main loop now consumes from the listening generator.
        # The generator handles all microphone and STT logic internally.
        for user_input in listen_generator(app_state):
            if not app_state.is_running:
                break

            if assistant_state == 'DORMANT':
                if any(phrase in user_input for phrase in ACTIVATION_PHRASES):
                    assistant_state = 'LISTENING'
                    log.info("Activation phrase heard. AIST is now LISTENING.")
                    speak("I'm listening.")
            
            elif assistant_state == 'LISTENING':
                # Check for control phrases first, in order of priority.
                if any(phrase in user_input for phrase in EXIT_PHRASES):
                    speak("Goodbye.")
                    # Give the TTS a moment to finish speaking before shutting down
                    time.sleep(1.5)
                    shutdown_callback()
                    break
                elif any(phrase in user_input for phrase in DEACTIVATION_PHRASES):
                    assistant_state = 'DORMANT'
                    log.info("Deactivation phrase heard. AIST is now DORMANT.")
                    speak("Pausing.")
                else:
                    # If no control phrase was detected, it's a command.
                    log.info(f"Command Heard: '{user_input}'")
                    ipc_client.send_command(user_input)

    except Exception as e:
        log.error(f"An unhandled exception occurred in the assistant thread: {e}", exc_info=True)
    finally:
        # This block ensures that no matter how the loop exits (normally or via exception),
        # we attempt a graceful shutdown of the whole application.
        if app_state.is_running:
            log.warning("Assistant loop is terminating unexpectedly. Triggering full shutdown.")
            # Set the flag to false before calling the callback to prevent potential recursion
            app_state.is_running = False
            shutdown_callback()
        log.info("Assistant loop has terminated.")

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

    app_state = AppState()
    image = Image.open("icon.png")

    # Initialize and start the IPC client to connect to the backend service
    ipc_client = IPCClient()
    # Set the callback for the IPC client to use our new speaking function
    # This allows the client to make the assistant speak when a response is received.
    ipc_client.on_response_received = lambda text: speak(text)
    ipc_client.start()

    # This will be our single point of shutdown logic, accessible to the tray and hotkey.
    tray_icon = None
    def shutdown_app():
        """Signals all parts of the application to shut down gracefully."""
        log.info("Shutdown signal received. Terminating.")
        app_state.is_running = False
        ipc_client.stop()
        if tray_icon:
            tray_icon.stop()

    menu = (item('Quit AIST', lambda icon, item: shutdown_app()),)
    tray_icon = icon("AIST", image, "AIST Assistant", menu)

    # Register the global hotkey to call the same shutdown function.
    try:
        keyboard.add_hotkey('ctrl+win+x', shutdown_app)
        log.info("Registered global hotkey Ctrl+Win+X to force quit.")
    except Exception as e:
        log.warning(f"Could not register global hotkey. You may need to run as administrator. Error: {e}")

    threading.Thread(target=run_assistant, args=(app_state, ipc_client, shutdown_app), daemon=True).start()
    tray_icon.run()

    # Cleanup hotkey when the application exits gracefully
    keyboard.remove_all_hotkeys()
    log.info("Global hotkeys unregistered.")

if __name__ == "__main__":
    main()