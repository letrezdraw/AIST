import re
import json
from core.llm import process_with_llm, get_intent_from_llm, summarize_system_output
from skills.system import skill_open_application, skill_close_application, skill_get_time, skill_get_system_info, skill_execute_system_command
from skills.memory_skills import skill_learn_fact, skill_list_memories, skill_forget_fact
from skills.web import skill_search_web

# --- Skill Mapping ---
# This dictionary-based approach is much cleaner and more scalable than if/elif chains.
# To add a new skill, just import it and add it to this dictionary.
SKILLS = {
    "open_app": skill_open_application,
    "close_app": skill_close_application,
    "search_web": skill_search_web,
    "get_time": skill_get_time,
    "get_system_info": skill_get_system_info,
    "learn_fact": skill_learn_fact,
    "list_memories": skill_list_memories,
    "forget_fact": skill_forget_fact,
    "execute_system_command": skill_execute_system_command,
}

def command_dispatcher(command, llm, conversation_history, relevant_facts):
    """
    Determines user intent, routes to the appropriate skill, and returns the response.
    Returns a string response to be spoken, or `False` to signal exit.
    """
    # Immediately check for an exit command to ensure reliable shutdown.
    if "goodbye" in command or "exit" in command or "stop listening" in command:
        return False  # Signal to exit

    try:
        raw_response = get_intent_from_llm(llm, command, conversation_history, relevant_facts)
        # Use regex to find the JSON object within the LLM's raw response
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if not json_match:
            raise json.JSONDecodeError("No JSON object found in LLM response.", raw_response, 0)
        
        intent_json = json_match.group(0)
        intent = json.loads(intent_json) # Parse the extracted JSON

        command_name = intent.get("command")
        parameters = intent.get("parameters", {})
    except (json.JSONDecodeError, AttributeError, TypeError, IndexError) as e:
        print(f"Could not parse intent from LLM response. Falling back to chat. Error: {e}")
        command_name = "chat"
        parameters = {"query": command}

    # --- Route to the appropriate skill with special handling for system commands ---
    if command_name == "execute_system_command":
        # Execute the command to get raw output
        raw_output = skill_execute_system_command(parameters)
        # Ask the LLM to summarize the raw output for the user
        return summarize_system_output(llm, command, raw_output)

    if command_name in SKILLS:
        skill_function = SKILLS[command_name]
        # All other skills are called directly
        return skill_function(parameters)
    elif command_name == "chat":
        return process_with_llm(llm, parameters.get("query", command), conversation_history, relevant_facts)
    else:
        # Fallback for unrecognized commands
        return process_with_llm(llm, command, conversation_history, relevant_facts)