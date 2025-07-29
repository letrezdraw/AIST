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
        :param app_state: The shared application state object.
        :param stt_ready_event: An event to signal when the STT engine is fully initialized.
        """
        self.app_state = app_state
        self.stt_ready_event = stt_ready_event

    @abstractmethod
    def run(self):
        """
        The main loop for the STT provider. This should block until the provider is stopped.
        It is responsible for listening to the audio stream and publishing transcriptions.
        """
        pass