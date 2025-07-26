# core/stt.py - Speech-to-Text Engine using Vosk

import logging
import json
import os
import pyaudio
from vosk import Model, KaldiRecognizer
from config import VOSK_MODEL_PATH, ACTIVATION_PHRASES, DEACTIVATION_PHRASES, EXIT_PHRASES

log = logging.getLogger(__name__)

# --- Vosk Initialization ---
vosk_model = None
try:
    if not os.path.exists(VOSK_MODEL_PATH):
        log.fatal(f"Vosk model not found at '{VOSK_MODEL_PATH}'")
        log.fatal("Please download a model from https://alphacephei.com/vosk/models")
    else:
        log.info(f"Loading Vosk model from '{VOSK_MODEL_PATH}'...")
        vosk_model = Model(VOSK_MODEL_PATH)
        log.info("Vosk model loaded successfully.")
except Exception as e:
    log.error(f"Error initializing Vosk model: {e}", exc_info=True)

def listen_generator(app_state):
    """
    A generator that continuously listens to the microphone and yields transcribed text.
    Handles microphone stream and Vosk recognition internally.
    Stops when app_state.is_running becomes False.
    """
    if not vosk_model:
        log.error("Vosk model not loaded. Cannot start listening.")
        return

    p = pyaudio.PyAudio()
    stream = None
    try:
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,
            input=True,
            frames_per_buffer=8192
        )
        stream.start_stream()
        log.info("Microphone stream opened for Vosk.")

        # Initialize the recognizer without a specific grammar to allow it
        # to recognize any spoken words, not just control phrases.
        recognizer = KaldiRecognizer(vosk_model, 16000)
        # Enable word-level confidence scores
        recognizer.SetWords(True)
        log.debug("Vosk recognizer initialized for general-purpose recognition with word confidence.")

        while app_state.is_running:
            data = stream.read(4096, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result_json = recognizer.Result()
                result_dict = json.loads(result_json)

                # --- Confidence Filtering ---
                # To improve accuracy and prevent acting on misheard speech,
                # we calculate the average confidence of the transcription.
                words = result_dict.get('result', [])
                if words:
                    total_confidence = sum(item['conf'] for item in words)
                    average_confidence = total_confidence / len(words)

                    if average_confidence < 0.85: # Confidence threshold (0.0 to 1.0)
                        log.warning(f"Low confidence transcription ignored (conf: {average_confidence:.2f}): '{result_dict.get('text', '')}'")
                        continue # Skip this result and listen again

                transcribed_text = result_dict.get('text', '').strip().lower()
                
                if transcribed_text:
                    log.info(f"Heard with high confidence: '{transcribed_text}'")
                    yield transcribed_text

    except Exception as e:
        log.error(f"An error occurred in the listening generator: {e}", exc_info=True)
    finally:
        if stream and stream.is_active():
            stream.stop_stream()
            stream.close()
            log.info("Microphone stream closed.")
        p.terminate()
        log.info("PyAudio terminated.")