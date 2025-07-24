# skills/system.py - System-related skills

import os
import datetime
import psutil
import subprocess

def skill_open_application(parameters):
    """Opens an application."""
    app_name = parameters.get("app_name")
    if not app_name:
        return "You need to tell me which application to open."
    try:
        os.system(f'start {app_name}')
        return f"Opening {app_name}."
    except Exception as e:
        print(f"Error opening application: {e}")
        return f"Sorry, I couldn't open {app_name}. I ran into an error."

def skill_close_application(parameters):
    """Closes a running application by its name."""
    app_name = parameters.get("app_name")
    if not app_name:
        return "You need to tell me which application to close."

    # Sanitize the app name to match common executable names
    if ".exe" not in app_name:
        app_name += ".exe"

    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'].lower() == app_name.lower():
            try:
                p = psutil.Process(proc.info['pid'])
                p.terminate() # Gracefully terminate the process
                return f"I've closed {app_name}."
            except psutil.Error as e:
                print(f"Error closing application: {e}")
                return f"I found {app_name}, but couldn't close it. You might need to do it manually."
    return f"I couldn't find an application named {app_name} running."

def skill_get_time(parameters):
    """Gets the current time."""
    now = datetime.datetime.now()
    current_time = now.strftime("%I:%M %p")
    return f"The current time is {current_time}."

def skill_get_system_info(parameters):
    """Gets system information like CPU and battery status."""
    stat_type = parameters.get("stat_type", "")
    if "cpu" in stat_type or "processor" in stat_type:
        cpu_usage = psutil.cpu_percent(interval=1)
        return f"The current CPU usage is at {cpu_usage:.1f} percent."
    elif "battery" in stat_type or "power" in stat_type:
        battery = psutil.sensors_battery()
        if battery:
            plugged_in = "plugged in and charging" if battery.power_plugged else "on battery power"
            return f"The battery is at {battery.percent} percent and is currently {plugged_in}."
        else:
            return "I can't find a battery on this system. It might be a desktop computer."
    else:
        return f"I'm not sure how to check the system status for {stat_type}."

def skill_execute_system_command(parameters):
    """Executes a shell command and returns its raw output for summarization."""
    shell_command = parameters.get("shell_command")
    if not shell_command:
        return "Error: No command provided to execute."

    print(f"Executing system command: '{shell_command}'")
    try:
        # Execute the command, capturing output and using a timeout.
        result = subprocess.run(
            shell_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode == 0:
            # Command was successful
            return result.stdout.strip() if result.stdout.strip() else "The command ran successfully but produced no output."
        else:
            # Command failed
            return f"The command failed with the following error: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"The command '{shell_command}' timed out."
    except Exception as e:
        return f"An error occurred while executing '{shell_command}': {e}"