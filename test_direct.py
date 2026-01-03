#!/usr/bin/env python3
"""
Direct test of ChromaDB functionality without Flask app
"""

import sys
import os
sys.path.append('/Users/prasadkachawar/Desktop/my-info-project')

from app.services.resume_vector_service import resume_vector_service

def test_direct_search():
    """Test ChromaDB search functionality directly"""
    
    print("🧪 Direct ChromaDB Search Test")
    print("=" * 40)
    
    # Clear and reprocess
    print("1. Clearing old data...")
    clear_result = resume_vector_service.clear_resume_vectors()
    print(f"   Clear result: {clear_result}")
    
    print("\n2. Processing resume...")
    pdf_path = "/Users/prasadkachawar/Desktop/my-info-project/data/Prassad Narayan Kachawar GResume .docx.pdf"
    process_result = resume_vector_service.process_resume_pdf(pdf_path, chunk_size=100, overlap=10)
    print(f"   Process success: {process_result.get('success', False)}")
    if process_result.get('success'):
        print(f"   Total chunks: {process_result.get('total_chunks', 'N/A')}")
    
    print("\n3. Testing search...")
    test_questions = [
        "What are my technical skills?",
        "What is my experience?",
        "What is my education?",
        "contact information",
        "Prasad"
    ]
    
    for question in test_questions:
        print(f"\n   ❓ '{question}'")
        search_result = resume_vector_service.search_resume_content(question, n_results=3)
        
        if search_result.get('success'):
            results = search_result.get('results', {})
            documents = results.get('documents', [])
            print(f"   ✅ Found {len(documents)} results")
            
            if documents:
                for i, doc in enumerate(documents[:2]):  # Show first 2
                    print(f"      📝 {i+1}: {doc[:80]}...")
        else:
            print(f"   ❌ Search failed: {search_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_direct_search()
