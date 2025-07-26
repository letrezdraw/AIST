# AIST.io Configuration File

# --- AI Model Configuration ---
# IMPORTANT: Update this path to the exact name of the model file you downloaded.
MODEL_PATH = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
GPU_LAYERS = 99 # Offload all possible layers to the GPU.
CONTEXT_LENGTH = 4096
MAX_NEW_TOKENS = 150 # Max tokens for the LLM to generate. Keeps answers concise.

# --- Assistant Configuration ---
ASSISTANT_NAME = "AIST"
# Phrases to wake the assistant up and start listening for commands
ACTIVATION_PHRASES = ["hey assist", "assist start", "okay assist", "ok assist"]
# Phrase to stop listening for commands and go back to sleep
DEACTIVATION_PHRASES = ["assist pause"]
# Phrase to exit the application completely
EXIT_PHRASES = ["assist exit"]

# --- TTS Configuration ---
# Path to the Piper voice model .onnx file.
PIPER_VOICE_MODEL = "piper_voices/en_US-lessac-medium.onnx"

# --- STT Configuration ---
# Path to the Vosk model directory.
# Download from: https://alphacephei.com/vosk/models
VOSK_MODEL_PATH = "vosk_models/vosk-model-en-us-0.22"