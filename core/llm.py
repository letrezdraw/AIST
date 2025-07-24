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

def get_intent_from_llm(llm, command):
    """
    Uses the LLM to determine the user's intent and extract parameters.
    Returns a dictionary with 'command' and 'parameters'.
    """
    # This prompt is crucial. It constrains the LLM to act as a command parser.
    prompt = f'''
    Analyze the user's command and respond with a single, minified JSON object.
    The JSON object must have two keys: "command" and "parameters".
    The "command" can be one of the following: ["open_app", "close_app", "search_web", "get_time", "get_system_info", "chat"].
    The "parameters" is a dictionary of extracted values.

    User command: "open notepad for me"
    {{"command": "open_app", "parameters": {{"app_name": "notepad"}}}}

    User command: "what is the cpu usage"
    {{"command": "get_system_info", "parameters": {{"stat_type": "cpu"}}}}

    User command: "what is the meaning of life"
    {{"command": "chat", "parameters": {{"query": "what is the meaning of life"}}}}

    User command: "{command}"
    '''
    print("Determining intent...")
    response = llm(prompt, stream=False, max_new_tokens=128, temperature=0)
    return response