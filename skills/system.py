# skills/system.py - System-related skills

import os
import datetime
import psutil
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
    """Gets and speaks system information like CPU and battery status."""
    if "cpu" in stat_type or "processor" in stat_type:
        cpu_usage = psutil.cpu_percent(interval=1)
        speak(f"The current CPU usage is at {cpu_usage:.1f} percent.")
    elif "battery" in stat_type or "power" in stat_type:
        battery = psutil.sensors_battery()
        if battery:
            plugged_in = "plugged in and charging" if battery.power_plugged else "on battery power"
            speak(f"The battery is at {battery.percent} percent and is currently {plugged_in}.")
        else:
            speak("I can't find a battery on this system. It might be a desktop computer.")
    else:
        speak(f"I'm not sure how to check the system status for {stat_type}.")