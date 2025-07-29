# aist/skills/time_skill/__init__.py
import logging
from datetime import datetime
from aist.skills.base import BaseSkill

log = logging.getLogger(__name__)

class TimeSkill(BaseSkill):
    def initialize(self):
        log.info("Time skill initialized.")

    def register_intents(self, register_intent_handler):
        """Register this skill's intents."""
        register_intent_handler('get_current_time', {
            "phrases": [
                "what time is it",
                "what's the current time",
                "tell me the time"
            ],
            "handler": self.handle_get_time,
            "parameters": []
        })

    def handle_get_time(self, _payload):
        """Handler for getting the current time."""
        now = datetime.now()
        current_time = now.strftime("%I:%M %p")
        return f"The current time is {current_time}."

def create_skill():
    """The entry point for the skill loader."""
    return TimeSkill()