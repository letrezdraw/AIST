import json
import inspect
from core.llm import process_with_llm
from .skill_loader import discover_skills

# --- Skill Discovery ---
# On startup, discover all available skills and create the prompt fragment for the LLM.
# This makes the system extensible: just drop a new skill file into the directory.
AVAILABLE_SKILLS, SKILLS_PROMPT_FRAGMENT = discover_skills()

def select_skill_with_llm(llm, command, conversation_history, relevant_facts):
    """
    Asks the LLM to select a skill and parameters based on user input.
    This is the "Brain" part of the architecture.
    """
    # This prompt is critical. It instructs the LLM to act as a JSON-based router.
    system_prompt = f"""You are an AI assistant's brain. Your primary function is to select the correct skill to execute based on the user's request.
You must respond with a single, valid JSON object and nothing else.

The JSON object must have two keys:
1. "skill": A string representing the name of the skill to be called.
2. "parameters": An object containing the arguments for the chosen skill.

Here are the available skills:
{SKILLS_PROMPT_FRAGMENT}
- chat(query): Use for general conversation, questions, or when no other skill is appropriate.
- quit(): Use when the user wants to exit or stop the assistant.

Analyze the user's request, conversation history, and relevant facts to determine the most appropriate skill and its parameters.
If the user says "goodbye", "exit", or "stop", you must call the "quit" skill.
"""
    # We pass the full context to the LLM, which is now acting as the core of the "Brain".
    # The `process_with_llm` function is a generic LLM call wrapper.
    # NOTE: `process_with_llm` in core/llm.py must be updated to accept `system_prompt_override`.
    raw_response = process_with_llm(llm, command, conversation_history, relevant_facts, system_prompt_override=system_prompt)
    return raw_response

def command_dispatcher(command, llm, conversation_history, relevant_facts):
    """
    The "Skill Manager". It gets a skill selection from the "Brain" (LLM)
    and executes it via the "Hands" (the actual skill functions).
    Returns a string response to be spoken, or a special command like "QUIT_AIST".
    """
    llm_response_str = ""
    try:
        # 1. Ask the "Brain" (LLM) to choose a skill.
        llm_response_str = select_skill_with_llm(llm, command, conversation_history, relevant_facts)
        # The LLM is instructed to return *only* JSON, so we can parse it directly.
        decision = json.loads(llm_response_str)
        skill_name = decision.get("skill")
        parameters = decision.get("parameters", {})
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        print(f"Error parsing LLM decision. Falling back to chat. Error: {e}\nLLM Response: '{llm_response_str}'")
        skill_name = "chat"
        parameters = {} # Parameters will be handled in the execution block

    # 2. Execute the chosen skill (the "Hands").
    if skill_name == "quit":
        return "QUIT_AIST"

    # Handle general conversation as a special case.
    if skill_name == "chat":
        return process_with_llm(llm, command, conversation_history, relevant_facts)

    if skill_name in AVAILABLE_SKILLS:
        skill_function = AVAILABLE_SKILLS[skill_name]
        try:
            # Inject the 'llm' object if the skill function's signature requests it.
            # This allows skills to perform their own sub-tasks, like summarization.
            if 'llm' in inspect.signature(skill_function).parameters:
                parameters['llm'] = llm

            # For all other skills, call them with the parameters decided by the LLM.
            return skill_function(**parameters)
        except TypeError as e:
            return f"Error calling skill '{skill_name}'. The LLM likely provided incorrect parameters. Details: {e}"
        except Exception as e:
            return f"An unexpected error occurred while executing skill '{skill_name}': {e}"
    else:
        print(f"LLM chose a non-existent skill: '{skill_name}'. Falling back to chat.")
        return process_with_llm(llm, command, conversation_history, relevant_facts)