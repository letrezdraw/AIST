# core/memory.py - Long-term memory using SQLite

import logging
import sqlite3
import os

log = logging.getLogger(__name__)

# --- Database Configuration ---
DB_FOLDER = "data/memory"
DB_FILENAME = "memory.db"
DB_FILEPATH = os.path.join(DB_FOLDER, DB_FILENAME)

# --- Connection and Setup ---
# The connection is established here, but the DB file is created in setup_database()
connection = sqlite3.connect(DB_FILEPATH, check_same_thread=False)
connection.row_factory = sqlite3.Row # Allows accessing columns by name

def setup_database():
    """Creates the necessary tables if they don't exist."""
    os.makedirs(DB_FOLDER, exist_ok=True)
    cursor = connection.cursor()
    # Table for user preferences and specific facts (key-value)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_facts (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # FTS5 virtual table for efficient full-text search on general facts.
    # We keep 'id' and 'timestamp' but mark them as UNINDEXED as we only search 'content'.
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS general_facts USING fts5(id UNINDEXED, content, timestamp UNINDEXED)
    ''')
    connection.commit()

# --- Functions for General, Unstructured Facts ---
# These replace the previous ChromaDB functionality.

def add_fact(fact_text: str, fact_id: str) -> bool:
    """Adds a new general fact to the database."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO general_facts (id, content) VALUES (?, ?)",
            (fact_id, fact_text)
        )
        connection.commit()
        log.info(f"Added general fact '{fact_text}' with ID '{fact_id}'")
        return True
    except sqlite3.IntegrityError:
        log.warning(f"Fact with ID '{fact_id}' already exists.")
        return False
    except Exception as e:
        log.error(f"Error adding fact to memory: {e}", exc_info=True)
        return False

def retrieve_relevant_facts(query: str, top_n: int = 3) -> list[str]:
    """
    Retrieves relevant general facts using SQLite's FTS5 full-text search.
    This is much more effective than a simple LIKE search.
    """
    try:
        cursor = connection.cursor()
        # FTS5 queries are more powerful. We can use OR to find documents containing any of the words.
        # For more complex logic, this can be enhanced (e.g., using NEAR).
        search_query = ' OR '.join(query.split())
        cursor.execute(
            "SELECT content FROM general_facts WHERE general_facts MATCH ? ORDER BY rank LIMIT ?",
            (search_query, top_n)
        )
        results = [row['content'] for row in cursor.fetchall()]
        return results
    except Exception as e:
        log.error(f"Error retrieving facts from memory: {e}", exc_info=True)
        return []

def get_all_facts() -> list[str]:
    """Retrieves all general facts from memory."""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT content FROM general_facts ORDER BY timestamp DESC")
        return [row['content'] for row in cursor.fetchall()]
    except Exception as e:
        log.error(f"Error retrieving all facts: {e}", exc_info=True)
        return []

def find_and_delete_fact(query: str) -> str | None:
    """Finds the most relevant general fact to a query and deletes it."""
    try:
        cursor = connection.cursor()
        search_query = ' OR '.join(query.split())
        # Find the most relevant matching fact using FTS5's ranking
        cursor.execute(
            "SELECT id, content FROM general_facts WHERE general_facts MATCH ? ORDER BY rank LIMIT 1",
            (search_query,)
        )
        result = cursor.fetchone()
        if not result:
            return None

        fact_id_to_delete, fact_document_to_delete = result['id'], result['content']
        cursor.execute("DELETE FROM general_facts WHERE id = ?", (fact_id_to_delete,))
        connection.commit()
        log.info(f"Deleted fact '{fact_document_to_delete}' with ID '{fact_id_to_delete}'")
        return fact_document_to_delete
    except Exception as e:
        log.error(f"Error deleting fact: {e}", exc_info=True)
        return None

# --- Functions for Structured User Facts (Key-Value) ---
# These are new functions to manage user preferences as per the blueprint.

def set_user_fact(key: str, value: str) -> bool:
    """Saves or updates a user-specific fact (preference) using its key."""
    try:
        cursor = connection.cursor()
        # Use INSERT OR REPLACE to handle both new and existing keys
        cursor.execute(
            "INSERT OR REPLACE INTO user_facts (key, value) VALUES (?, ?)",
            (key, value)
        )
        connection.commit()
        log.info(f"Set user fact '{key}' to '{value}'")
        return True
    except Exception as e:
        log.error(f"Error setting user fact for key '{key}': {e}", exc_info=True)
        return False

def get_user_fact(key: str) -> str | None:
    """Retrieves a user-specific fact by its key."""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT value FROM user_facts WHERE key = ?", (key,))
        result = cursor.fetchone()
        return result['value'] if result else None
    except Exception as e:
        log.error(f"Error getting user fact for key '{key}': {e}", exc_info=True)
        return None

# --- Initialize Database on Load ---
setup_database()