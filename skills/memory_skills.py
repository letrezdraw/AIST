# skills/memory_skills.py - Skills for interacting with AIST's memory

import uuid
from core.memory import add_fact, get_all_facts, find_and_delete_fact, set_user_fact, get_user_fact

def skill_learn_fact(fact: str):
    """Learns and stores a new piece of information (a fact) in long-term memory."""
    if not fact:
        return "What would you like me to learn? Please state it as a full fact."

    # Generate a unique ID for this memory
    fact_id = str(uuid.uuid4())

    if add_fact(fact, fact_id):
        return f"Okay, I've learned that: {fact}"
    else:
        return "I had trouble remembering that. Please try again."

def skill_list_memories():
    """Retrieves and lists all learned facts from memory."""
    all_facts = get_all_facts()
    if not all_facts:
        return "I haven't learned anything yet."

    response = "Here is everything I have learned:\n"
    for i, fact in enumerate(all_facts, 1):
        # Ensure each fact ends with a newline for clean formatting
        response += f"{i}. {fact.strip()}\n"
    return response.strip()

def skill_forget_fact(fact_query: str):
    """Forgets a fact from memory based on a user's query describing the memory."""
    if not fact_query:
        return "What should I forget? Please describe the memory."

    deleted_fact = find_and_delete_fact(fact_query)

    if deleted_fact:
        return f"Okay, I will forget that: {deleted_fact}"
    else:
        return f"I couldn't find a memory related to '{fact_query}'."

def skill_remember_preference(key: str, value: str):
    """Remembers a specific user preference with a key and a value (e.g., key='git path', value='D:/repos')."""
    if not key or not value:
        return "I need both a name and a value for the preference you want me to remember."

    if set_user_fact(key, value):
        return f"Okay, I've remembered that '{key}' is '{value}'."
    else:
        return f"I had trouble remembering the preference for '{key}'."

def skill_recall_preference(key: str):
    """Recalls a specific user preference by its key."""
    if not key:
        return "What preference are you asking about?"

    value = get_user_fact(key)

    if value:
        return f"I remember that '{key}' is '{value}'."
    else:
        return f"I don't have a preference stored for '{key}'."