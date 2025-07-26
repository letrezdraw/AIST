# AIST.io Configuration File

# --- AI Model Configuration ---
# Models are expected to be in the 'data/models/' directory.
MODEL_PATH = "data/models/llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
GPU_LAYERS = 99 # Offload all possible layers to the GPU.
CONTEXT_LENGTH = 4096
MAX_NEW_TOKENS = 150 # Max tokens for the LLM to generate. Keeps answers concise.

# --- Assistant Configuration ---
ASSISTANT_NAME = "AIST"
# Phrases to wake the assistant up and start listening for commands
# The phrases below are no longer used for hardcoded checks, but serve as examples for the LLM.
ACTIVATION_PHRASES = ["hey assist", "assist start", "okay assist", "ok assist", "hey"]
# Phrase to stop listening for commands and go back to sleep
DEACTIVATION_PHRASES = ["assist pause"]
# Phrase to exit the application completely
EXIT_PHRASES = ["assist exit"]

# --- TTS Configuration ---
# Path to the Piper voice model .onnx file, relative to the project root.
PIPER_VOICE_MODEL = "data/models/tts/en_US-lessac-medium.onnx"

# --- STT Configuration ---
# Path to the Vosk model directory, relative to the project root.
VOSK_MODEL_PATH = "data/models/stt/vosk-model-en-us-0.22"