# AIST.io - Main Entry Point

# --- Core Libraries ---
import threading
import sys
import speech_recognition as sr
from pystray import MenuItem as item, Icon as icon
from PIL import Image

# --- AIST.io Imports ---
from core.llm import initialize_llm
from core.tts import speak
from core.stt import listen_for_wake_word, listen_for_command
from skills.dispatcher import command_dispatcher

# --- Main Loop ---
def run_assistant(tray_icon):
    """The main logic loop for the assistant, designed to run in a thread."""
    global assistant_thread_running
    assistant_thread_running = True
    llm = initialize_llm()
    if not llm:
        speak("Assistant cannot start because the AI model failed to load.")
        return

    speak("Assistant activated. Initializing microphone...")
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            print("Adjusting for ambient noise... Please wait.")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("Microphone ready.")

            while assistant_thread_running:
                if not listen_for_wake_word(recognizer, source):
                    speak("Halting due to a critical microphone error.")
                    break

                command = listen_for_command(recognizer, source)
                if command:
                    if not command_dispatcher(command, llm):
                        assistant_thread_running = False # Stop if dispatcher signals exit
                        break # Exit signal from dispatcher

            if tray_icon.visible:
                tray_icon.stop()

    except (IOError, AttributeError) as e:
        speak("Could not access the microphone. Please ensure it is connected and permissions are set.")
        print(f"Microphone Error: {e}")
    except Exception as e:
        speak("An unexpected error occurred with the microphone.")
        print(f"Unexpected Error: {e}")
    
    assistant_thread_running = False

def quit_assistant(tray_icon, item):
    """Callback function to quit the assistant from the tray menu."""
    global assistant_thread_running
    assistant_thread_running = False
    tray_icon.stop()
    # A more forceful exit might be needed if threads don't close gracefully
    sys.exit(0)

def main():
    """Sets up the system tray icon and starts the assistant thread."""
    image = Image.open("icon.png")
    menu = (item('Quit', quit_assistant),)
    tray_icon = icon("AIST.io", image, "AIST.io Assistant", menu)

    threading.Thread(target=run_assistant, args=(tray_icon,), daemon=True).start()
    tray_icon.run()

if __name__ == "__main__":
    main()