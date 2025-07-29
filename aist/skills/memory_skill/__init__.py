# aist/skills/memory_skill/__init__.py
import logging
from aist.skills.base import BaseSkill
from aist.core.memory import store_fact, retrieve_relevant_facts

log = logging.getLogger(__name__)


class MemorySkill(BaseSkill):
    def initialize(self):
        log.info("Memory skill initialized.")

    def register_intents(self, register_intent_handler):
        """Register this skill's intents."""
        register_intent_handler('store_memory', {
            "phrases": ["remember that", "store this information", "remind me that"],
            "handler": self.handle_store_memory,
            "parameters": [
                {"name": "fact", "description": "The specific piece of information to be stored in memory."}
            ]

        })
        register_intent_handler('recall_memory', {
            "phrases": ["what do you know about", "what do you remember about", "tell me about"],
            "handler": self.handle_recall_memory,
            "parameters": [
                {"name": "query", "description": "The topic to search for in memory."}
        
            ]
        })

    def handle_store_memory(self, payload):
        """Handler for storing a fact."""
        fact = payload.get("fact")
        if not fact:
            return "I didn't quite catch what you wanted me to remember."
        store_fact(fact, source=self.skill_id)
        return "Okay, I'll remember that."

    def handle_recall_memory(self, payload):
        """Handler for recalling facts."""
        query = payload.get("query")
        if not query:
            return "What would you like to know about?"
        results = retrieve_relevant_facts(query, top_n=1)
        if not results:
            return f"I don't seem to have any memories about {query}."
        return f"I remember this about {query}: {results[0]}"

def create_skill():
    """The entry point for the skill loader."""
    return MemorySkill()