# skills/web.py - Web-related skills

import webbrowser

def skill_search_web(query: str):
    """Searches the web for a given query using the default browser."""
    if not query:
        return "What would you like me to search for?"
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Searching the web for '{query}'."