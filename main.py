# AIST - Main Entry Point

# --- Core Libraries ---
import sys
import speech_recognition as sr
from pystray import MenuItem as item, Icon as icon
from PIL import Image

# --- AIST Imports ---
from core.llm import initialize_llm
from core.tts import speak
from core.stt import listen_for_wake_word, listen_for_command
from skills.dispatcher import command_dispatcher

# --- Application State ---
class AppState:
    """A simple class to hold shared application state."""
    def __init__(self):
        self.is_running = True

# --- Main Loop ---
def run_assistant(app_state, tray_icon):
    """The main logic loop for the assistant, designed to run in a thread."""
    llm = initialize_llm()
    if not llm:
        speak("Assistant cannot start because the AI model failed to load.")
        app_state.is_running = False
        if tray_icon.visible:
            tray_icon.stop()
        return

    speak("Assistant activated. Initializing microphone...")
    recognizer = sr.Recognizer()
    # Adjust the recognizer's sensitivity to ambient noise.
    # A higher value means it's less sensitive, which helps ignore the end of its own speech.
    recognizer.energy_threshold = 1000
    # Seconds of non-speaking audio before a phrase is considered complete
    recognizer.pause_threshold = 1.5
    # This setting helps it adapt to changing noise levels automatically.
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            print("Adjusting for ambient noise... Please wait.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone ready.")

            speak("Waiting for the wake word to begin.")

            # --- Main application loop: Listen -> Command -> Process -> Repeat ---
            while app_state.is_running:
                # 1. Listen for the wake word to activate the assistant
                if not listen_for_wake_word(recognizer, source):
                    # This indicates a critical error from the STT function itself
                    speak("Halting due to a critical microphone error.")
                    break # Exit the main while loop

                # 2. Wake word detected, now listen for a single command
                speak("I'm listening.") # A shorter, better activation message

                command = listen_for_command(recognizer, source)

                # Check if quit was requested from the tray while we were listening
                if not app_state.is_running:
                    break

                if command:
                    # 3. Process the command
                    response = command_dispatcher(command, llm)

                    if response is False:
                        aist_say("Goodbye!")
                        app_state.is_running = False # Set flag to terminate the loop
                        break
                    elif isinstance(response, str) and response.strip():
                        # More robust check for unhelpful LLM "thinking out loud" responses
                        if "[insert" in response or "based on the user's request" in response.lower():
                            aist_say("I had trouble processing that. Could you please rephrase your command?")
                        else:
                            aist_say(response)
                # If command is None (due to timeout or not understanding), the loop
                # simply restarts, correctly waiting for the wake word again.
    except (IOError, AttributeError) as e:
        speak("Could not access the microphone. Please ensure it is connected and permissions are set.")
        print(f"Microphone Error: {e}")
    except Exception as e:
        speak("An unexpected error occurred with the microphone.")
        print(f"Unexpected Error: {e}")
    
    app_state.is_running = False
    if tray_icon.visible:
        tray_icon.stop()

def quit_assistant(tray_icon, item, app_state):
    """Callback function to quit the assistant from the tray menu."""
    print("Quit requested from tray. Shutting down.")
    app_state.is_running = False
    tray_icon.stop()

def aist_say(message):
    """Helper function for the assistant to speak and print messages."""
    print(f"AIST: {message}")
    speak(message)

def main():
    """Sets up the system tray icon and starts the assistant thread."""
    # Using a dedicated thread library is good practice, but standard library is fine for this.
    import threading
    app_state = AppState()
    image = Image.open("icon.png")
    menu = (item('Quit AIST', lambda icon, item: quit_assistant(icon, item, app_state)),)
    tray_icon = icon("AIST", image, "AIST Assistant", menu)

    threading.Thread(target=run_assistant, args=(app_state, tray_icon), daemon=True).start()
    tray_icon.run()

if __name__ == "__main__":
    main()