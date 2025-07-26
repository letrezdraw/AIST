# aist/skills/system.py
import os
import logging
from .skill_loader import aist_skill

log = logging.getLogger(__name__)

@aist_skill
def open_application(app_name: str) -> str:
    """
    Opens a specified application on the Windows operating system.
    The application name should be what you would type in the 'Run' dialog (e.g., 'notepad', 'calc', 'explorer').
    """
    try:
        log.info(f"Attempting to open application: {app_name}")
        os.startfile(app_name)
        return f"I've opened {app_name} for you."
    except FileNotFoundError:
        log.error(f"Application not found: {app_name}")
        return f"Sorry, I couldn't find an application named {app_name}."
    except Exception as e:
        log.error(f"An unexpected error occurred while trying to open {app_name}: {e}", exc_info=True)
        return f"Sorry, an unexpected error occurred while trying to open {app_name}."