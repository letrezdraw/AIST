# aist/skills/dispatcher.py
import logging
import json
from thefuzz import fuzz
import re
import multiprocessing
import queue
from aist.core.config_manager import config
from aist.core.ipc.protocol import STATE_DORMANT, STATE_LISTENING
from aist.skills import skill_loader
from aist.core.llm import process_with_llm, summarize_system_output
from aist.core.memory import retrieve_relevant_facts

log = logging.getLogger(__name__)

# --- Initialization ---
activation_phrases = config.get('assistant.activation_phrases', [])
exit_phrases = config.get('assistant.exit_phrases', [])
deactivation_phrases = config.get('assistant.deactivation_phrases', [])
fuzzy_match_threshold = config.get('assistant.fuzzy_match_threshold', 85)
skill_timeout = config.get('assistant.skill_timeout', 5)

def _is_fuzzy_match(text: str, phrases: list[str]) -> bool:
    """Checks if the text is a fuzzy match for any of the provided phrases."""
    if not text or not phrases:
        return False
    # We use partial_ratio to be more forgiving of extra words.
    # token_set_ratio is better for matching phrases with different word order.
    for phrase in phrases:
        similarity = fuzz.token_set_ratio(text.lower(), phrase.lower())
        if similarity >= fuzzy_match_threshold:
            log.info(f"Fuzzy match successful for '{text}' with '{phrase}' (Similarity: {similarity}%)")
            return True
    return False

def _find_fast_path_intent(command_text: str):
    """
    Checks if the command text is a fuzzy match for any registered intent phrases.
    This is the "fast path" that avoids using the LLM for simple, known commands.
    """
    for intent_name, intent_data in skill_loader.skill_manager.intents.items():
        if _is_fuzzy_match(command_text, intent_data.get("phrases", [])):
            log.info(f"Fast-path intent match found: '{intent_name}'")
            return intent_name, intent_data
    return None, None

def _skill_process_wrapper(skill_id, handler_name, params, result_queue):
    """
    This function runs in a separate process to execute a skill handler.
    It isolates the skill from the main backend process and captures exceptions.
    """
    # Re-setup logging for this process to ensure errors are captured.
    from aist.core.log_setup import setup_logging
    import importlib
    import logging
    setup_logging() # Ensure logging is set up first
    log = logging.getLogger(__name__)
    log.info(f"Skill process wrapper started for skill: {skill_id}") # Added log

    try:
        log.info(f"Attempting to load skill module: {skill_id}") # Added log
        # We need to re-import and create the skill in the new process
        module_path = f"aist.skills.{skill_id}"
        skill_module = importlib.import_module(module_path)
        
        if not hasattr(skill_module, 'create_skill'):
            raise RuntimeError(f"Skill '{skill_id}' has no create_skill() function.")

        skill_instance = skill_module.create_skill()
        skill_instance._register(skill_id) # Properly initialize the skill with its ID
        handler = getattr(skill_instance, handler_name)
        log.info(f"Executing handler {handler_name} for skill {skill_id}") # Added log
        
        result = handler(params)
        result_queue.put({"status": "success", "output": result})
        log.info(f"Skill {skill_id} handler {handler_name} completed successfully.") # Added log
    except Exception as e:
        # Log the full error in the child process for debugging
        log.error(f"Skill '{skill_id}' crashed in isolated process.", exc_info=True)
        result_queue.put({"status": "error", "output": str(e)})

def _execute_skill(intent_name: str, intent_data: dict, params: dict, llm, original_command: str):
    """
    Executes a skill's intent handler in a sandboxed process
    with a timeout and returns a response dictionary.
    """
    skill_id = intent_data.get("skill_id")
    handler = intent_data.get("handler")
    response_intent = {"name": intent_name, "params": params}
    
    if not all([skill_id, handler]):
        log.error(f"Could not execute skill. Invalid intent data: {intent_data}")
        return {"action": "COMMAND", "speak": "I had a problem running that command.", "intent": response_intent}
    
    result_queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_skill_process_wrapper,
        args=(skill_id, handler.__name__, params, result_queue),
        daemon=False # Child process should not outlive parent
    )
    
    log.info(f"Executing skill '{skill_id}' in a sandboxed process.")
    process.start()
    process.join(timeout=skill_timeout)

    if process.is_alive():
        log.warning(f"Skill '{skill_id}' timed out after {skill_timeout} seconds. Terminating.")
        process.terminate()
        process.join() # Clean up the terminated process
        return {"action": "COMMAND", "speak": f"The {skill_id} skill took too long to respond.", "intent": response_intent}

    try:
        result = result_queue.get_nowait()
        status = result.get("status")
        output = result.get("output")

        if status == "error":
            log.error(f"Skill '{skill_id}' executed with an error: {output}")
            return {"action": "COMMAND", "speak": f"I encountered an error with the {skill_id} skill.", "intent": response_intent}
        
        # Success case
        log.info(f"Skill '{skill_id}' executed successfully.")
        if isinstance(output, str) and len(output) > 100:
            speak_text = summarize_system_output(llm, original_command, output)
        else:
            speak_text = str(output)

        return {"action": "COMMAND", "speak": speak_text, "intent": response_intent}

    except queue.Empty:
        log.error(f"Skill '{skill_id}' terminated unexpectedly without a result (crash). Exit code: {process.exitcode}")
        return {"action": "COMMAND", "speak": f"The {skill_id} skill crashed.", "intent": response_intent}
    except Exception as e:
        log.error(f"An unexpected error occurred while running skill '{skill_id}': {e}", exc_info=True)
        return {"action": "COMMAND", "speak": f"I had a problem running the {skill_id} skill.", "intent": response_intent}

def _get_llm_decision(command_text: str, llm, conversation_history: list):
    """Asks the LLM to decide which skill to use by returning a JSON object."""
    # Build a list of dictionaries representing the available functions.
    # This is safer than manual string formatting as it handles escaping automatically.
    prompt_functions_data = []
    for name, data in skill_loader.skill_manager.intents.items():
        skill_id = data['skill_id']
        skill_info = skill_loader.skill_manager.skills.get(skill_id, {})
        prompt_functions_data.append({
            "name": name,
            "description": skill_info.get('manifest', {}).get('description', 'No description available.'),
            "parameters": [
                {"name": p["name"], "description": p["description"]} for p in data.get('parameters', [])
            ]
        })
    
    # Add the default chat function
    prompt_functions_data.append({
        "name": "chat",
        "description": "Use for general conversation, questions, or when no other function matches.",
        "parameters": [{"name": "user_query", "description": "The user's original, un-edited query."}]
    })
    # Convert the list of dictionaries to a nicely formatted JSON string for the prompt
    functions_json_string = json.dumps(prompt_functions_data, indent=2)

    system_prompt = f"""You are an expert command router. Your job is to determine the user's intent and map it to one of the available functions by generating a JSON object.
Respond with a single, valid JSON object and nothing else.

Here are the available functions in JSON format:
{functions_json_string}

Example of how to respond:
User's command: "what is the current time?"
Your JSON response: {{"function": "get_current_time", "parameters": {{}}}}

Now, process the following command.
IMPORTANT: If the user is making a statement or asking a general question that does not map to a function, you MUST use the 'chat' function.
Do NOT call a function unless the user's intent is explicit.
Based on the user's command, choose the single best function to call.
Your response must be a single JSON object containing the function's name and a dictionary of any extracted parameters.
Your JSON response:"""
    response_text = process_with_llm(llm, command_text, conversation_history, [], system_prompt_override=system_prompt)
    try:
        # Use a regex to find the first JSON object in the response. This is more
        # robust than string stripping, as it handles markdown and other text.
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON object found in LLM response", response_text, 0)
        decision = json.loads(json_match.group(0))
        return decision
    except (json.JSONDecodeError, TypeError):
        log.warning(f"LLM did not return valid JSON for skill selection. Output: '{response_text}'")
        # Fallback to chat if the LLM fails to produce valid JSON
        return {"function": "chat", "parameters": {"user_query": command_text}}

def command_dispatcher(command_text: str, state: str, llm, conversation_history: list):
    """
    The main dispatcher for routing user commands based on state and intent.
    """
    # --- Universal Commands (checked in any state) ---
    if _is_fuzzy_match(command_text, exit_phrases):
        return {"action": "EXIT", "speak": "Goodbye."}

    # --- State-Specific Logic ---
    if state == STATE_DORMANT:
        if _is_fuzzy_match(command_text, activation_phrases):
            return {"action": "ACTIVATE", "speak": "Listening."}
        else:
            # In dormant state, we ignore anything that isn't an activation or exit phrase.
            return None
    
    elif state == STATE_LISTENING:
        if _is_fuzzy_match(command_text, deactivation_phrases):
            return {"action": "DEACTIVATE", "speak": "Okay."}

        # --- Skill / Chat Logic ---
        # 1. Try the fast path first for simple, registered commands.
        fast_path_intent_name, fast_path_intent_data = _find_fast_path_intent(command_text)
        if fast_path_intent_data:
            return _execute_skill(fast_path_intent_name, fast_path_intent_data, {}, llm, command_text)
        
        # --- Special Case: Summarization ---
        # This is a core function that needs access to the conversation and LLM,
        # so we handle it here instead of in a sandboxed skill process.
        summarize_phrases = ["summarize this conversation", "what have we talked about", "give me a summary"]
        if _is_fuzzy_match(command_text, summarize_phrases):
            log.info("Handling special case: summarize_conversation")
            if not conversation_history:
                return {"action": "COMMAND", "speak": "There's nothing to summarize yet."}
            conversation_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
            prompt = f"Summarize the following conversation and extract any key facts to be stored in long-term memory:\n{conversation_text}"
            summary = process_with_llm(llm, prompt, conversation_history, [])
            store_fact(f"The user and I had a conversation, which was summarized as: {summary}", source="summarize_conversation")
            return {"action": "COMMAND", "speak": "Okay, I've summarized our conversation and stored the key points in my long-term memory.", "intent": {"name": "summarize_conversation", "params": {}}}

        # 2. If no fast path, use the LLM for complex routing.
        log.info("No fast-path match. Consulting LLM for intent...")
        decision = _get_llm_decision(command_text, llm, conversation_history)
        intent_name = decision.get("function")
        params = decision.get("parameters", {})

        if intent_name == "chat":
            relevant_facts = retrieve_relevant_facts(command_text)
            chat_response = process_with_llm(llm, command_text, conversation_history, relevant_facts)
            return {"action": "COMMAND", "speak": chat_response, "intent": {"name": "chat", "params": {"user_query": command_text}}}
        
        # 3. Execute the skill chosen by the LLM.
        chosen_intent = skill_loader.skill_manager.intents.get(intent_name)
        if chosen_intent:
            return _execute_skill(intent_name, chosen_intent, params, llm, command_text)
        
    

        # 4. Fallback if the LLM hallucinates a function name.
        log.warning(f"LLM chose a non-existent function: '{intent_name}'. Falling back to chat.")
        relevant_facts = retrieve_relevant_facts(command_text)
        chat_response = process_with_llm(llm, command_text, conversation_history, relevant_facts)
        return {"action": "COMMAND", "speak": chat_response, "intent": {"name": "chat", "params": {"user_query": command_text}}}

    return None # Default case, should not be reached