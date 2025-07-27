# core/tts.py - Text-to-Speech Engine

import os
import logging
import io
import wave
import pyaudio
import threading
from piper.voice import PiperVoice
from aist.core.audio import audio_manager # type: ignore
from aist.core.events import bus, TTS_SPEAK, TTS_STARTED, TTS_FINISHED
from aist.core.config_manager import config

log = logging.getLogger(__name__)

# --- Piper TTS Initialization ---
voice = None
model_path = None # Define in outer scope for error logging

try:
    model_path_config = config.get('models.tts.piper_voice_model')
    if not model_path_config:
        log.fatal("FATAL: Piper TTS model path is not configured in config.yaml (models.tts.piper_voice_model).")
    else:
        model_path = os.path.abspath(model_path_config)
        model_config_path = f"{model_path}.json"

        if not os.path.exists(model_path) or not os.path.exists(model_config_path):
            log.fatal(f"Piper voice model or config not found at '{model_path}'")
            log.fatal("Please download a voice from https://huggingface.co/rhasspy/piper-voices/tree/main")
            log.fatal("And place both the .onnx and .json files in the configured path.")
        else:
            log.info("Loading Piper TTS voice... This may take a moment.")
            voice = PiperVoice.load(model_path, config_path=model_config_path)
            log.info("Piper TTS voice loaded successfully.")
except Exception as e:
    log.error(f"Error initializing Piper TTS engine for model '{model_path}': {e}", exc_info=True)

def _speak_audio(text: str):
    """
    The core implementation of converting text to speech and playing it.
    """
    if not voice:
        log.error("TTS engine not available. Cannot play audio.")
        return
    if text:
        log.info(f"AIST Speaking: \"{text}\"")
        p = audio_manager.get_pyaudio()
        if not p:
            log.error("PyAudio instance not available. Cannot play audio.")
            return

        stream = None
        try:
            # Signal that TTS is starting, so other components (like STT) can pause.
            bus.sendMessage(TTS_STARTED)

            # Create an in-memory buffer to hold the WAV data.
            wav_buffer = io.BytesIO()

            # The piper library expects a wave writer object that it can configure.
            # We create a wave writer that writes to our in-memory buffer.
            with wave.open(wav_buffer, "wb") as wav_file_writer:
                # The piper library will set the WAV parameters (channels, sample rate, etc.)
                # on the wav_file_writer object during synthesis.
                voice.synthesize_wav(text, wav_file=wav_file_writer)

            # After the 'with' block, the buffer is written and the wave file is closed.
            # Now, rewind the buffer to the beginning so we can read from it for playback.
            wav_buffer.seek(0)

            # Use the wave module to read the in-memory WAV data
            with wave.open(wav_buffer, 'rb') as wf:
                # Open a PyAudio stream with the correct format from the WAV file
                stream = p.open(
                    format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                # Read data in chunks and stream it to the speakers
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)
        except Exception as e:
            log.error(f"Error during TTS playback: {e}", exc_info=True)
        finally:
            # Always ensure the stream is closed.
            # We DO NOT terminate the PyAudio instance because it is shared.
            if stream:
                stream.stop_stream()
                stream.close()
            
            # Signal that TTS has finished.
            bus.sendMessage(TTS_FINISHED)

def _handle_speak_request(text: str):
    """
    Handles a speak request from the event bus.
    Runs the actual speaking in a separate thread to avoid blocking the bus.
    """
    if not text:
        return
    threading.Thread(target=_speak_audio, args=(text,), daemon=True).start()

def initialize_tts_listener():
    """Subscribes the TTS engine to the event bus."""
    bus.subscribe(_handle_speak_request, TTS_SPEAK)
    log.info("TTS engine is listening for 'tts.speak' events.")