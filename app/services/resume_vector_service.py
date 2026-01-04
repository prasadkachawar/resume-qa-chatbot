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
        Optimized RAG flow: Chunking -> Embedding -> Retrieval -> LLM Generation
        
        Flow:
        1. Text is already chunked with overlapping windows (nothing missed)
        2. User query embedded with same embedding method as document chunks
        3. Retrieve top 3 results from vector database
        4. Send top 3 hits with user query to LLM and parse answer to user
        
        Args:
            question: User's question
            n_results: Number of context chunks to retrieve (default: 3 for optimal performance)
            
        Returns:
            LLM-generated answer with context
        """
        try:
            logger.info(f"🔍 Step 1: Processing query: '{question}'")
            
            # STEP 2: User query embedded with same embedding method
            # ChromaDB automatically uses the same embedding function for search as storage
            search_results = self.chromadb_service.search_similar_chunks(question, n_results)
            
            if not search_results or 'documents' not in search_results:
                return {
                    'success': False,
                    'error': 'No search results found',
                    'message': 'Unable to find relevant information'
                }
            
            # STEP 3: Retrieve top 3 results from database
            top_chunks = search_results['documents'][0] if search_results['documents'] else []
            distances = search_results['distances'][0] if search_results['distances'] else []
            
            logger.info(f"📊 Step 3: Retrieved {len(top_chunks)} chunks with distances: {distances}")
            
            if not top_chunks:
                return {
                    'success': False,
                    'error': 'No relevant chunks found',
                    'message': 'Could not find relevant information in the resume'
                }
            
            # Prepare context from top 3 hits
            context = self._prepare_context_from_chunks(top_chunks, distances)
            
            # STEP 4: Send top 3 hits with user query to LLM
            logger.info(f"🤖 Step 4: Generating LLM response with {len(top_chunks)} context chunks")
            
            try:
                from app.services.llm_service import get_llm_service
                llm_service = get_llm_service()
                
                # Generate intelligent answer using LLM with context
                intelligent_answer = llm_service.generate_answer(question, context)
                
                logger.info(f"✅ Successfully generated LLM answer using {llm_service.backend} backend")
                
                return {
                    'success': True,
                    'question': question,
                    'answer': intelligent_answer,
                    'context_chunks': top_chunks,
                    'chunk_scores': distances,
                    'num_chunks_used': len(top_chunks),
                    'llm_backend': llm_service.backend,
                    'message': f'Answer generated using {len(top_chunks)} most relevant chunks'
                }
                
            except ImportError as e:
                logger.warning(f"LLM service not available: {e}, using fallback")
                return self._generate_fallback_answer(question, top_chunks, distances)
                
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to process question through RAG pipeline'
            }
    
    def _prepare_context_from_chunks(self, chunks: List[str], distances: List[float]) -> str:
        """
        Prepare context from retrieved chunks, ordered by relevance
        
        Args:
            chunks: Retrieved text chunks
            distances: Similarity distances (lower = more similar)
            
        Returns:
            Formatted context string
        """
        # Sort chunks by relevance (lower distance = more relevant)
        chunk_data = list(zip(chunks, distances))
        chunk_data.sort(key=lambda x: x[1])  # Sort by distance
        
        # Format context with relevance indicators
        context_parts = []
        for i, (chunk, distance) in enumerate(chunk_data):
            relevance_score = max(0, 1 - distance)  # Convert distance to relevance (0-1)
            context_parts.append(f"[Context {i+1} - Relevance: {relevance_score:.2f}]\n{chunk.strip()}")
        
        return "\n\n".join(context_parts)
    
    def _generate_fallback_answer(self, question: str, chunks: List[str], distances: List[float]) -> Dict[str, Any]:
        """
        Fallback method when LLM is not available
        Uses simple text processing with the top 3 chunks
        """
        # Use the most relevant chunk (lowest distance)
        best_chunk = chunks[0] if chunks else ""
        
        # Simple answer construction
        if any(keyword in question.lower() for keyword in ['skill', 'technology', 'programming']):
            answer = f"Based on the resume, the technical skills include: {best_chunk}"
        elif any(keyword in question.lower() for keyword in ['experience', 'work', 'job']):
            answer = f"Work experience summary: {best_chunk}"
        elif any(keyword in question.lower() for keyword in ['education', 'degree', 'study']):
            answer = f"Educational background: {best_chunk}"
        elif any(keyword in question.lower() for keyword in ['contact', 'email', 'phone']):
            answer = f"Contact information: {best_chunk}"
        else:
            answer = f"Based on the resume information: {best_chunk}"
        
        return {
            'success': True,
            'question': question,
            'answer': answer,
            'context_chunks': chunks,
            'chunk_scores': distances,
            'num_chunks_used': len(chunks),
            'llm_backend': 'simple_fallback',
            'message': f'Fallback answer generated using {len(chunks)} chunks'
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
