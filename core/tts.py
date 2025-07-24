# core/tts.py - Text-to-Speech Engine

import pyttsx3
from config import ASSISTANT_NAME

# Initialize Text-to-Speech Engine
try:
    # Explicitly specify the SAPI5 driver for better compatibility on Windows
    engine = pyttsx3.init('sapi5')
except Exception as e:
    print(f"Error initializing TTS engine: {e}")
    engine = None

def speak(text):
    """Converts text to speech."""
    if engine and text:
        engine.say(text)
        try:
            engine.runAndWait()
        except RuntimeError as e:
            print(f"Error during speech synthesis: {e}")