# skills/memory_skills.py - Skills for interacting with AIST's memory

import uuid
from core.memory import add_fact, get_all_facts, find_and_delete_fact

def skill_learn_fact(parameters):
    """
    Learns a new piece of information and stores it in long-term memory.
    """
    fact_to_learn = parameters.get("fact")
    if not fact_to_learn:
        return "What would you like me to learn? Please state it as a full fact."

    # Generate a unique ID for this memory
    fact_id = str(uuid.uuid4())

    if add_fact(fact_to_learn, fact_id):
        return f"Okay, I've learned that: {fact_to_learn}"
    else:
        return "I had trouble remembering that. Please try again."

def skill_list_memories(parameters):
    """Retrieves and lists all learned facts."""
    all_facts = get_all_facts()
    if not all_facts:
        return "I haven't learned anything yet."

    response = "Here is everything I have learned:\n"
    for i, fact in enumerate(all_facts, 1):
        response += f"{i}. {fact}\n"
    return response.strip()

def skill_forget_fact(parameters):
    """Forgets a fact based on a user's query."""
    fact_to_forget = parameters.get("fact_query")
    if not fact_to_forget:
        return "What should I forget? Please describe the memory."

    deleted_fact = find_and_delete_fact(fact_to_forget)

    if deleted_fact:
        return f"Okay, I will forget that: {deleted_fact}"
    else:
        return f"I couldn't find a memory related to '{fact_to_forget}'."