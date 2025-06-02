import os
import sqlite3
import chromadb
import hashlib
from typing import Dict, Any, List, Optional

class DatabaseManager:
    """
    Manage database connections and operations
    
    This class provides a unified interface for interacting with both SQLite and ChromaDB databases.
    SQLite is used for storing session metadata and analysis results in a structured format,
    while ChromaDB is used for storing the actual document content with vector embeddings
    for potential semantic search capabilities.
    """
    
    def __init__(self, base_path: str = ".data"):
        """
        Initialize database manager with base path for storage
        
        Creates necessary directories and initializes connections to both SQLite and ChromaDB.
        
        Args:
            base_path (str): Base directory for storing database files
        """
        self.base_path = base_path
        self.chroma_path = os.path.join(base_path, "chroma")
        self.sqlite_path = os.path.join(base_path, "sessions.db")
        
        # Create base directory if it doesn't exist
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.chroma_path, exist_ok=True)
        
        # Initialize SQLite
        self.conn = sqlite3.connect(self.sqlite_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._init_sqlite_tables()
        
        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_path)
        
        # Cache for collection objects
        self.collections = {}
    
    def _init_sqlite_tables(self):
        """
        Initialize SQLite tables
        
        Creates the sessions table if it doesn't exist, which stores:
        - session_id: Unique identifier for each analysis session
        - url: The URL of the analyzed document
        - readability: LLM analysis of document readability
        - structure: LLM analysis of document structure
        - completeness: LLM analysis of document completeness
        - style: LLM analysis of document style adherence
        """
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT, 
            url TEXT, 
            readability TEXT, 
            structure TEXT, 
            completeness TEXT, 
            style TEXT
        )''')
        self.conn.commit()
    
    def get_url_collection(self, url: str) -> chromadb.Collection:
        """
        Get a ChromaDB collection for a specific URL
        
        Creates a deterministic collection name from the URL using MD5 hashing,
        which allows us to store documents from the same URL in the same collection
        for efficient retrieval and comparison.
        
        Args:
            url (str): The URL to get a collection for
            
        Returns:
            chromadb.Collection: The ChromaDB collection for the URL
        """
        # Create a deterministic collection name from the URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        collection_name = f"url_{url_hash}"
        
        # Return from cache if exists
        if collection_name in self.collections:
            return self.collections[collection_name]
        
        # Create and cache collection
        collection = self.chroma_client.get_or_create_collection(name=collection_name)
        self.collections[collection_name] = collection
        return collection
    
    def save_analysis(self, session_id: str, url: str, content: str, analysis_results: Dict[str, Any]) -> None:
        """
        Save analysis results to both SQLite and ChromaDB
        
        This method stores the analysis results in SQLite for structured querying,
        and the full document content in ChromaDB for potential semantic search.
        The session_id acts as a link between the two databases.
        
        Args:
            session_id (str): Unique identifier for the analysis session
            url (str): URL of the analyzed document
            content (str): Full text content of the document
            analysis_results (Dict[str, Any]): Results of the document analysis
        """
        # Save to SQLite
        self.cursor.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?, ?)", 
            (
                session_id, 
                url, 
                analysis_results["readability"]["analysis"] if isinstance(analysis_results["readability"], dict) else analysis_results["readability"],
                analysis_results["structure"],
                analysis_results["completeness"],
                analysis_results["style"]
            )
        )
        self.conn.commit()
        
        # Save to ChromaDB (URL-specific collection)
        collection = self.get_url_collection(url)
        collection.add(
            documents=[content],
            metadatas=[{
                "session_id": session_id, 
                "url": url,
                "analysis_summary": f"Readability: {analysis_results.get('readability_score', 'N/A')}"
            }],
            ids=[session_id]
        )
    
    def get_recent_sessions(self, limit: int = 5) -> List:
        """
        Get recent analysis sessions
        
        Retrieves the most recent analysis sessions from SQLite,
        ordered by the implicit rowid which increases with each insertion.
        
        Args:
            limit (int): Maximum number of sessions to retrieve
            
        Returns:
            List: List of session data tuples (session_id, url, rowid)
        """
        self.cursor.execute("SELECT session_id, url, rowid FROM sessions ORDER BY rowid DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()
    
    def get_all_sessions(self) -> List:
        """
        Get all analysis sessions
        
        Retrieves all analysis sessions from SQLite,
        ordered by the implicit rowid which increases with each insertion.
        
        Returns:
            List: List of session data tuples (session_id, url, readability, structure, completeness, style, rowid)
        """
        self.cursor.execute("SELECT session_id, url, readability, structure, completeness, style, rowid FROM sessions ORDER BY rowid DESC")
        return self.cursor.fetchall()
    
    def get_session(self, session_id: str) -> Optional[tuple]:
        """
        Get a specific analysis session
        
        Retrieves a specific analysis session from SQLite by its session_id.
        
        Args:
            session_id (str): The session ID to retrieve
            
        Returns:
            Optional[tuple]: Session data tuple or None if not found
        """
        self.cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        return self.cursor.fetchone()
    
    def close(self):
        """
        Close database connections
        
        Closes the SQLite connection to prevent resource leaks.
        """
        self.conn.close()

def init_databases(base_path: str = ".data") -> DatabaseManager:
    """
    Initialize and return a DatabaseManager instance
    
    This is a convenience function for creating a DatabaseManager with the given base path.
    
    Args:
        base_path (str): Base directory for storing database files
        
    Returns:
        DatabaseManager: Initialized database manager
    """
    return DatabaseManager(base_path)