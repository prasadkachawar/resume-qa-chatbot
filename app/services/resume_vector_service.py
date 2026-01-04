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
        # Initialize NER service for entity extraction
        self.ner_service = None
        self._initialize_ner_service()
    
    def _initialize_ner_service(self):
        """Initialize Resume NER service"""
        try:
            from app.services.resume_ner_service import get_resume_ner_service
            self.ner_service = get_resume_ner_service()
            logger.info("✅ Resume NER service initialized")
        except Exception as e:
            logger.warning(f"NER service not available: {e}")
            self.ner_service = None
    
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
            top_3_chunks = search_results['documents'] if search_results['documents'] else []
            distances = search_results['distances'] if search_results['distances'] else []
            
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

    def extract_resume_entities(self, pdf_path: str = None, text: str = None) -> Dict[str, Any]:
        """
        Extract structured information from resume using NER model
        
        Args:
            pdf_path: Path to PDF file (optional)
            text: Resume text directly (optional)
            
        Returns:
            Dictionary with extracted entities
        """
        try:
            # Get text from PDF or use provided text
            if pdf_path and os.path.exists(pdf_path):
                resume_text = self.pdf_processor.extract_text_from_pdf(pdf_path)
            elif text:
                resume_text = text
            else:
                return {
                    'success': False,
                    'error': 'Either pdf_path or text must be provided',
                    'message': 'No input provided for entity extraction'
                }
            
            # Extract entities using NER model
            if self.ner_service:
                ner_result = self.ner_service.extract_entities(resume_text)
                
                if ner_result['success']:
                    # Enhance with summary
                    summary = self.ner_service.get_entity_summary(ner_result['entities'])
                    
                    return {
                        'success': True,
                        'entities': ner_result['entities'],
                        'summary': summary,
                        'model_used': ner_result['model_used'],
                        'message': f"Extracted {summary['total_entities']} entities of {summary['entity_types']} types"
                    }
                else:
                    return ner_result
            else:
                return {
                    'success': False,
                    'error': 'NER service not available',
                    'message': 'Resume NER model not loaded'
                }
                
        except Exception as e:
            logger.error(f"Error extracting resume entities: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to extract entities from resume'
            }
    
    def get_structured_resume_info(self, pdf_path: str = None) -> Dict[str, Any]:
        """
        Get both vector search capability and structured NER information
        
        Args:
            pdf_path: Path to resume PDF
            
        Returns:
            Combined information from vector database and NER extraction
        """
        try:
            result = {
                'success': True,
                'vector_stats': {},
                'structured_entities': {},
                'message': 'Resume information retrieved successfully'
            }
            
            # Get vector database stats
            vector_stats = self.get_resume_stats()
            if vector_stats['success']:
                result['vector_stats'] = vector_stats['stats']
            
            # Extract structured entities if PDF path provided
            if pdf_path:
                entity_result = self.extract_resume_entities(pdf_path=pdf_path)
                if entity_result['success']:
                    result['structured_entities'] = entity_result['entities']
                    result['entity_summary'] = entity_result['summary']
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting structured resume info: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve structured resume information'
            }
    
    def answer_with_entity_context(self, question: str, pdf_path: str = None) -> Dict[str, Any]:
        """
        Enhanced answering using both vector search and entity extraction
        
        Args:
            question: User's question
            pdf_path: Path to resume PDF for entity extraction
            
        Returns:
            Enhanced answer with entity context
        """
        try:
            # Get standard RAG answer
            rag_result = self.answer_question_with_llm(question, n_results=3)
            
            if not rag_result['success']:
                return rag_result
            
            # Enhance with entity information if available
            if self.ner_service and pdf_path and os.path.exists(pdf_path):
                entity_result = self.extract_resume_entities(pdf_path=pdf_path)
                
                if entity_result['success']:
                    # Add entity context to the answer
                    entities = entity_result['entities']
                    
                    # Check if question relates to specific entity types
                    entity_context = self._get_relevant_entities(question, entities)
                    
                    if entity_context:
                        enhanced_answer = f"{rag_result['answer']}\n\nStructured Information: {entity_context}"
                        rag_result['answer'] = enhanced_answer
                        rag_result['entities_used'] = entity_context
                        rag_result['enhancement'] = 'NER_enhanced'
            
            return rag_result
            
        except Exception as e:
            logger.error(f"Error in enhanced answering: {e}")
            # Fall back to standard RAG
            return self.answer_question_with_llm(question, n_results=3)
    
    def _get_relevant_entities(self, question: str, entities: Dict[str, List[str]]) -> str:
        """Get relevant entity information based on question context"""
        question_lower = question.lower()
        relevant_info = []
        
        if any(word in question_lower for word in ['skill', 'technology', 'programming', 'language']):
            if 'Technical Skill' in entities:
                relevant_info.append(f"Skills: {', '.join(entities['Technical Skill'])}")
            if 'Technical Skills' in entities:
                relevant_info.append(f"Skills: {', '.join(entities['Technical Skills'])}")
            if 'Programming Language' in entities:
                relevant_info.append(f"Languages: {', '.join(entities['Programming Language'])}")
            if 'Programming Languages' in entities:
                relevant_info.append(f"Languages: {', '.join(entities['Programming Languages'])}")
        
        if any(word in question_lower for word in ['contact', 'email', 'phone', 'reach']):
            if 'Email Address' in entities:
                relevant_info.append(f"Email: {', '.join(entities['Email Address'])}")
            if 'Email Addresses' in entities:
                relevant_info.append(f"Email: {', '.join(entities['Email Addresses'])}")
            if 'Phone Number' in entities:
                relevant_info.append(f"Phone: {', '.join(entities['Phone Number'])}")
            if 'Phone Numbers' in entities:
                relevant_info.append(f"Phone: {', '.join(entities['Phone Numbers'])}")
        
        if any(word in question_lower for word in ['education', 'degree', 'college', 'university']):
            if 'Educational Institution' in entities:
                relevant_info.append(f"Institutions: {', '.join(entities['Educational Institution'])}")
            if 'Educational Institutions' in entities:
                relevant_info.append(f"Institutions: {', '.join(entities['Educational Institutions'])}")
            if 'Academic Degree' in entities:
                relevant_info.append(f"Degrees: {', '.join(entities['Academic Degree'])}")
            if 'Academic Degrees' in entities:
                relevant_info.append(f"Degrees: {', '.join(entities['Academic Degrees'])}")
            if 'Degree' in entities:
                relevant_info.append(f"Degrees: {', '.join(entities['Degree'])}")
        
        if any(word in question_lower for word in ['work', 'job', 'position', 'company', 'organization']):
            if 'Organization' in entities:
                relevant_info.append(f"Companies: {', '.join(entities['Organization'])}")
            if 'Organizations/Companies' in entities:
                relevant_info.append(f"Companies: {', '.join(entities['Organizations/Companies'])}")
            if 'Job Title' in entities:
                relevant_info.append(f"Positions: {', '.join(entities['Job Title'])}")
            if 'Job Titles/Positions' in entities:
                relevant_info.append(f"Positions: {', '.join(entities['Job Titles/Positions'])}")
            if 'Designation' in entities:
                relevant_info.append(f"Positions: {', '.join(entities['Designation'])}")
        
        return '; '.join(relevant_info) if relevant_info else ""
    
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
