# core/llm.py - Large Language Model Interaction

from ctransformers import AutoModelForCausalLM
from config import MODEL_PATH, GPU_LAYERS, CONTEXT_LENGTH

def initialize_llm():
    """Loads the Local AI Model."""
    print("Loading AI model... This may take a few moments.")
    try:
        llm = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            model_type="mistral",
            gpu_layers=GPU_LAYERS,
            context_length=CONTEXT_LENGTH
        )
        print("AI Model loaded successfully.")
        return llm
    except Exception as e:
        print(f"FATAL: Could not load the AI model from path: {MODEL_PATH}")
        print(f"Error: {e}")
        return None

def process_with_llm(llm, command):
    """Sends the command to the LLM and gets a conversational response."""
    if not command:
        return ""
    prompt = f'You are a helpful AI assistant. A user has said the following: "{command}". Respond to the user concisely.'
    try:
        print("Thinking...")
        return llm(prompt, stream=False, max_new_tokens=256)
    except Exception as e:
        print(f"Error during LLM processing: {e}")
        return "I encountered an error while thinking."