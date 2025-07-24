# core/tts.py - Text-to-Speech Engine

import pyttsx3
from config import ASSISTANT_NAME

# Initialize Text-to-Speech Engine
try:
    engine = pyttsx3.init()
except Exception as e:
    print(f"Error initializing TTS engine: {e}")
    engine = None

def speak(text):
    """Converts text to speech."""
    if engine and text:
        print(f"{ASSISTANT_NAME}: {text}")
        engine.say(text)
        engine.runAndWait()