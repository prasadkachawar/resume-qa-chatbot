#!/usr/bin/env python3
"""
Test script for ChromaDB and Resume Processing functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.resume_vector_service import resume_vector_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chromadb_connection():
    """Test ChromaDB connection and collection creation"""
    try:
        logger.info("Testing ChromaDB connection...")
        
        # Get collection stats
        stats = resume_vector_service.get_resume_stats()
        logger.info(f"ChromaDB Stats: {stats}")
        
        return stats['success']
        
    except Exception as e:
        logger.error(f"ChromaDB connection failed: {str(e)}")
        return False

def test_resume_processing():
    """Test processing the resume PDF"""
    try:
        logger.info("Testing resume processing...")
        
        # Path to the resume PDF
        pdf_path = os.path.join(os.path.dirname(__file__), 'data', 'Prassad Narayan Kachawar GResume .docx.pdf')
        logger.info(f"Looking for PDF at: {pdf_path}")
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            logger.error(f"Resume PDF not found at: {pdf_path}")
            return False
        
        # Process the resume with 100-character chunks and 10-character overlap
        result = resume_vector_service.process_resume_pdf(pdf_path, chunk_size=100, overlap=10)
        
        logger.info(f"Processing result: {result}")
        
        return result['success']
        
    except Exception as e:
        logger.error(f"Resume processing failed: {str(e)}")
        return False

def test_search_functionality():
    """Test searching the resume content"""
    try:
        logger.info("Testing search functionality...")
        
        # Test search queries
        test_queries = [
            "experience",
            "skills",
            "education",
            "projects"
        ]
        
        for query in test_queries:
            logger.info(f"Searching for: '{query}'")
            result = resume_vector_service.search_resume_content(query, n_results=3)
            
            if result['success']:
                logger.info(f"Found {result['results']['count']} results for '{query}'")
                if result['results']['documents']:
                    logger.info(f"Top result: {result['results']['documents'][0][:50]}...")
            else:
                logger.error(f"Search failed for '{query}': {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Search testing failed: {str(e)}")
        return False

def main():
    """Main test function"""
    logger.info("Starting ChromaDB Resume Processing Tests")
    logger.info("=" * 50)
    
    # Test 1: ChromaDB Connection
    logger.info("\n1. Testing ChromaDB Connection...")
    if test_chromadb_connection():
        logger.info("✅ ChromaDB connection successful")
    else:
        logger.error("❌ ChromaDB connection failed")
        return
    
    # Test 2: Resume Processing
    logger.info("\n2. Testing Resume Processing...")
    if test_resume_processing():
        logger.info("✅ Resume processing successful")
    else:
        logger.error("❌ Resume processing failed")
        return
    
    # Test 3: Search Functionality
    logger.info("\n3. Testing Search Functionality...")
    if test_search_functionality():
        logger.info("✅ Search functionality successful")
    else:
        logger.error("❌ Search functionality failed")
        return
    
    # Final stats
    logger.info("\n4. Final Statistics...")
    stats = resume_vector_service.get_resume_stats()
    if stats['success']:
        logger.info(f"Final stats: {stats['stats']}")
    
    logger.info("\n" + "=" * 50)
    logger.info("All tests completed successfully! 🎉")

if __name__ == "__main__":
    main()
