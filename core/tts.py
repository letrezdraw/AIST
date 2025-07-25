# core/tts.py - Text-to-Speech Engine

import os
import logging
import tempfile
import wave
import pyaudio
from piper.voice import PiperVoice
from config import PIPER_VOICE_MODEL

log = logging.getLogger(__name__)

# --- Piper TTS Initialization ---
voice = None

try:
    # Check if the model file and its .json config exist
    model_path = os.path.abspath(PIPER_VOICE_MODEL)
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
    log.error(f"Error initializing Piper TTS engine: {e}", exc_info=True)

def speak(text):
    """Converts text to speech using Piper and plays it."""
    if not voice:
        log.error("TTS engine not available. Cannot speak.")
        return
    if text:
        log.info(f"AIST Speaking: \"{text}\"")
        output_path = None # Define here to ensure it's in scope for finally
        # Use a temporary file to prevent race conditions
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav_file:
                output_path = tmp_wav_file.name
            
            # Synthesize speech to the temporary WAV file
            with wave.open(output_path, "wb") as wav_file:
                # Set the parameters for the WAV file based on the voice model's config.
                wav_file.setnchannels(1) # Piper voices are mono
                wav_file.setsampwidth(2) # 16-bit audio
                wav_file.setframerate(voice.config.sample_rate)
                voice.synthesize(text, wav_file)

            # --- PyAudio Playback Logic ---
            # Open the wave file for reading
            with wave.open(output_path, 'rb') as wf:
                p = pyaudio.PyAudio()
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True)
                # Read data in chunks and write to the stream
                data = wf.readframes(1024)
                while data:
                    stream.write(data)
                    data = wf.readframes(1024)
                # Stop and close the stream and PyAudio instance
                stream.stop_stream()
                stream.close()
                p.terminate()
        except Exception as e:
            log.error(f"Error during TTS playback: {e}", exc_info=True)
        finally:
            # Ensure the temporary audio file is always cleaned up
            if output_path and os.path.exists(output_path):
                os.remove(output_path)