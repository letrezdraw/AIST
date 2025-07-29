# aist/tts_providers/piper_provider.py
import os
import logging
import io
import wave
from piper.voice import PiperVoice
from aist.core.audio import audio_manager
from aist.core.events import bus, TTS_STARTED, TTS_FINISHED
from aist.core.config_manager import config
from .base import BaseTTSProvider

log = logging.getLogger(__name__)

class PiperProvider(BaseTTSProvider):
    """The Piper TTS engine provider."""

    def __init__(self):
        super().__init__()
        self.voice = self._load_voice()
        self.p = audio_manager.get_pyaudio()

    def _load_voice(self):
        """Loads the Piper voice model from the path specified in the config."""
        voice = None
        model_path = None
        try:
            model_path_config = config.get('models.tts.piper_voice_model')
            if not model_path_config:
                log.fatal("FATAL: Piper TTS model path is not configured in config.yaml (models.tts.piper_voice_model).")
            else:
                model_path = os.path.abspath(model_path_config)
                model_config_path = f"{model_path}.json"

                if not os.path.exists(model_path) or not os.path.exists(model_config_path):
                    log.fatal(f"Piper voice model or config not found at '{model_path}'")
                else:
                    log.info("Loading Piper TTS voice... This may take a moment.")
                    voice = PiperVoice.load(model_path, config_path=model_config_path)
                    log.info("Piper TTS voice loaded successfully.")
        except Exception as e:
            log.error(f"Error initializing Piper TTS engine for model '{model_path}': {e}", exc_info=True)
        return voice

    def speak(self, text: str):
        """Synthesizes text and plays the audio."""
        if not self.voice:
            log.error("TTS engine (Piper) not available. Cannot play audio.")
            return
        if not text:
            return

        log.info(f"AIST Speaking: \"{text}\"")
        if not self.p:
            log.error("PyAudio instance not available. Cannot play audio.")
            return

        stream = None
        try:
            bus.sendMessage(TTS_STARTED)
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file_writer:
                self.voice.synthesize_wav(text, wav_file=wav_file_writer)
            wav_buffer.seek(0)
            with wave.open(wav_buffer, 'rb') as wf:
                stream = self.p.open(format=self.p.get_format_from_width(wf.getsampwidth()), channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
                data = wf.readframes(1024)
                while data:
                    stream.write(data)
                    data = wf.readframes(1024)
        except Exception as e:
            log.error(f"Error during TTS playback: {e}", exc_info=True)
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
            bus.sendMessage(TTS_FINISHED)