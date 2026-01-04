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
    
    def answer_question_with_llm(self, question: str, n_results: int = 3) -> Dict[str, Any]:
        """
        RAG Flow: DB → Top 3 → LLM → Single Answer → Frontend
        
        Flow:
        1. User query embedded with same method as documents
        2. Retrieve top 3 results from vector database
        3. Send top 3 results + user query to LLM
        4. LLM generates ONE answer
        5. Send single answer to frontend
        
        Args:
            question: User's question
            n_results: Number of context chunks to retrieve (fixed at 3)
            
        Returns:
            Single LLM-generated answer for frontend
        """
        try:
            logger.info(f"🔍 Step 1: Embedding user query: '{question}'")
            
            # STEP 1: Get top 3 results from database
            search_results = self.chromadb_service.search_similar_chunks(question, n_results)
            
            if not search_results or 'documents' not in search_results:
                return {
                    'success': False,
                    'error': 'No search results found',
                    'message': 'Unable to find relevant information'
                }
            
            # STEP 2: Extract top 3 results
            top_3_chunks = search_results['documents'][0] if search_results['documents'] else []
            distances = search_results['distances'][0] if search_results['distances'] else []
            
            logger.info(f"📊 Step 2: Retrieved top {len(top_3_chunks)} chunks from database")
            
            if not top_3_chunks:
                return {
                    'success': False,
                    'error': 'No relevant chunks found',
                    'message': 'Could not find relevant information in the resume'
                }
            
            # STEP 3: Prepare context from top 3 results for LLM
            context = self._format_context_for_llm(top_3_chunks)
            
            logger.info(f"🤖 Step 3: Sending top 3 results + query to LLM")
            
            # STEP 4: Get ONE answer from LLM
            try:
                from app.services.llm_service import get_llm_service
                llm_service = get_llm_service()
                
                # LLM generates ONE single answer based on top 3 results
                single_answer = llm_service.generate_answer(question, context)
                
                logger.info(f"✅ Step 4: LLM generated single answer using {llm_service.backend}")
                
                # STEP 5: Return single answer to frontend
                return {
                    'success': True,
                    'question': question,
                    'answer': single_answer,  # ONE answer only
                    'llm_backend': llm_service.backend,
                    'chunks_used': len(top_3_chunks),
                    'message': f'Single answer generated from top {len(top_3_chunks)} database results'
                }
                
            except ImportError as e:
                logger.warning(f"LLM service not available: {e}, using fallback")
                return self._generate_fallback_single_answer(question, top_3_chunks)
                
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to process question through RAG pipeline'
            }
    
    def _format_context_for_llm(self, top_3_chunks: List[str]) -> str:
        """
        Format top 3 database results as context for LLM
        
        Args:
            top_3_chunks: Top 3 most relevant chunks from database
            
        Returns:
            Formatted context string for LLM processing
        """
        # Simple concatenation of top 3 results
        context = "\n".join(f"Context {i+1}: {chunk}" for i, chunk in enumerate(top_3_chunks))
        return context
    
    def _generate_fallback_single_answer(self, question: str, top_3_chunks: List[str]) -> Dict[str, Any]:
        """
        Fallback method: Generate ONE answer when LLM is not available
        Uses top 3 chunks to create a single response
        """
        # Use the most relevant chunk (first one) as primary answer
        primary_chunk = top_3_chunks[0] if top_3_chunks else ""
        
        # Create one cohesive answer from top 3 chunks
        if any(keyword in question.lower() for keyword in ['skill', 'technology', 'programming']):
            answer = f"Technical skills include: {primary_chunk}"
        elif any(keyword in question.lower() for keyword in ['experience', 'work', 'job']):
            answer = f"Work experience: {primary_chunk}"
        elif any(keyword in question.lower() for keyword in ['education', 'degree', 'study']):
            answer = f"Educational background: {primary_chunk}"
        elif any(keyword in question.lower() for keyword in ['contact', 'email', 'phone']):
            answer = f"Contact information: {primary_chunk}"
        else:
            answer = f"Based on the resume: {primary_chunk}"
        
        return {
            'success': True,
            'question': question,
            'answer': answer,  # ONE answer only
            'llm_backend': 'fallback',
            'chunks_used': len(top_3_chunks),
            'message': f'Single fallback answer generated from top {len(top_3_chunks)} results'
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
