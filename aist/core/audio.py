# aist/core/audio.py
import pyaudio
import logging

log = logging.getLogger(__name__)

class AudioManager:
    """
    A singleton class to manage a single, shared PyAudio instance.
    This prevents resource conflicts that can occur when multiple parts of the
    application try to initialize PyAudio independently.
    """
    _instance = None
    _pyaudio_instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            try:
                log.info("Initializing shared PyAudio instance...")
                cls._pyaudio_instance = pyaudio.PyAudio()
                log.info("Shared PyAudio instance initialized successfully.")
            except Exception as e:
                log.fatal(f"FATAL: Failed to initialize PyAudio: {e}", exc_info=True)
                cls._pyaudio_instance = None
        return cls._instance

    def get_pyaudio(self):
        """Returns the shared PyAudio instance."""
        return self._pyaudio_instance

# Global instance that can be imported by other modules.
audio_manager = AudioManager()