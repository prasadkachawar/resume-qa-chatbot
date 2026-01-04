from app.services.chromadb_service import chromadb_service
from app.utils.pdf_processor import PDFProcessor
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class ResumeVectorService:
    """Service for processing resume and creating vectors"""
    
    def __init__(self):
        self.chromadb_service = chromadb_service
        self.pdf_processor = PDFProcessor()
    
    def process_resume_pdf(self, pdf_path: str, chunk_size: int = 100, overlap: int = 10) -> Dict[str, Any]:
        """
        Process resume PDF and store vectors in ChromaDB
        
        Args:
            pdf_path: Path to the resume PDF file
            chunk_size: Size of each text chunk (default: 100 characters)
            overlap: Overlap between chunks (default: 10 characters)
            
        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Starting resume processing for: {pdf_path}")
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"Resume PDF not found: {pdf_path}")
            
            # Process PDF to chunks
            pdf_result = self.pdf_processor.process_pdf_to_chunks(pdf_path, chunk_size, overlap)
            
            # Extract chunk texts and metadata
            chunk_texts = pdf_result['chunk_texts']
            chunk_metadata = pdf_result['chunk_metadata']
            
            # Add additional metadata
            for metadata in chunk_metadata:
                metadata.update({
                    'document_type': 'resume',
                    'processing_timestamp': datetime.now().isoformat(),
                    'embedding_model': 'all-MiniLM-L6-v2'
                })
            
            # Store chunks in ChromaDB
            success = self.chromadb_service.add_text_chunks(chunk_texts, chunk_metadata)
            
            if success:
                logger.info(f"Successfully stored {len(chunk_texts)} chunks in ChromaDB")
                
                # Get collection stats
                stats = self.chromadb_service.get_collection_stats()
                
                return {
                    'success': True,
                    'message': 'Resume processed and vectors created successfully',
                    'source_file': pdf_path,
                    'total_chunks': len(chunk_texts),
                    'total_characters': len(pdf_result['original_text']),
                    'chunk_size': chunk_size,
                    'overlap': overlap,
                    'collection_stats': stats,
                    'sample_chunk': chunk_texts[0] if chunk_texts else None
                }
            else:
                raise Exception("Failed to store chunks in ChromaDB")
                
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to process resume and create vectors'
            }
    
    def search_resume_content(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Search for content in the resume using semantic search
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            Search results
        """
        try:
            results = self.chromadb_service.search_similar_chunks(query, n_results)
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'message': f"Found {results['count']} relevant chunks"
            }
            
        except Exception as e:
            logger.error(f"Error searching resume content: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to search resume content'
            }
    
    def answer_question_with_llm(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Answer questions about the resume using LLM-enhanced responses
        
        Args:
            question: User's question
            n_results: Number of context chunks to retrieve
            
        Returns:
            LLM-generated answer with context
        """
        try:
            # First, get relevant context from ChromaDB
            search_results = self.search_resume_content(question, n_results)
            
            if not search_results['success']:
                return search_results
            
            # Extract context text from search results
            context_chunks = []
            if search_results['results']['documents']:
                context_chunks = search_results['results']['documents'][0]
            
            context = '\n'.join(context_chunks) if context_chunks else "No relevant context found"
            
            # Use LLM service to generate intelligent answer
            try:
                from app.services.llm_service import get_llm_service
                llm_service = get_llm_service()
                
                intelligent_answer = llm_service.generate_answer(question, context)
                
                return {
                    'success': True,
                    'question': question,
                    'answer': intelligent_answer,
                    'context_used': context_chunks,
                    'search_results': search_results['results'],
                    'llm_backend': llm_service.backend,
                    'message': 'Answer generated successfully'
                }
                
            except ImportError:
                # Fallback if LLM service not available
                return self._generate_simple_answer(question, context_chunks, search_results)
                
        except Exception as e:
            logger.error(f"Error generating LLM answer: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to generate answer'
            }
    
    def _generate_simple_answer(self, question: str, context_chunks: List[str], search_results: Dict) -> Dict[str, Any]:
        """Fallback method for generating answers without LLM"""
        if context_chunks:
            # Simple concatenation of relevant chunks
            answer = f"Based on the resume information: {' '.join(context_chunks[:2])}"
        else:
            answer = "I couldn't find specific information about that in the resume."
        
        return {
            'success': True,
            'question': question,
            'answer': answer,
            'context_used': context_chunks,
            'search_results': search_results['results'] if 'results' in search_results else {},
            'llm_backend': 'simple_fallback',
            'message': 'Simple answer generated (LLM not available)'
        }
    
    def get_resume_stats(self) -> Dict[str, Any]:
        """Get statistics about the stored resume vectors"""
        try:
            stats = self.chromadb_service.get_collection_stats()
            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            logger.error(f"Error getting resume stats: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def clear_resume_vectors(self) -> Dict[str, Any]:
        """Clear all resume vectors from ChromaDB"""
        try:
            success = self.chromadb_service.clear_collection()
            if success:
                return {
                    'success': True,
                    'message': 'Resume vectors cleared successfully'
                }
            else:
                raise Exception("Failed to clear vectors")
                
        except Exception as e:
            logger.error(f"Error clearing resume vectors: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to clear resume vectors'
            }
    
    def reprocess_resume(self, pdf_path: str, chunk_size: int = 100, overlap: int = 10) -> Dict[str, Any]:
        """
        Clear existing vectors and reprocess the resume
        
        Args:
            pdf_path: Path to the resume PDF file
            chunk_size: Size of each text chunk
            overlap: Overlap between chunks
            
        Returns:
            Processing results
        """
        try:
            # Clear existing vectors
            clear_result = self.clear_resume_vectors()
            if not clear_result['success']:
                return clear_result
            
            # Process resume again
            return self.process_resume_pdf(pdf_path, chunk_size, overlap)
            
        except Exception as e:
            logger.error(f"Error reprocessing resume: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to reprocess resume'
            }

# Global service instance
resume_vector_service = ResumeVectorService()
