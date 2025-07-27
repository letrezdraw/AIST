# aist/stt_providers/base.py
from abc import ABC, abstractmethod
import threading

class BaseSTTProvider(ABC):
    """
    Abstract base class for all Speech-to-Text providers.
    This defines the standard interface for STT engines, allowing them to be
    pluggable and interchangeable.
    """
    def __init__(self, app_state, stt_ready_event: threading.Event):
        """
        Initializes the provider.
        
        Args:
            app_state: The shared application state object.
            stt_ready_event: A threading event to signal when the provider is ready.
        """
        self.app_state = app_state
        self.stt_ready_event = stt_ready_event

    @abstractmethod
    def run(self):
        """Starts the main listening loop for the provider."""
        pass