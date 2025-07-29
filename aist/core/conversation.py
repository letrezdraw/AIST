# aist/core/conversation.py
import logging
from collections import deque
from aist.core.config_manager import config

log = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages the short-term conversation history for contextual understanding.
    """
    def __init__(self):
        # max_history_length is the number of user/assistant *exchanges*.
        # So, the deque will hold 2 * max_history_length items.
        history_length = config.get('assistant.conversation_history_length', 5)
        self.max_size = history_length * 2
        self.history = deque(maxlen=self.max_size)
        log.info(f"ConversationManager initialized with a max history of {history_length} exchanges.")

    def add_message(self, role: str, text: str):
        """Adds a message to the history."""
        self.history.append({"role": role, "content": text})

    def get_history(self) -> list[dict]:
        """Returns the current conversation history as a list of dicts."""
        return list(self.history)

    def clear(self):
        """Clears the conversation history."""
        self.history.clear()
        log.info("Conversation history cleared.")