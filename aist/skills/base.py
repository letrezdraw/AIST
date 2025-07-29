# aist/skills/base.py
from abc import ABC, abstractmethod
import logging

log = logging.getLogger(__name__)

class BaseSkill(ABC):
    """
    Abstract base class for all AIST skills.
    Defines the standard interface for a skill's lifecycle and execution.
    """
    def __init__(self):
        self.skill_id = None

    def _register(self, skill_id: str):
        """
        Internal registration method called by the Skill Manager.
        This provides the skill with its unique ID.
        """
        self.skill_id = skill_id
        self.initialize()

    def initialize(self):
        """
        Called after the skill is loaded and registered.
        Override this for one-time setup.
        """
        pass

    @abstractmethod
    def register_intents(self, register_intent_handler: callable):
        """
        Called by the Skill Manager at startup. The skill must use the
        provided `register_intent_handler` to register its capabilities.
        """
        pass