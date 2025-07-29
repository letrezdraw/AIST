# aist/tts_providers/base.py
from abc import ABC, abstractmethod

class BaseTTSProvider(ABC):
    """
    Abstract base class for all Text-to-Speech providers.
    This defines the standard interface for TTS engines, allowing them to be
    pluggable and interchangeable.
    """
    def __init__(self):
        """Initializes the provider."""
        pass

    @abstractmethod
    def speak(self, text: str):
        """
        Synthesizes the given text into speech and plays it.
        """
        pass