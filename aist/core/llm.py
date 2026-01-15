# core/llm.py - Large Language Model Interaction

import logging
import os
from ctransformers import AutoModelForCausalLM
from huggingface_hub.errors import RepositoryNotFoundError
from aist.core.config_manager import config
from aist.core.ipc.protocol import INIT_STATUS_UPDATE

log = logging.getLogger(__name__)

def initialize_llm(event_broadcaster):
    """Loads the Local AI Model."""
    log.info("Loading local AI model. This can take several minutes on the first run...")
    model_path = config.get('models.llm.path')
    if not model_path:
        log.fatal("FATAL: LLM model path is not configured in config.yaml (models.llm.path).")
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": "LLM model path not configured."})
        return None

    # Check if the path is a local file and if it exists
    if os.path.exists(model_path):
        log.info(f"Found local model at: {model_path}")
    elif not any(s in model_path for s in ['/', '\\']):
        log.info(f"'{model_path}' is not a local path. Assuming it's a Hugging Face repo and attempting to download.")
    else:
        log.fatal(f"FATAL: The specified LLM model file does not exist at the path: {model_path}")
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": f"Model file not found at {model_path}"})
        return None

    try:
        llm = AutoModelForCausalLM.from_pretrained(
            model_path,
            model_type="mistral",
            gpu_layers=config.get('models.llm.gpu_layers', 0),
            context_length=config.get('models.llm.context_length', 2048)
        )
        log.info("AI Model loaded successfully.")
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "initialized"})
        return llm
    except ValueError as e:
        if "Model path" in str(e) and "doesn't exist" in str(e):
            log.fatal(f"FATAL: The model path '{model_path}' does not seem to exist, either locally or on Hugging Face.")
            log.error(f"Please check that the path in your config.yaml is correct.", exc_info=True)
            event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": f"Model path '{model_path}' not found."})
        else:
            log.fatal(f"FATAL: A ValueError occurred while loading the model: {e}")
            event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": str(e)})
        return None
    except RepositoryNotFoundError as e:
        log.fatal(f"FATAL: The Hugging Face repository '{model_path}' could not be found.")
        log.error("Please ensure the repository ID is correct and that you have an internet connection.", exc_info=True)
        log.error("If it's a private repository, make sure you are authenticated with 'huggingface-cli login'.")
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": f"Hugging Face repo '{model_path}' not found."})
        return None
    except FileNotFoundError as e:
        if 'ctransformers.dll' in str(e) and config.get('models.llm.gpu_layers', 0) > 0:
            log.fatal("FATAL: Could not find the ctransformers CUDA library.")
            log.error("This usually means the NVIDIA CUDA Toolkit is not installed or not in the system's PATH.")
            log.error("You can either install the CUDA toolkit or set 'gpu_layers: 0' in your config.yaml to run on CPU.", exc_info=True)
            event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": "ctransformers CUDA library not found."})
        else:
            log.fatal(f"FATAL: A FileNotFoundError occurred: {e}", exc_info=True)
            event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": str(e)})
        return None
    except Exception as e:
        log.fatal(f"FATAL: An unexpected error occurred while loading the AI model from path: {model_path}")
        log.error(f"Error: {e}", exc_info=True)
        event_broadcaster.broadcast(INIT_STATUS_UPDATE, {"component": "llm", "status": "failed", "error": str(e)})
        return None

def _format_history(history: list[tuple[str, str]]) -> str:
    """Formats the conversation history for the LLM prompt."""
    if not history:
        return ""
    # Format for Mistral Instruct model
    formatted = "<s>"
    for role, content in history:
        if role == 'user':
            formatted += f"[INST] {content} [/INST]"
        else:
            formatted += f"{content}</s>"
    return formatted

def process_with_llm(llm, command, conversation_history, relevant_facts, system_prompt_override=None):
    """
    Sends a prompt to the LLM and gets a response.
    Can be used for general conversation or for structured tasks via a system_prompt_override.
    """
    if not command and not system_prompt_override:
        return ""

    history_str = _format_history(conversation_history)

    # If a system prompt override is provided, it takes precedence.
    # This is used for structured tasks like skill selection.
    if system_prompt_override:
        # The system prompt contains the full instruction, including the user's command.
        prompt = f"{history_str}[INST] {system_prompt_override} [/INST]"
        # For skill selection, we want a deterministic, low-creativity response.
        temperature = 0.0
        max_tokens = 256 # Should be enough for a JSON object
    else:
        # This is for regular, conversational chat.
        facts_str = ""
        if relevant_facts:
            facts_str = "You have the following relevant information from your memory to help you answer:\n- " + "\n- ".join(relevant_facts) + "\n"
        prompt = f'{history_str}[INST] {facts_str}Based on the conversation history and the provided information, answer the following user query. Be concise and direct. User query: {command} [/INST]'
        temperature = 0.7 # Standard temperature for creative/conversational responses
        max_tokens = config.get('models.llm.max_new_tokens', 150)

    try:
        log.info("Sending prompt to LLM...")
        return llm(prompt, stream=False, max_new_tokens=max_tokens, temperature=temperature)
    except Exception as e:
        log.error(f"Error during LLM processing: {e}", exc_info=True)
        return "I encountered an error while thinking."

def summarize_system_output(llm, original_user_command, system_output):
    """Asks the LLM to summarize raw system command output in a natural way."""
    if not system_output:
        return "The command produced no output to summarize."

    prompt = f'''
You are an AI assistant. Your job is to interpret raw command-line output and explain it to a non-technical user in a clear, concise, and friendly way.

The user originally asked: "{original_user_command}"
The following system output was generated to answer their question:
--- SYSTEM OUTPUT ---
{system_output}
--- END SYSTEM OUTPUT ---

Now, summarize this output and answer the user's original question naturally. Do not mention that you ran a command.
'''
    log.info("Summarizing system output...")
    return process_with_llm(llm, prompt, [], []) # Process without history or facts for a clean summary
