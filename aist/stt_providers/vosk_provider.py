# aist/stt_providers/vosk_provider.py
import logging
import json
import os
import pyaudio
import vosk
import numpy as np
import time

from aist.core.audio import audio_manager
from aist.core.events import bus, STT_TRANSCRIBED, TTS_STARTED, TTS_FINISHED, STATE_CHANGED, VAD_STATUS_CHANGED
from aist.core.config_manager import config
from .base import BaseSTTProvider

STATE_DORMANT = "DORMANT"
STATE_LISTENING = "LISTENING"

log = logging.getLogger(__name__)

# Suppress the noisy C++ logs from the Vosk library itself.
vosk.SetLogLevel(-1)

class VoskProvider(BaseSTTProvider):
    """The Vosk STT engine provider."""

    def __init__(self, app_state, stt_ready_event):
        super().__init__(app_state, stt_ready_event)
        self.vosk_model = None # Model will be loaded in the background `run` thread.

    def _load_model(self):
        """Loads the Vosk model from the path specified in the config."""
        try:
            vosk_model_path = config.get('models.stt.vosk_model_path')
            if not vosk_model_path:
                log.fatal("FATAL: Vosk model path is not configured in config.yaml (models.stt.vosk_model_path).")
                return None
            elif not os.path.exists(vosk_model_path):
                log.fatal(f"Vosk model not found at '{vosk_model_path}'")
                log.fatal("Please download a model from https://alphacephei.com/vosk/models")
                return None
            else:
                log.info(f"Loading Vosk model from '{vosk_model_path}'...")
                model = vosk.Model(vosk_model_path)
                log.info("Vosk model loaded successfully.")
                return model
        except Exception as e:
            log.error(f"Error initializing Vosk model: {e}", exc_info=True)
            return None

    def run(self):
        """The core loop that listens to the microphone and publishes transcribed text."""
        # Load the model here, in the background thread, so it doesn't block the UI.
        self.vosk_model = self._load_model()
        if not self.vosk_model:
            log.error("Vosk model failed to load. STT provider will not run.")
            return

        is_tts_active = False

        activation_phrases = config.get('assistant.activation_phrases', ['hey assist'])
        exit_phrases = config.get('assistant.exit_phrases', ['assist exit'])
        grammar = json.dumps(activation_phrases + exit_phrases, ensure_ascii=False)

        try:
            # Create a standard recognizer first.
            recognizer_dormant = vosk.KaldiRecognizer(self.vosk_model, 16000)
            # Then, apply the specific grammar. This is the correct way to use dynamic grammars
            # and avoids the "Runtime graphs are not supported" warning with some models.
            recognizer_dormant.SetGrammar(grammar)
            recognizer_dormant.SetWords(True)
            recognizer_listening = vosk.KaldiRecognizer(self.vosk_model, 16000)
            recognizer_listening.SetWords(True)
            log.info("Vosk recognizers (Dormant and Listening) created successfully.")
        except Exception as e:
            log.error(f"Failed to create KaldiRecognizers: {e}", exc_info=True)
            return

        current_recognizer = recognizer_dormant
        current_state = STATE_DORMANT

        p = audio_manager.get_pyaudio()
        if not p:
            log.error("PyAudio instance not available. Cannot start listening.")
            return

        def _pause_listening():
            nonlocal is_tts_active
            is_tts_active = True
            recognizer_dormant.Reset()
            recognizer_listening.Reset()
            log.debug("STT paused and recognizers reset due to TTS activity.")

        def _resume_listening():
            nonlocal is_tts_active
            is_tts_active = False
            log.debug("STT resumed after TTS activity.")

        def _handle_state_change(state: str):
            nonlocal current_recognizer, current_state
            current_state = state
            if state == STATE_LISTENING:
                current_recognizer = recognizer_listening
            elif state == STATE_DORMANT:
                current_recognizer = recognizer_dormant

        stream = None
        try:
            try:
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
            except OSError as e:
                log.fatal(f"FATAL: Could not open microphone stream: {e}")
                log.fatal("Please ensure you have a microphone connected and configured as the default input device.")
                return

            stream.start_stream()
            log.info("Microphone stream opened for Vosk.")

            bus.subscribe(_pause_listening, TTS_STARTED)
            bus.subscribe(_resume_listening, TTS_FINISHED)
            bus.subscribe(_handle_state_change, STATE_CHANGED)
            
            # Signal that the STT provider is initialized and ready to receive events.
            self.stt_ready_event.set()

            energy_threshold = config.get('audio.stt.energy_threshold', 300)
            last_vad_status = "silence"

            while self.app_state.is_running:
                data = stream.read(2048, exception_on_overflow=False)

                if is_tts_active:
                    continue

                if not data:
                    continue
                
                audio_chunk_np = np.frombuffer(data, dtype=np.int16)
                if audio_chunk_np.size == 0:
                    continue
                
                try:
                    energy = np.sqrt(np.mean(audio_chunk_np.astype(np.float64)**2))
                except RuntimeWarning:
                    energy = 0.0
                
                if energy > energy_threshold:
                    if last_vad_status == "silence":
                        bus.sendMessage(VAD_STATUS_CHANGED, status="speech")
                        last_vad_status = "speech"
                else:
                    if last_vad_status == "speech":
                        bus.sendMessage(VAD_STATUS_CHANGED, status="silence")
                        last_vad_status = "silence"
                    continue

                if current_recognizer.AcceptWaveform(data):
                    result_json = current_recognizer.Result()
                    result_dict = json.loads(result_json)

                    # Only perform a strict confidence check when actively listening for commands.
                    # For the DORMANT state, we allow lower-confidence results to pass through
                    # to the fuzzy matcher, which is better at handling wake-word variations.
                    words = result_dict.get('result', [])
                    if words and current_state == STATE_LISTENING:
                        total_confidence = sum(item['conf'] for item in words)
                        average_confidence = total_confidence / len(words)

                        confidence_threshold = config.get('audio.stt.confidence_threshold', 0.85)
                        if average_confidence < confidence_threshold:
                            log.warning(f"Low confidence transcription ignored (conf: {average_confidence:.2f}): '{result_dict.get('text', '')}'")
                            continue

                    transcribed_text = result_dict.get('text', '').strip().lower()
                    
                    if transcribed_text:
                        log.info(f"Heard with high confidence: '{transcribed_text}'")
                        bus.sendMessage(STT_TRANSCRIBED, text=transcribed_text)

        except Exception as e:
            log.error(f"An error occurred in the Vosk listening loop: {e}", exc_info=True)
        finally:
            if stream:
                stream.stop_stream()
                stream.close()
                log.info("Microphone stream closed.")
            
            bus.unsubscribe(_pause_listening, TTS_STARTED)
            bus.unsubscribe(_resume_listening, TTS_FINISHED)
            bus.unsubscribe(_handle_state_change, STATE_CHANGED)