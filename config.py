# AIST.io Configuration File

# --- AI Model Configuration ---
# IMPORTANT: Update this path to the exact name of the model file you downloaded.
MODEL_PATH = "mistral-7b-instruct-v0.2.Q4_K_M.gguf"
GPU_LAYERS = 99 # Offload all possible layers to the GPU.
CONTEXT_LENGTH = 4096

# --- Assistant Configuration ---
WAKE_WORD = "hey assistant"
ASSISTANT_NAME = "AIST"