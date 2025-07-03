# ChromaClient.py
# This module will contain ChromaDB client functionality

import re
import sqlite3
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

class ChromaCollectionFactory:    
    @staticmethod
    def query_as_list(query: str, db_path: str = "../Chinook.db") -> list:
        """Execute SQLite query and return cleaned list of unique string values"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        conn.close()

        res = [str(item) for row in res for item in row if item]
        res = [re.sub(r"\b\d+\b", "", string).strip() for string in res]
        return list(set([item for item in res if item]))
    
    @classmethod
    def create_collection(cls, db_path: str = "../Chinook.db", chroma_path: str = "../chroma_data_chinook"):
        """
        Factory method to create and populate ChromaDB collection with artists and albums
        
        Args:
            db_path (str): Path to SQLite database (default: "../Chinook.db")
            chroma_path (str): Path to ChromaDB storage directory (default: "../chroma_data_chinook")
            
        Returns:
            chromadb.Collection: Populated ChromaDB collection
        """
        # Get artists and albums
        artists = cls.query_as_list("SELECT Name FROM Artist", db_path)
        albums = cls.query_as_list("SELECT Title FROM Album", db_path)
        
        # Create ChromaDB client
        chroma_client = chromadb.PersistentClient(path=chroma_path)
        
        # Create or get a collection to store embeddings
        collection = chroma_client.get_or_create_collection(
            name="chinook_agent",
            embedding_function=OpenAIEmbeddingFunction(
                model_name="text-embedding-3-large"
            )
        )
        
        # Add artists to collection
        if artists:
            collection.add(
                documents=artists,
                ids=["artist_" + str(index) for index, _ in enumerate(artists)]
            )
        
        # Add albums to collection
        if albums:
            collection.add(
                documents=albums,
                ids=["albums_" + str(index) for index, _ in enumerate(albums)]
            )
        
        return collection
