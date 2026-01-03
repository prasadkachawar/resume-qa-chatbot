import PyPDF2
import pypdf
import os
import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Utility class for processing PDF files and creating text chunks"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str, method: str = 'pypdf') -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to the PDF file
            method: 'pypdf' or 'PyPDF2' (default: 'pypdf')
            
        Returns:
            Extracted text as string
        """
        try:
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            text = ""
            
            if method == 'pypdf':
                with open(pdf_path, 'rb') as file:
                    reader = pypdf.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            
            elif method == 'PyPDF2':
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            
            else:
                raise ValueError(f"Unsupported extraction method: {method}")
            
            # Clean up the text
            text = PDFProcessor.clean_text(text)
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newline
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = text.strip()
        
        return text
    
    @staticmethod
    def create_chunks_with_overlap(text: str, chunk_size: int = 100, overlap: int = 10) -> List[Dict[str, Any]]:
        """
        Split text into chunks with specified overlap
        
        Args:
            text: Input text to chunk
            chunk_size: Size of each chunk in characters (default: 100)
            overlap: Number of overlapping characters (default: 10)
            
        Returns:
            List of dictionaries containing chunk data
        """
        try:
            if len(text) <= chunk_size:
                return [{
                    'text': text,
                    'chunk_index': 0,
                    'start_pos': 0,
                    'end_pos': len(text),
                    'chunk_size': len(text),
                    'overlap_chars': 0
                }]
            
            chunks = []
            start = 0
            chunk_index = 0
            
            while start < len(text):
                # Calculate end position
                end = min(start + chunk_size, len(text))
                
                # Extract chunk
                chunk_text = text[start:end]
                
                # Calculate overlap characters for this chunk
                overlap_chars = overlap if chunk_index > 0 else 0
                
                chunks.append({
                    'text': chunk_text,
                    'chunk_index': chunk_index,
                    'start_pos': start,
                    'end_pos': end,
                    'chunk_size': len(chunk_text),
                    'overlap_chars': overlap_chars,
                    'total_text_length': len(text)
                })
                
                # Move to next chunk position with overlap
                if end >= len(text):
                    break
                
                start = end - overlap
                chunk_index += 1
            
            logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
            return chunks
            
        except Exception as e:
            logger.error(f"Error creating chunks: {str(e)}")
            raise
    
    @staticmethod
    def process_pdf_to_chunks(pdf_path: str, chunk_size: int = 100, overlap: int = 10) -> Dict[str, Any]:
        """
        Complete pipeline: extract text from PDF and create chunks
        
        Args:
            pdf_path: Path to PDF file
            chunk_size: Size of each chunk in characters
            overlap: Number of overlapping characters
            
        Returns:
            Dictionary containing original text and chunks
        """
        try:
            # Extract text from PDF
            full_text = PDFProcessor.extract_text_from_pdf(pdf_path)
            
            # Create chunks
            chunks = PDFProcessor.create_chunks_with_overlap(full_text, chunk_size, overlap)
            
            # Extract just the text for each chunk
            chunk_texts = [chunk['text'] for chunk in chunks]
            
            # Prepare metadata for each chunk
            metadata = [{
                'chunk_index': chunk['chunk_index'],
                'start_pos': chunk['start_pos'],
                'end_pos': chunk['end_pos'],
                'chunk_size': chunk['chunk_size'],
                'overlap_chars': chunk['overlap_chars'],
                'source_file': os.path.basename(pdf_path),
                'total_chunks': len(chunks)
            } for chunk in chunks]
            
            result = {
                'original_text': full_text,
                'chunk_texts': chunk_texts,
                'chunk_metadata': metadata,
                'total_chunks': len(chunks),
                'total_characters': len(full_text),
                'chunk_size': chunk_size,
                'overlap': overlap,
                'source_file': pdf_path
            }
            
            logger.info(f"Successfully processed PDF into {len(chunks)} chunks")
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF to chunks: {str(e)}")
            raise
    
    @staticmethod
    def get_chunk_statistics(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the created chunks"""
        if not chunks:
            return {'total_chunks': 0}
        
        chunk_sizes = [chunk['chunk_size'] for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'min_chunk_size': min(chunk_sizes),
            'max_chunk_size': max(chunk_sizes),
            'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes),
            'total_characters': sum(chunk_sizes),
            'overlap_chars': chunks[0].get('overlap_chars', 0) if chunks else 0
        }

# Convenience functions
def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file"""
    return PDFProcessor.extract_text_from_pdf(pdf_path)

def create_text_chunks(text: str, chunk_size: int = 100, overlap: int = 10) -> List[str]:
    """Create overlapping text chunks"""
    chunks = PDFProcessor.create_chunks_with_overlap(text, chunk_size, overlap)
    return [chunk['text'] for chunk in chunks]

def process_resume_pdf(pdf_path: str, chunk_size: int = 100, overlap: int = 10) -> Dict[str, Any]:
    """Process resume PDF to chunks"""
    return PDFProcessor.process_pdf_to_chunks(pdf_path, chunk_size, overlap)
