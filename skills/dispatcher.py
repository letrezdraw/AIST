

import re
from core.tts import speak
from core.llm import process_with_llm
from skills.system import skill_open_application, skill_get_time, skill_get_system_info
from skills.web import skill_search_web

def command_dispatcher(command, llm):

    if match := re.search(r'open (.*)', command, re.IGNORECASE):
        app_name = match.group(1)
        skill_open_application(app_name)
    elif match := re.search(r'search for (.*)', command, re.IGNORECASE):
        query = match.group(1)
        skill_search_web(query)
    elif "what time is it" in command:
        skill_get_time()
    elif match := re.search(r'.*(cpu|processor) (usage|load|status)', command, re.IGNORECASE):
        # Example: "what's the cpu usage?"
        skill_get_system_info('cpu')
    elif match := re.search(r'.*(battery|power) (status|level|percentage)', command, re.IGNORECASE):
        # Example: "check battery status"
        skill_get_system_info('battery')
    elif "goodbye" in command or "exit" in command or "stop listening" in command:
        speak("Goodbye!")
        return False  # Signal to exit
    else:
        # If no skill matches, treat it as a conversation
        response = process_with_llm(llm, command)
        speak(response)

    return True  # Signal to continue