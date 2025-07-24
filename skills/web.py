# skills/web.py - Web-related skills

import webbrowser
from core.tts import speak

def skill_search_web(query):
    """Searches the web."""
    speak(f"Searching the web for {query}.")
    webbrowser.open(f"https://www.google.com/search?q={query}")