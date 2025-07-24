# skills/system.py - System-related skills

import os
import datetime
from core.tts import speak

def skill_open_application(app_name):
    """Opens an application."""
    speak(f"Opening {app_name}.")
    try:
        os.system(f'start {app_name}')
    except Exception as e:
        speak(f"Sorry, I couldn't open {app_name}. I ran into an error.")
        print(f"Error opening application: {e}")

def skill_get_time():
    """Gets and speaks the current time."""
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M %p")
    speak(f"The current time is {current_time}.")

def skill_get_system_info(stat_type):
    """Gets system information (placeholder)."""
    speak(f"I can't check the {stat_type} yet, but this feature is coming soon.")