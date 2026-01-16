# aist/stt_providers/whisper_provider.py
import logging
import torch
import whisper
import numpy as np
import threading
import time
import os
from queue import Queue, Empty
import speech_recognition as sr
import noisereduce as nr
import soundfile as sf
import tempfile
from scipy.io.wavfile import write as write_wav

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
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone() # Initialize the Microphone once
        self.noise_profile = None
        self._calibrate_noise() # Calibrate noise on initialization

    def _calibrate_noise(self):
        """
        Calibrates the noise profile for noise reduction.
        This method will be called on initialization of the provider.
        """
        use_noise_cancellation = config.get('audio.stt.use_noise_cancellation', False)
        if not use_noise_cancellation:
            log.debug("Noise cancellation not enabled in config, skipping calibration.")
            return

        noise_profile_path = config.get('audio.stt.noise_profile_path', 'data/audio/noise_profile.wav')
        noise_calibration_duration = config.get('audio.stt.noise_calibration_duration', 2)

        # Ensure the directory for noise profile exists
        os.makedirs(os.path.dirname(noise_profile_path), exist_ok=True)

        if os.path.exists(noise_profile_path):
            log.info(f"Attempting to load existing noise profile from '{noise_profile_path}'")
            try:
                # Use soundfile to read to ensure compatibility with noisereduce
                data, rate = sf.read(noise_profile_path)
                # noisereduce expects float64, so ensure type
                self.noise_profile = data.astype(np.float64)
                log.info("Noise profile loaded successfully.")
                return
            except Exception as e:
                log.warning(f"Failed to load noise profile from '{noise_profile_path}': {e}. Recalibrating...")
                self.noise_profile = None # Reset if loading fails

        log.info(f"No noise profile found or failed to load. Calibrating noise for {noise_calibration_duration} seconds. Please be quiet.")
        try:
            with self.microphone as source:
                # Adjust for ambient noise for a brief moment before recording the profile
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                log.info("Recording ambient noise...")
                audio = self.recognizer.listen(source, duration=noise_calibration_duration, timeout=noise_calibration_duration + 1)
            
            # Convert audio data to numpy array for noisereduce
            # speech_recognition AudioData object needs to be converted to numpy array
            audio_data_np = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
            
            # Save the captured noise to the specified path
            write_wav(noise_profile_path, audio.sample_rate, audio_data_np)

            # Load with soundfile for noisereduce compatibility
            data, rate = sf.read(noise_profile_path)
            self.noise_profile = data.astype(np.float64) # noisereduce expects float64

            log.info(f"Noise profile created and saved to {noise_profile_path}")

        except sr.WaitTimeoutError:
            log.warning("No ambient noise detected during calibration within the timeout. Noise profile may not be accurate.")
            self.noise_profile = None
        except Exception as e:
            log.error(f"Error during noise calibration: {e}", exc_info=True)
            self.noise_profile = None

    def _load_model(self):
        """Loads the Whisper model based on configuration."""
        model_name = config.get('models.stt.whisper_model_name', 'tiny.en')
        device = config.get('models.stt.whisper_device', 'cpu')
        
        # Set custom cache directory for Whisper models
        cache_dir = "data/models/stt"
        os.makedirs(cache_dir, exist_ok=True)
        # Set WHISPER_MODEL_DIR to manage cache location explicitly
        os.environ['WHISPER_MODEL_DIR'] = os.path.abspath(cache_dir)
        
        log.info(f"Checking for CUDA availability... torch.cuda.is_available() = {torch.cuda.is_available()}")
        if device == "cuda" and not torch.cuda.is_available():
            log.warning("CUDA device specified but not available. Falling back to CPU.")
            device = "cpu"
        
        log.info(f"Loading Whisper model '{model_name}' on device '{device}'... This may take a moment.")
        log.info(f"Model cache directory: {os.environ['WHISPER_MODEL_DIR']}")
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

                # Check if we received a shutdown signal (None)
                if audio_data is None:
                    log.debug("Transcription worker received shutdown signal.")
                    break

                # audio_data is now a numpy array of float32s
                audio_np = audio_data

                # Transcribe the audio.
                result = self.model.transcribe(audio_np, fp16=torch.cuda.is_available(), language=config.get('audio.stt.language', 'en'))
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

        # Configure recognizer with settings from config.yaml
        use_dynamic_energy = config.get('audio.stt.use_dynamic_energy', False)
        energy_threshold = config.get('audio.stt.whisper_vad.energy_threshold', None) # Can be None for dynamic
        self.recognizer.pause_threshold = config.get('audio.stt.pause_threshold', 0.8)
        phrase_time_limit = config.get('audio.stt.whisper_vad.phrase_timeout', 1.0) # Used for sr.listen
        listen_timeout = config.get('audio.stt.listen_timeout', 1.6)

        last_vad_status = "silence"

        try:
            with self.microphone as source:
                # Adjust for ambient noise if dynamic energy is enabled
                if use_dynamic_energy:
                    log.info("Adjusting for ambient noise...")
                    self.recognizer.adjust_for_ambient_noise(source)
                    log.info(f"Set energy threshold to {self.recognizer.energy_threshold} (dynamically adjusted).")
                elif energy_threshold is not None:
                    self.recognizer.energy_threshold = energy_threshold
                    log.info(f"Using manual energy threshold: {self.recognizer.energy_threshold}.")
                else:
                    log.info("Using default SpeechRecognition energy threshold (no dynamic adjustment or manual override).")

                log.info(f"Whisper STT listening with pause_threshold={self.recognizer.pause_threshold}, phrase_time_limit={phrase_time_limit}, listen_timeout={listen_timeout}")

                while self.app_state.is_running:
                    if is_tts_active:
                        # If TTS is active, don't listen to avoid self-transcription
                        time.sleep(0.1)
                        continue

                    try:
                        # Use listen() with phrase_time_limit and timeout
                        # The timeout argument in listen() specifies how long to wait for a phrase to start.
                        # If nothing is said, it returns sr.WaitTimeoutError.
                        # phrase_time_limit specifies the maximum duration of a phrase.
                        log.debug("Listening for speech...")
                        audio = self.recognizer.listen(
                            source, 
                            phrase_time_limit=phrase_time_limit,
                            timeout=listen_timeout # How long to wait for a phrase to start
                        )
                        
                        # If we get here, speech was detected and captured.
                        # Broadcast VAD status change if it was previously silent.
                        if last_vad_status == "silence":
                            bus.sendMessage(VAD_STATUS_CHANGED, status="speech")
                            last_vad_status = "speech"
                        
                        log.debug("Speech detected, processing audio...")
                        
                        # Convert AudioData to NumPy array for processing
                        audio_data_np = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                        sample_rate = audio.sample_rate

                        # Apply noise reduction if enabled and profile exists
                        use_noise_cancellation = config.get('audio.stt.use_noise_cancellation', False)
                        if use_noise_cancellation and self.noise_profile is not None:
                            log.debug("Applying noise reduction...")
                            # noisereduce expects float64, so convert
                            audio_data_float = audio_data_np.astype(np.float64) / 32768.0
                            
                            # Ensure the noise profile matches the sample rate if necessary
                            # For simplicity, assuming sample rates match after calibration.
                            reduced_noise_audio = nr.reduce_noise(y=audio_data_float, sr=sample_rate, y_noise=self.noise_profile, prop_decrease=1.0)
                            
                            # Convert back to float32 for Whisper (expected by model.transcribe)
                            processed_audio = (reduced_noise_audio * 32768.0).astype(np.float32) / 32768.0
                            log.debug("Noise reduction applied.")
                        else:
                            processed_audio = audio_data_np.astype(np.float32) / 32768.0
                            if use_noise_cancellation and self.noise_profile is None:
                                log.warning("Noise cancellation enabled but no profile available. Skipping noise reduction.")

                        self.audio_queue.put(processed_audio) # Queue the processed audio for transcription

                    except sr.UnknownValueError:
                        log.debug("SpeechRecognition could not understand audio (too quiet, garbled, etc.).")
                        # If it was previously speech, now it's effectively silence
                        if last_vad_status == "speech":
                            bus.sendMessage(VAD_STATUS_CHANGED, status="silence")
                            last_vad_status = "silence"
                    except sr.WaitTimeoutError:
                        log.debug("No speech detected within timeout period.")
                        # If it was previously speech, now it's effectively silence
                        if last_vad_status == "speech":
                            bus.sendMessage(VAD_STATUS_CHANGED, status="silence")
                            last_vad_status = "silence"
                    except Exception as e:
                        log.error(f"An error occurred during audio capture: {e}", exc_info=True)
                        # Ensure VAD status reflects potential silence after an error
                        if last_vad_status == "speech":
                            bus.sendMessage(VAD_STATUS_CHANGED, status="silence")
                            last_vad_status = "silence"

        except Exception as e:
            log.error(f"An unrecoverable error occurred in the Whisper listening loop: {e}", exc_info=True)
        finally:
            self.audio_queue.put(None) # Signal worker thread to exit
            worker_thread.join()
            bus.unsubscribe(_pause_listening, TTS_STARTED)
            bus.unsubscribe(_resume_listening, TTS_FINISHED)
            log.info("Whisper provider stopped.")