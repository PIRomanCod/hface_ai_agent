from typing import Optional, List, Any
import sqlite3
import os
from langchain_core.tools import tool

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "news.db")

@tool
def read_from_db(query: str) -> List[tuple]:
    """
    Execute a SELECT query on the local SQLite database and return results.
    Args:
        query: A SQL SELECT query string.
    Returns:
        List of rows resulting from the query.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        return [("Error", str(e))]

@tool
def write_to_db(query: str) -> str:
    """
    Execute an INSERT or UPDATE SQL query on the local SQLite database.
    Args:
        query: A SQL INSERT or UPDATE query string.
    Returns:
        Success message or error description.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(query)
        conn.commit()
        conn.close()
        return "Query executed successfully."
    except Exception as e:
        return f"Error: {str(e)}"