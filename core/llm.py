# core/llm.py - Large Language Model Interaction

import logging
from ctransformers import AutoModelForCausalLM
from config import MODEL_PATH, GPU_LAYERS, CONTEXT_LENGTH, MAX_NEW_TOKENS

log = logging.getLogger(__name__)

def initialize_llm():
    """Loads the Local AI Model."""
    log.info("Loading AI model... This may take a few moments.")
    try:
        llm = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            model_type="mistral",
            gpu_layers=GPU_LAYERS,
            context_length=CONTEXT_LENGTH
        )
        log.info("AI Model loaded successfully.")
        return llm
    except Exception as e:
        log.fatal(f"FATAL: Could not load the AI model from path: {MODEL_PATH}")
        log.error(f"Error: {e}", exc_info=True)
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
        # The system prompt contains the full instruction. The user's command is the final piece of data.
        # We combine the history with the new instruction.
        prompt = f"{history_str}[INST] {system_prompt_override}\n\nUser's latest request: \"{command}\" [/INST]"
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
        max_tokens = MAX_NEW_TOKENS

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