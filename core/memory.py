# core/memory.py - Long-term memory using a Vector Database

import chromadb
from chromadb.utils import embedding_functions

# Use a pre-built sentence-transformer model for creating embeddings.
# This model is small and runs efficiently on CPU.
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Initialize the ChromaDB client. It will store data in the 'chroma' directory.
client = chromadb.PersistentClient(path="./chroma")

# Get or create a collection to store memories.
# We pass the embedding function directly to the collection.
memory_collection = client.get_or_create_collection(
    name="aist_memory",
    embedding_function=sentence_transformer_ef
)

def add_fact(fact_text: str, fact_id: str):
    """Adds a new fact to the long-term memory."""
    try:
        memory_collection.add(
            documents=[fact_text],
            ids=[fact_id]
        )
        print(f"Memory: Added fact '{fact_text}' with ID '{fact_id}'")
        return True
    except Exception as e:
        print(f"Error adding fact to memory: {e}")
        return False

def retrieve_relevant_facts(query: str, top_n: int = 3) -> list[str]:
    """Retrieves the most relevant facts from memory based on a query."""
    try:
        results = memory_collection.query(query_texts=[query], n_results=top_n)
        return results['documents'][0] if results['documents'] else []
    except Exception as e:
        print(f"Error retrieving facts from memory: {e}")
        return []

def get_all_facts() -> list[str]:
    """Retrieves all facts from memory as a list of strings."""
    try:
        results = memory_collection.get()
        return results['documents'] if results and results.get('documents') else []
    except Exception as e:
        print(f"Error retrieving all facts: {e}")
        return []

def find_and_delete_fact(query: str) -> str | None:
    """Finds the most relevant fact to a query and deletes it."""
    try:
        # Find the most relevant fact
        results = memory_collection.query(query_texts=[query], n_results=1)
        if not results or not results.get('ids') or not results['ids'][0]:
            return None # No fact found to delete

        fact_id_to_delete = results['ids'][0][0]
        fact_document_to_delete = results['documents'][0][0]

        memory_collection.delete(ids=[fact_id_to_delete])
        print(f"Memory: Deleted fact '{fact_document_to_delete}' with ID '{fact_id_to_delete}'")
        return fact_document_to_delete # Return the text of the deleted fact
    except Exception as e:
        print(f"Error deleting fact: {e}")
        return None