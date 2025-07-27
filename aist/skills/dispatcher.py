# aist/skills/dispatcher.py
import logging
import json
from thefuzz import fuzz
import re
from aist.core.config_manager import config
from aist.skills.skill_loader import discover_skills
from aist.core.llm import process_with_llm, summarize_system_output
from aist.core.memory import retrieve_relevant_facts

log = logging.getLogger(__name__)

# --- Initialization ---
# Load skills and configuration when the module is first imported.
available_skills, skills_prompt_fragment = discover_skills()
activation_phrases = config.get('assistant.activation_phrases', [])
exit_phrases = config.get('assistant.exit_phrases', [])
deactivation_phrases = config.get('assistant.deactivation_phrases', [])
fuzzy_match_threshold = config.get('assistant.fuzzy_match_threshold', 85)

def _is_fuzzy_match(text: str, phrases: list[str]) -> bool:
    """Checks if the text is a fuzzy match for any of the provided phrases."""
    if not text or not phrases:
        return False
    # We use partial_ratio to be more forgiving of extra words.
    # e.g., "hey assist can you..." will still match "hey assist".
    for phrase in phrases:
        similarity = fuzz.partial_ratio(text.lower(), phrase.lower())
        if similarity >= fuzzy_match_threshold:
            log.info(f"Fuzzy match successful for '{text}' with '{phrase}' (Similarity: {similarity}%)")
            return True
    return False

def _execute_skill(skill_name: str, params: dict, llm, original_command: str):
    """Executes a skill and returns a response dictionary."""
    if skill_name in available_skills:
        try:
            log.info(f"Executing skill '{skill_name}' with params: {params}")
            skill_func = available_skills[skill_name]
            output = skill_func(**params)
            
            # If the skill returns a long string, assume it's raw output that needs summarizing.
            if isinstance(output, str) and len(output) > 100:
                speak_text = summarize_system_output(llm, original_command, output)
            else:
                speak_text = str(output)

            return {"action": "COMMAND", "speak": speak_text}
        except Exception as e:
            log.error(f"Error executing skill '{skill_name}': {e}", exc_info=True)
            return {"action": "COMMAND", "speak": f"I encountered an error trying to run the {skill_name} skill."}
    else:
        return {"action": "COMMAND", "speak": f"I'm sorry, I thought I had a skill called {skill_name}, but I can't find it."}

def _get_llm_decision(command_text: str, llm):
    """Asks the LLM to decide which skill to use by returning a JSON object."""
    system_prompt = f"""
You are an expert command router. Your job is to determine the user's intent and map it to one of the available functions.
Respond with a single, valid JSON object and nothing else.

Available functions:
{skills_prompt_fragment}
- chat(user_query: str): Use for general conversation, questions, or when no other function matches.

User's command: "{command_text}"

Choose the best function and parameters to respond to the user's command.
Your JSON response should look like this: {{"function": "function_name", "parameters": {{"param1": "value1"}}}}
"""
    response_text = process_with_llm(llm, command_text, [], [], system_prompt_override=system_prompt)
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

def command_dispatcher(command_text: str, state: str, llm, conversation_history: list, relevant_facts: list):
    """
    The main dispatcher for routing user commands based on state and intent.
    """
    # --- Universal Commands (checked in any state) ---
    if _is_fuzzy_match(command_text, exit_phrases):
        return {"action": "EXIT", "speak": "Goodbye."}

    # --- State-Specific Logic ---
    if state == 'DORMANT':
        if _is_fuzzy_match(command_text, activation_phrases):
            return {"action": "ACTIVATE", "speak": "Listening."}
        else:
            # In dormant state, we ignore anything that isn't an activation or exit phrase.
            return None
    
    elif state == 'LISTENING':
        if _is_fuzzy_match(command_text, deactivation_phrases):
            return {"action": "DEACTIVATE", "speak": "Okay."}

        # --- Skill / Chat Logic ---
        decision = _get_llm_decision(command_text, llm)
        skill_name = decision.get("function")
        params = decision.get("parameters", {})

        if skill_name == "chat":
            facts = retrieve_relevant_facts(command_text)
            chat_response = process_with_llm(llm, command_text, conversation_history, facts)
            return {"action": "COMMAND", "speak": chat_response}
        else:
            return _execute_skill(skill_name, params, llm, command_text)

    return None # Default case, should not be reached