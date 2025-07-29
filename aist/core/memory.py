# aist/core/memory.py
import sqlite3
import logging
import os
import time

log = logging.getLogger(__name__)

# Define DB path
DB_FOLDER = "data/memory"
DB_PATH = os.path.join(DB_FOLDER, "memory.db")

def _initialize_db():
    """
    Ensures the database and the 'general_facts' FTS5 table exist and have the correct schema.
    If an old, invalid table is found, it is dropped and recreated.
    """
    os.makedirs(DB_FOLDER, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # This query is a lightweight way to check if the table exists and is a valid FTS table.
        # It will raise an OperationalError if 'general_facts' is a standard table.
        cursor.execute("SELECT * FROM general_facts WHERE general_facts MATCH 'test';")
    except sqlite3.OperationalError:
        log.warning("Memory database has an outdated schema. Recreating the 'general_facts' table...")
        # Drop the old table if it exists, then create the new FTS5 table.
        cursor.execute("DROP TABLE IF EXISTS general_facts;")
        cursor.execute("""
        CREATE VIRTUAL TABLE general_facts USING fts5(
            content,
            timestamp,
            source
        );
        """)
        log.info("FTS5 memory table 'general_facts' recreated successfully.")

    conn.commit()
    conn.close()

def store_fact(content: str, source: str):
    """Stores a new fact in the general_facts FTS5 table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO general_facts (content, timestamp, source) VALUES (?, ?, ?)",
        (content, time.time(), source)
    )
    conn.commit()
    conn.close()
    log.info(f"Stored new fact from '{source}'.")

def retrieve_relevant_facts(search_query: str, top_n: int = 3):
    """Retrieves the most relevant facts from memory using FTS5."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM general_facts WHERE general_facts MATCH ? ORDER BY rank LIMIT ?", (search_query, top_n))
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    except sqlite3.OperationalError as e:
        log.error(f"Error retrieving facts from memory: {e}", exc_info=True)
        return []

# Initialize the database when the module is first imported.
_initialize_db()