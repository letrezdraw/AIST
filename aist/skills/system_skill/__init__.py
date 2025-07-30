# aist/skills/system_skill/__init__.py
import logging
import os
import sys
import subprocess
from aist.skills.base import BaseSkill

log = logging.getLogger(__name__)

class SystemSkill(BaseSkill):
    def initialize(self):
        log.info("System skill initialized.")

    def register_intents(self, register_intent_handler):
        """Register this skill's intents."""
        register_intent_handler('open_application', {
            "phrases": [
                "open application",
                "launch application",
                "start application",
                "open"
            ],
            "handler": self.handle_open_application,
            "parameters": [
                {"name": "app_name", "description": "The name of the application to open (e.g., 'notepad', 'calc', 'explorer')."}
            ]
        })

    def handle_open_application(self, payload):
        """Handler for opening an application."""
        app_name = payload.get("app_name")
        if not app_name:
            return "Which application would you like to open?"
        
        try:
            log.info(f"Attempting to open application: {app_name}")
            if sys.platform == "win32":
                os.startfile(app_name)
            elif sys.platform == "darwin": # macOS
                subprocess.Popen(["open", app_name])
            else: # Linux and other UNIX-like systems
                subprocess.Popen(["xdg-open", app_name])
            return f"I've opened {app_name} for you."
        except FileNotFoundError:
            log.error(f"Application not found: {app_name}")
            return f"Sorry, I couldn't find an application named {app_name}."
        except Exception as e:
            log.error(f"An unexpected error occurred while trying to open {app_name}: {e}", exc_info=True)
            return f"Sorry, an unexpected error occurred while trying to open {app_name}."

def create_skill():
    """The entry point for the skill loader."""
    return SystemSkill()