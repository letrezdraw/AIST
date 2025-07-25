# skills/vision.py - Skills for screen awareness and UI interaction

try:
    from pywinauto import Desktop
except ImportError:
    print("Warning: pywinauto is not installed. Vision skills will not be available.")
    print("Please run 'pip install pywinauto' to enable them.")
    Desktop = None

def skill_get_active_window_info():
    """Gets information about the currently active window on the screen."""
    if not Desktop:
        return "The vision module is not available because pywinauto is not installed."
    try:
        # Use the 'uia' backend for better compatibility with modern applications
        desktop = Desktop(backend="uia")
        active_window = desktop.active_window()
        window_title = active_window.window_text()
        return f"The currently active window is titled: '{window_title}'."
    except Exception as e:
        print(f"Error getting active window info: {e}")
        return "I had trouble reading the screen. There might not be an active window."