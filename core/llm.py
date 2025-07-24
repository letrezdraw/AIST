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

def process_with_llm(llm, command, conversation_history, relevant_facts):
    """Sends the command to the LLM and gets a conversational response."""
    if not command:
        return ""
    history_str = _format_history(conversation_history)

    facts_str = ""
    if relevant_facts:
        facts_str = "You have the following relevant information from your memory to help you answer:\n- " + "\n- ".join(relevant_facts) + "\n"

    prompt = f'{history_str}[INST] {facts_str}Based on the conversation history and the provided information, answer the following user query: {command} [/INST]'
    try:
        print("Thinking...")
        return llm(prompt, stream=False, max_new_tokens=256)
    except Exception as e:
        print(f"Error during LLM processing: {e}")
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
    print("Summarizing system output...")
    return process_with_llm(llm, prompt, [], []) # Process without history or facts for a clean summary

def get_intent_from_llm(llm, command, conversation_history, relevant_facts):
    """
    Uses the LLM to determine the user's intent and extract parameters.
    Returns a dictionary with 'command' and 'parameters'.
    """
    history_str = _format_history(conversation_history)
    if history_str:
        history_str = f"Here is the recent conversation history:\n{history_str}\n"

    facts_str = ""
    if relevant_facts:
        facts_str = "Here is some relevant information from memory that might help determine the intent:\n- " + "\n- ".join(relevant_facts) + "\n"

    # This prompt is crucial. It constrains the LLM to act as a command parser.
    prompt = f'''
    {history_str}{facts_str}Analyze the user's LATEST command based on the history and any provided facts. Respond with a single, minified JSON object.
    If the user's request requires interacting with the file system (e.g., listing files, checking disk space) or running a system utility not covered by another skill, use the "execute_system_command". Formulate a standard Windows 'cmd.exe' command.
    The JSON object must have two keys: "command" and "parameters".
    The "command" can be one of the following: ["open_app", "close_app", "search_web", "get_time", "get_system_info", "learn_fact", "list_memories", "forget_fact", "execute_system_command", "chat"].
    The "parameters" is a dictionary of extracted values.

    User command: "open notepad for me"
    {{"command": "open_app", "parameters": {{"app_name": "notepad"}}}}

    User command: "what is the cpu usage"
    {{"command": "get_system_info", "parameters": {{"stat_type": "cpu"}}}}

    User command: "what is the meaning of life"
    {{"command": "chat", "parameters": {{"query": "what is the meaning of life"}}}}

    User command: "remember that my favorite color is blue"
    {{"command": "learn_fact", "parameters": {{"fact": "my favorite color is blue"}}}}

    User command: "what have you learned"
    {{"command": "list_memories", "parameters": {{}}}}

    User command: "forget what I told you about my favorite color"
    {{"command": "forget_fact", "parameters": {{"fact_query": "my favorite color"}}}}

    User command: "list the files in my documents folder"
    {{"command": "execute_system_command", "parameters": {{"shell_command": "dir %USERPROFILE%\\Documents"}}}}

    User command: "{command}"
    '''
    print("Determining intent...")
    response = llm(prompt, stream=False, max_new_tokens=128, temperature=0)
    return response