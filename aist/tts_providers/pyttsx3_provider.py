# aist/tts_providers/pyttsx3_provider.py
import logging
import pyttsx3
from .base import BaseTTSProvider
from aist.core.events import bus, TTS_STARTED, TTS_FINISHED

log = logging.getLogger(__name__)

class Pyttsx3Provider(BaseTTSProvider):
    """
    A Text-to-Speech (TTS) provider that uses the pyttsx3 library.
    pyttsx3 is an offline, cross-platform library that uses native speech engines.
    """

    def __init__(self):
        super().__init__()
        try:
            self.engine = pyttsx3.init()
            log.info("pyttsx3 TTS provider initialized.")
        except Exception as e:
            log.fatal(f"Failed to initialize pyttsx3 engine: {e}", exc_info=True)
            self.engine = None

    def speak(self, text: str):
        """
        Synthesizes the given text into speech and plays it.
        This method is blocking.
        """
        if not self.engine:
            log.error("pyttsx3 engine not initialized. Cannot speak.")
            return

        try:
            log.info(f"AIST Speaking: \"{text}\"")
            bus.sendMessage(TTS_STARTED)
            self.engine.say(text)
            self.engine.runAndWait()
            bus.sendMessage(TTS_FINISHED)
        except Exception as e:
            log.error(f"An error occurred while speaking with pyttsx3: {e}", exc_info=True)

    def stop(self):
        """
        Stops the current speech.
        """
        if self.engine:
            self.engine.stop()