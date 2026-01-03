import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import os
import logging
from typing import List, Dict, Any
import uuid

logger = logging.getLogger(__name__)

class ChromaDBService:
    """Service for managing ChromaDB operations"""
    
    def __init__(self, persist_directory: str = None):
        """Initialize ChromaDB client and embedding model"""
        if persist_directory is None:
            persist_directory = os.path.join(os.path.dirname(__file__), '..', '..', 'chroma_db')
        
        # Create directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use default embedding function (OpenAI-compatible or default)
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Collection for resume vectors
        self.resume_collection_name = "resume_vectors"
        self.resume_collection = None
        
    def get_or_create_resume_collection(self):
        """Get or create the resume collection"""
        try:
            self.resume_collection = self.client.get_collection(
                name=self.resume_collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Retrieved existing collection: {self.resume_collection_name}")
        except ValueError:
            # Collection doesn't exist, create it
            self.resume_collection = self.client.create_collection(
                name=self.resume_collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Resume text chunks with embeddings"}
            )
            logger.info(f"Created new collection: {self.resume_collection_name}")
        
        return self.resume_collection
    
    def add_text_chunks(self, chunks: List[str], metadata: List[Dict[str, Any]] = None) -> bool:
        """Add text chunks with their embeddings to the collection"""
        try:
            collection = self.get_or_create_resume_collection()
            
            # Generate unique IDs for each chunk
            ids = [str(uuid.uuid4()) for _ in chunks]
            
            # Prepare metadata if not provided
            if metadata is None:
                metadata = [{"chunk_index": i, "text_length": len(chunk)} for i, chunk in enumerate(chunks)]
            
            # Add to collection (ChromaDB will generate embeddings automatically)
            collection.add(
                documents=chunks,
                metadatas=metadata,
                ids=ids
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to collection")
            return True
            
        except Exception as e:
            logger.error(f"Error adding text chunks: {str(e)}")
            return False
    
    def search_similar_chunks(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search for similar chunks based on query"""
        try:
            collection = self.get_or_create_resume_collection()
            
            # Search for similar chunks (ChromaDB will generate query embedding automatically)
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'count': len(results['documents'][0]) if results['documents'] else 0
            }
            
        except Exception as e:
            logger.error(f"Error searching chunks: {str(e)}")
            return {'documents': [], 'metadatas': [], 'distances': [], 'count': 0}
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the resume collection"""
        try:
            collection = self.get_or_create_resume_collection()
            count = collection.count()
            
            return {
                'collection_name': self.resume_collection_name,
                'total_chunks': count,
                'embedding_model': 'all-MiniLM-L6-v2'
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {'collection_name': self.resume_collection_name, 'total_chunks': 0}
    
    def clear_collection(self) -> bool:
        """Clear all data from the resume collection"""
        try:
            # Delete the collection if it exists
            try:
                self.client.delete_collection(self.resume_collection_name)
                logger.info(f"Deleted collection: {self.resume_collection_name}")
            except ValueError:
                logger.info(f"Collection {self.resume_collection_name} doesn't exist")
            
            # Recreate the collection
            self.get_or_create_resume_collection()
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False

# Global service instance
chromadb_service = ChromaDBService()
