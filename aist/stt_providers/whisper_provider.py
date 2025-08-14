# aist/stt_providers/whisper_provider.py
import logging
import torch
import whisper
import pyaudio
import numpy as np
import threading
import time
from queue import Queue, Empty

from aist.core.audio import audio_manager
from aist.core.events import bus, STT_TRANSCRIBED, TTS_STARTED, TTS_FINISHED, VAD_STATUS_CHANGED
from aist.core.config_manager import config
from .base import BaseSTTProvider

log = logging.getLogger(__name__)

class WhisperProvider(BaseSTTProvider):
    """
    The Whisper STT engine provider. It uses a more advanced VAD (Voice Activity Detection)
    approach to handle non-streaming transcription.
    """

    def __init__(self, app_state, stt_ready_event):
        super().__init__(app_state, stt_ready_event)
        self.model = self._load_model()
        self.audio_queue = Queue()

    def _load_model(self):
        """Loads the Whisper model based on configuration."""
        model_name = config.get('models.stt.whisper_model_name', 'tiny.en')
        device = config.get('models.stt.whisper_device', 'cpu')
        log.info(f"Checking for CUDA availability... torch.cuda.is_available() = {torch.cuda.is_available()}")
        if device == "cuda" and not torch.cuda.is_available():
            log.warning("CUDA device specified but not available. Falling back to CPU.")
            device = "cpu"
        
        log.info(f"Loading Whisper model '{model_name}' on device '{device}'... This may take a moment.")
        try:
            model = whisper.load_model(model_name, device=device)
            log.info("Whisper model loaded successfully.")
            return model
        except Exception as e:
            log.fatal(f"Failed to load Whisper model '{model_name}': {e}", exc_info=True)
            return None

    def _transcription_worker(self):
        """
        Continuously pulls audio data from the queue and transcribes it.
        This runs in a background thread.
        """
        while self.app_state.is_running:
            try:
                # Wait for audio data to become available. The timeout prevents
                # this loop from blocking indefinitely when the app is shutting down.
                audio_data = self.audio_queue.get(timeout=1)
                
                # Convert the raw bytes to a NumPy array that Whisper can process.
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Transcribe the audio.
                result = self.model.transcribe(audio_np, fp16=torch.cuda.is_available())
                text = result['text'].strip()
                
                # Filter out junk transcriptions that are common with silence.
                # We check if there is at least one alphabetic character.
                if text and any(c.isalpha() for c in text):
                    log.info(f"Whisper transcribed: '{text}'")
                    bus.sendMessage(STT_TRANSCRIBED, text=text)

            except Empty:
                # This is expected when there's no speech. Continue the loop silently.
                continue
            except Exception as e:
                log.error(f"Error in Whisper transcription worker: {e}", exc_info=True)

    def run(self):
        """The core loop that listens for voice activity and queues audio for transcription."""
        if not self.model:
            log.error("Whisper model not loaded. Cannot start listening loop.")
            return

        # Start the transcription worker thread
        worker_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        worker_thread.start()

        is_tts_active = False
        def _pause_listening():
            nonlocal is_tts_active
            is_tts_active = True
            log.debug("STT (Whisper) paused due to TTS activity.")

        def _resume_listening():
            nonlocal is_tts_active
            is_tts_active = False
            log.debug("STT (Whisper) resumed after TTS activity.")

        bus.subscribe(_pause_listening, TTS_STARTED)
        bus.subscribe(_resume_listening, TTS_FINISHED)
        
        # Signal that the STT provider is initialized and ready to receive events.
        self.stt_ready_event.set()

        p = audio_manager.get_pyaudio()
        if not p:
            log.error("PyAudio instance not available. Cannot start listening.")
            return

        # --- VAD Parameters ---
        RATE = 16000
        CHUNK = 1024
        PHRASE_TIMEOUT = config.get('audio.stt.whisper_vad.phrase_timeout', 1.0)
        ENERGY_THRESHOLD = config.get('audio.stt.whisper_vad.energy_threshold', 300)

        stream = None
        try:
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
            log.info("Microphone stream opened for Whisper.")

            phrase_buffer = []
            last_speech_time = time.time()

            last_vad_status = "silence"

            while self.app_state.is_running:
                if is_tts_active:
                    phrase_buffer.clear() # Clear any buffered audio
                    time.sleep(0.1)
                    continue

                data = stream.read(CHUNK, exception_on_overflow=False)
                if not data:
                    continue
                
                # Simple energy-based VAD
                # We use numpy for fast RMS calculation
                audio_chunk_np = np.frombuffer(data, dtype=np.int16)
                # Add a more robust check to ensure the audio chunk is not empty before processing.
                # This prevents a RuntimeWarning if the audio stream returns an empty chunk.
                if audio_chunk_np.size == 0:
                    continue
                
                try:
                    energy = np.sqrt(np.mean(audio_chunk_np.astype(np.float64)**2))
                except RuntimeWarning:
                    # This can happen with empty or invalid audio chunks. Assume silence.
                    energy = 0.0

                if energy > ENERGY_THRESHOLD:
                    # Broadcast that speech is detected, but only on change
                    if last_vad_status == "silence":
                        bus.sendMessage(VAD_STATUS_CHANGED, status="speech")
                        last_vad_status = "speech"

                    phrase_buffer.append(data)
                    last_speech_time = time.time()
                elif phrase_buffer:
                    # If we have buffered audio and we've been silent for a bit, transcribe.
                    if time.time() - last_speech_time > PHRASE_TIMEOUT:
                        audio_to_transcribe = b''.join(phrase_buffer)
                        phrase_buffer.clear()
                        self.audio_queue.put(audio_to_transcribe)
                
                # Broadcast that silence is detected, but only on change
                if energy <= ENERGY_THRESHOLD and last_vad_status == "speech":
                    bus.sendMessage(VAD_STATUS_CHANGED, status="silence")
                    last_vad_status = "silence"

        except Exception as e:
            log.error(f"An error occurred in the Whisper listening loop: {e}", exc_info=True)
        finally:
            if stream:
                stream.close()
            self.audio_queue.put(None) # Signal worker thread to exit
            worker_thread.join()
            bus.unsubscribe(_pause_listening, TTS_STARTED)
            bus.unsubscribe(_resume_listening, TTS_FINISHED)
            log.info("Whisper provider stopped.")