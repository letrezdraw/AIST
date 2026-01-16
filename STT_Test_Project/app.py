import tkinter as tk
from tkinter import scrolledtext
import threading
import queue
import speech_recognition as sr
import whisper
import numpy as np
import tempfile
import os
import sys
from scipy.io.wavfile import write as write_wav
import logging
import json

# --- Setup Configuration and Logging ---
CONFIG_FILE = "config.json"
LOG_FILE = "app.log"

# Default configuration
default_config = {
    "whisper_model": "small",
    "language": "en",
    "clear_log_on_start": True,
    "ffmpeg_path": "ffmpeg.exe",
    "phrase_time_limit": 10,
    "energy_threshold": 275,
    "pause_threshold": 0.8,
    "listen_timeout": 1.6,
    "use_dynamic_energy": False
}

# Load config or create with defaults
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    # Add missing keys with default values
    for key, value in default_config.items():
        if key not in config:
            config[key] = value
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
except FileNotFoundError:
    config = default_config
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

# Clear log file on start based on config
if config.get("clear_log_on_start"):
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w"):
            pass

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logging.info("Application starting.")
logging.info(f"Loaded configuration: {config}")

# --- FFmpeg Path setup ---
ffmpeg_path = config.get("ffmpeg_path", "ffmpeg.exe")
# Add the project root to the PATH, as ffmpeg.exe is expected there.
project_root = os.getcwd()
os.environ["PATH"] = project_root + os.pathsep + os.environ["PATH"]
logging.info(f"Added '{project_root}' to PATH to locate '{ffmpeg_path}'.")

import noisereduce as nr
from scipy.io import wavfile
import soundfile as sf

# --- End Setup ---



class SpeechToTextApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech-to-Text Control")
        self.root.geometry("300x200")

        self.is_running = False
        self.recognizer = sr.Recognizer()
        
        self.config = config # Store config
        self.noise_profile = None
        
        logging.info(f"Loading Whisper model '{self.config.get('whisper_model', 'base')}'...")
        self.model = whisper.load_model(self.config.get('whisper_model', 'base'))  # Using the base model
        logging.info("Whisper model loaded.")

        self.status_label = tk.Label(self.root, text="Status: Idle", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.start_button = tk.Button(self.root, text="Start Listening", command=self.start_listening)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(self.root, text="Stop Listening", command=self.stop_listening, state=tk.DISABLED)
        self.stop_button.pack(pady=5)
        
        if self.config.get("use_noise_cancellation", False):
            self.calibrate_button = tk.Button(self.root, text="Calibrate Noise", command=self.calibrate_noise)
            self.calibrate_button.pack(pady=5)

        self.output_window = None
        self.output_text = None
        self.text_queue = queue.Queue()

        self.create_output_window()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_output_window(self):
        self.output_window = tk.Toplevel(self.root)
        self.output_window.title("Transcription Output")
        self.output_window.geometry("500x400")
        
        input_label = tk.Label(self.output_window, text="Input (Status)", font=("Arial", 10))
        input_label.pack(pady=(5,0))
        
        self.input_status_text = scrolledtext.ScrolledText(self.output_window, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.input_status_text.pack(padx=10, pady=(0,10), fill=tk.X)

        output_label = tk.Label(self.output_window, text="Output (Transcription)", font=("Arial", 10))
        output_label.pack(pady=(5,0))

        self.output_text = scrolledtext.ScrolledText(self.output_window, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(padx=10, pady=(0,10), expand=True, fill=tk.BOTH)

        self.output_window.protocol("WM_DELETE_WINDOW", self.on_closing)

    def update_text_display(self):
        while not self.text_queue.empty():
            message_type, text = self.text_queue.get()
            if message_type == "input":
                self.input_status_text.config(state=tk.NORMAL)
                self.input_status_text.delete('1.0', tk.END)
                self.input_status_text.insert(tk.END, text + "\n")
                self.input_status_text.config(state=tk.DISABLED)
                self.input_status_text.see(tk.END)
            elif message_type == "output":
                self.output_text.config(state=tk.NORMAL)
                self.output_text.insert(tk.END, text + "\n")
                self.output_text.config(state=tk.DISABLED)
                self.output_text.see(tk.END)
        self.root.after(100, self.update_text_display)

    def start_listening(self):
        logging.info("Start listening button clicked.")
        self.is_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        if self.config.get("use_noise_cancellation", False):
            self.calibrate_button.config(state=tk.DISABLED)
        self.status_label.config(text="Status: Listening")
        self.text_queue.put(("input", "Listening..."))

        self.listen_thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.listen_thread.start()
        self.root.after(100, self.update_text_display)


    def stop_listening(self):
        if self.is_running:
            logging.info("Stop listening button clicked.")
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            if self.config.get("use_noise_cancellation", False):
                self.calibrate_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Idle")
            self.text_queue.put(("input", "Stopped listening."))

    def calibrate_noise(self):
        logging.info("Noise calibration started.")
        self.text_queue.put(("input", "Calibrating noise... Please be quiet."))
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.calibrate_button.config(state=tk.DISABLED)
        
        calibration_duration = self.config.get("noise_calibration_duration", 2)
        
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                self.text_queue.put(("input", f"Recording ambient noise for {calibration_duration} seconds..."))
                audio = self.recognizer.listen(source, duration=calibration_duration)
            
            # Save the noise profile
            noise_profile_path = self.config.get("noise_profile_path", "noise_profile.wav")
            with open(noise_profile_path, "wb") as f:
                f.write(audio.get_wav_data())

            rate, data = wavfile.read(noise_profile_path)
            self.noise_profile = data.astype(np.float32)

            logging.info(f"Noise profile created and saved to {noise_profile_path}")
            self.text_queue.put(("input", "Noise calibration complete."))

        except Exception as e:
            logging.error(f"Error during noise calibration: {e}", exc_info=True)
            self.text_queue.put(("input", f"Error during calibration: {e}"))
        finally:
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.calibrate_button.config(state=tk.NORMAL)

    def listen_loop(self):
        try:
            with sr.Microphone() as source:
                if self.config.get("use_dynamic_energy", True):
                    self.recognizer.adjust_for_ambient_noise(source)
                    self.text_queue.put(("input", "Adjusted for ambient noise. Ready to listen."))
                    logging.info("Adjusted for ambient noise. Ready to listen.")
                
                if self.config.get("energy_threshold") is not None:
                    self.recognizer.energy_threshold = self.config.get("energy_threshold")
                    logging.info(f"Using manual energy threshold: {self.recognizer.energy_threshold}")
                
                self.recognizer.pause_threshold = self.config.get("pause_threshold", 0.8)

                while self.is_running:
                    try:
                        self.text_queue.put(("input", "Listening for a phrase..."))
                        logging.info("Listening for a phrase...")
                        audio = self.recognizer.listen(
                            source, 
                            phrase_time_limit=self.config.get("phrase_time_limit", 5),
                            timeout=self.config.get("listen_timeout", 3)
                        )
                        
                        self.text_queue.put(("input", "Processing audio..."))
                        logging.info("Processing audio...")
                        
                        audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                        
                        if self.config.get("use_noise_cancellation", False) and self.noise_profile is not None:
                            logging.info("Applying noise reduction...")
                            # Convert to float32 for noisereduce
                            audio_data_float = audio_data.astype(np.float32) / 32768.0
                            
                            # Perform noise reduction
                            reduced_noise_audio = nr.reduce_noise(y=audio_data_float, sr=audio.sample_rate, y_noise=self.noise_profile, prop_decrease=1.0)
                            
                            # Convert back to int16 for Whisper
                            audio_data = (reduced_noise_audio * 32768.0).astype(np.int16)
                            logging.info("Noise reduction applied.")
                        
                        audio_data = audio_data.astype(np.float32) / 32768.0

                        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                            tmp_file_name = tmp_file.name
                        
                        write_wav(tmp_file_name, audio.sample_rate, audio_data)
                        
                        language = self.config.get("language", "en")
                        result = self.model.transcribe(tmp_file_name, fp16=False, language=language, condition_on_previous_text=False)
                        text = result['text'].strip()
                        logging.info(f"Transcription result: '{text}'")

                        if text:
                            self.text_queue.put(("output", text))
                        
                        try:
                            os.remove(tmp_file_name)
                        except OSError as e:
                            logging.error(f"Error removing temporary file: {e}")

                    except sr.UnknownValueError:
                        logging.warning("Could not understand audio, listening again...")
                        self.text_queue.put(("input", "Could not understand audio, listening again..."))
                    except sr.WaitTimeoutError:
                        logging.info("Listening timeout, continuing to listen...")
                        continue # Nothing was said, just continue listening
                    except Exception as e:
                        logging.error("An error occurred during transcription", exc_info=True)
                        self.text_queue.put(("input", f"An error occurred: {e}"))

        except AttributeError as e:
            logging.critical(f"PyAudio not found or microphone not working: {e}", exc_info=True)
            self.text_queue.put(("input", "ERROR: Microphone not found. Is PyAudio installed?"))
            self.stop_listening()
        except Exception as e:
            logging.critical("An unrecoverable error occurred in the listen loop.", exc_info=True)
            self.text_queue.put(("input", f"A critical error occurred: {e}"))
            self.stop_listening()
                    
    def on_closing(self):
        logging.info("Application closing.")
        self.stop_listening()
        self.root.destroy()
        if self.output_window:
            try:
                self.output_window.destroy()
            except tk.TclError:
                pass # Can happen if root is already destroyed

if __name__ == "__main__":
    logging.info("Application starting.")
    root = tk.Tk()
    app = SpeechToTextApp(root)
    root.mainloop()
    logging.info("Application finished.")

