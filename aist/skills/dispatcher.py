import json
import inspect
import logging
from aist.core.llm import process_with_llm
from aist.skills.skill_loader import discover_skills

# --- Skill Discovery ---
# On startup, discover all available skills and create the prompt fragment for the LLM.
# This makes the system extensible: just drop a new skill file into the directory.
AVAILABLE_SKILLS, SKILLS_PROMPT_FRAGMENT = discover_skills()
log = logging.getLogger(__name__)

def select_skill_with_llm(llm, command, state, conversation_history, relevant_facts):
    """
    Asks the LLM to select a skill and parameters based on user input.
    This is the "Brain" part of the architecture.
    """
    # This prompt is critical. It instructs the LLM to act as a JSON-based router.
    system_prompt = f"""You are an AI assistant's brain. Your primary function is to analyze the user's request and the assistant's current state to determine the correct action.
The assistant's current state is: {state}

You must respond with a single, valid JSON object and nothing else.

The JSON object must have two keys:
1. "skill": A string representing the name of the skill to be called.
2. "parameters": An object containing the arguments for the chosen skill.

Here are the available skills:
{SKILLS_PROMPT_FRAGMENT}
- activate(): The user is trying to wake the assistant. Only use this if the state is DORMANT.
- deactivate(): The user is trying to pause the assistant. Only use this if the state is LISTENING.
- ignore(): The user's speech is irrelevant or should be ignored. Use this if no other skill fits, especially when the state is DORMANT.
- chat(query): Use for general conversation or when no other skill is appropriate. Only use this if the state is LISTENING.
- quit(): Use when the user wants to exit or stop the assistant.

Analyze the user's request: "{command}"
Based on the state and the request, choose the most appropriate skill.
If the state is DORMANT, you must be very strict. Only choose 'activate' or 'quit'. If the user says anything else, you must choose 'ignore'.
If the state is LISTENING, you can use any skill.
"""
    # We pass the full context to the LLM, which is now acting as the core of the "Brain".
    # The `process_with_llm` function is a generic LLM call wrapper.
    # NOTE: `process_with_llm` in core/llm.py must be updated to accept `system_prompt_override`.
    raw_response = process_with_llm(llm, command, conversation_history, relevant_facts, system_prompt_override=system_prompt)
    return raw_response

def command_dispatcher(command, state, llm, conversation_history, relevant_facts):
    """
    The "Skill Manager". It gets a skill selection from the "Brain" (LLM)
    and executes it via the "Hands" (the actual skill functions).
    Returns a string response to be spoken, or a special command like "QUIT_AIST".
    """
    llm_response_str = ""
    try:
        # 1. Ask the "Brain" (LLM) to choose a skill.
        llm_response_str = select_skill_with_llm(llm, command, state, conversation_history, relevant_facts)
        # The LLM is instructed to return *only* JSON, so we can parse it directly.
        decision = json.loads(llm_response_str)
        skill_name = decision.get("skill")
        parameters = decision.get("parameters", {})
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        log.error(f"Error parsing LLM decision. Falling back to chat. Error: {e}\nLLM Response: '{llm_response_str}'")
        skill_name = "chat"
        parameters = {} # Parameters will be handled in the execution block

    # --- Universal Actions & State-based Intent Translation ---
    # These actions are independent of the current state.
    if skill_name == 'ignore':
        return {'action': 'IGNORE', 'speak': None}
    if skill_name == 'quit':
        return {'action': 'EXIT', 'speak': "Goodbye."}

    if state == 'DORMANT':
        if skill_name == 'activate':
            return {'action': 'ACTIVATE', 'speak': "I'm listening."}
        else:
            # If dormant, and it wasn't activate or quit (already handled), ignore it.
            return {'action': 'IGNORE', 'speak': None}

    elif state == 'LISTENING':
        if skill_name == 'deactivate':
            return {'action': 'DEACTIVATE', 'speak': "Pausing."}
        elif skill_name == 'activate':
            # Already listening, just confirm and do nothing.
            return {'action': 'COMMAND', 'speak': "I'm already listening."}
        
        # --- Skill Execution ---
        # Handle general conversation as a special case.
        if skill_name == "chat":
            result = process_with_llm(llm, command, conversation_history, relevant_facts)
            return {'action': 'COMMAND', 'speak': result}

        if skill_name in AVAILABLE_SKILLS:
            skill_function = AVAILABLE_SKILLS[skill_name]
            try:
                # Inject the 'llm' object if the skill function's signature requests it.
                if 'llm' in inspect.signature(skill_function).parameters:
                    parameters['llm'] = llm

                result = skill_function(**parameters)
                return {'action': 'COMMAND', 'speak': result}
            except TypeError as e:
                result = f"Error calling skill '{skill_name}'. The LLM likely provided incorrect parameters. Details: {e}"
                return {'action': 'COMMAND', 'speak': result}
            except Exception as e:
                result = f"An unexpected error occurred while executing skill '{skill_name}': {e}"
                return {'action': 'COMMAND', 'speak': result}
        else:
            # Fallback if the LLM hallucinates a skill that doesn't exist.
            log.warning(f"LLM chose a non-existent skill: '{skill_name}'. Falling back to chat.")
            result = process_with_llm(llm, command, conversation_history, relevant_facts)
            return {'action': 'COMMAND', 'speak': result}