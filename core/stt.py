# core/stt.py - Speech-to-Text Engine

import speech_recognition as sr
import threading
from core.tts import speak
from config import WAKE_WORD

def listen_for_wake_word(recognizer, source):
    """Listens in the background for the wake word using the provided audio source."""
    print(f"\nListening for wake word: '{WAKE_WORD}'")
    while True:
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio).lower()
            print(f"Heard: '{text}'") # <-- ADD THIS LINE FOR DEBUGGING
            if WAKE_WORD in text:
                print("Wake word detected!")
                speak("Yes? How can I help?")
                return True
        except sr.UnknownValueError:
            pass  # Ignore if it doesn't understand
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            speak("I'm having trouble connecting to the speech service.")
            threading.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred during wake word listening: {e}")
            speak("I've run into a microphone issue. Please restart me.")
            return False

def listen_for_command(recognizer, source):
    """Listens for a user command after the wake word is detected."""
    print("Listening for your command...")
    try:
        audio = recognizer.listen(source, timeout=5, phrase_time_limit=15)
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        return command
    except sr.WaitTimeoutError:
        speak("I didn't hear a command. Going back to sleep.")
        return None
    except sr.UnknownValueError:
        speak("I couldn't understand that. Please try again.")
        return None
    except sr.RequestError as e:
        speak("There was a connection issue. Please try again.")
        print(f"Speech Recognition Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during command listening: {e}")
        return None