import re
import json
from core.tts import speak
from core.llm import process_with_llm, get_intent_from_llm
from skills.system import skill_open_application, skill_close_application, skill_get_time, skill_get_system_info
from skills.web import skill_search_web

def command_dispatcher(command, llm):
    """
    Determines user intent via LLM and routes to the appropriate skill.
    Returns `False` to signal the main loop to exit, `True` otherwise.
    """
    # Immediately check for an exit command to ensure reliable shutdown.
    if "goodbye" in command or "exit" in command or "stop listening" in command:
        speak("Goodbye!")
        return False  # Signal to exit

    try:
        raw_response = get_intent_from_llm(llm, command)
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

    if command_name == "open_app":
        skill_open_application(parameters.get("app_name", ""))
    elif command_name == "close_app":
        skill_close_application(parameters.get("app_name", ""))
    elif command_name == "search_web":
        skill_search_web(parameters.get("query", ""))
    elif command_name == "get_time":
        skill_get_time()
    elif command_name == "get_system_info":
        skill_get_system_info(parameters.get("stat_type", ""))
    elif command_name == "chat":
        response = process_with_llm(llm, parameters.get("query", command))
        speak(response)
    else:
        response = process_with_llm(llm, command) # Fallback for unrecognized commands
        speak(response)

    return True  # Signal to continue