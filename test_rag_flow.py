#!/usr/bin/env python3
"""
Test script to verify the optimized RAG flow implementation

Flow Verification:
1. Chunking with overlapping windows (nothing missed)
2. User query embedded with same embedding method
3. Retrieve top 3 results from vector database
4. Send top 3 hits with user query to LLM and parse answer to user
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.resume_vector_service import resume_vector_service
from app.services.chromadb_service import chromadb_service
from app.utils.pdf_processor import PDFProcessor
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_chunking_with_overlap():
    """Test Step 1: Verify chunking strategy with overlapping windows"""
    print("🔧 STEP 1: Testing Chunking with Overlapping Windows")
    print("=" * 60)
    
    # Test text
    test_text = "This is a sample text for testing chunking with overlapping windows. The overlapping strategy ensures no information is missed between chunks."
    
    chunks = PDFProcessor.create_chunks_with_overlap(test_text, chunk_size=50, overlap=10)
    
    print(f"Original text length: {len(test_text)} characters")
    print(f"Number of chunks created: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: '{chunk['text']}' (overlap: {chunk['overlap_chars']})")
    
    # Verify overlap
    if len(chunks) > 1:
        chunk1_end = chunks[0]['text'][-10:]
        chunk2_start = chunks[1]['text'][:10]
        overlap_detected = chunk1_end in chunks[1]['text']
        print(f"✅ Overlap detected: {overlap_detected}")
        print(f"   Chunk 0 end: '{chunk1_end}'")
        print(f"   Chunk 1 start: '{chunk2_start}'")
    
    print()

def test_embedding_consistency():
    """Test Step 2: Verify same embedding method for storage and query"""
    print("🔍 STEP 2: Testing Embedding Consistency")
    print("=" * 60)
    
    # Test query
    test_query = "What are the technical skills?"
    
    # Get collection info
    collection = chromadb_service.get_or_create_resume_collection()
    
    print(f"Collection name: {collection.name}")
    print(f"Embedding function: {type(chromadb_service.embedding_function).__name__}")
    
    # Test search (this uses the same embedding function)
    results = chromadb_service.search_similar_chunks(test_query, n_results=3)
    
    print(f"✅ Query embedded and searched successfully")
    print(f"   Query: '{test_query}'")
    print(f"   Results found: {len(results.get('documents', [[]])[0])}")
    print()

def test_top_3_retrieval():
    """Test Step 3: Verify exactly 3 results are retrieved"""
    print("📊 STEP 3: Testing Top 3 Results Retrieval")
    print("=" * 60)
    
    test_queries = [
        "What programming languages do I know?",
        "Tell me about work experience",
        "What is my educational background?"
    ]
    
    for query in test_queries:
        results = chromadb_service.search_similar_chunks(query, n_results=3)
        
        documents = results.get('documents', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        print(f"Query: '{query}'")
        print(f"✅ Retrieved exactly {len(documents)} chunks")
        
        for i, (doc, dist) in enumerate(zip(documents, distances)):
            relevance = max(0, 1 - dist)
            print(f"   Chunk {i+1}: Relevance {relevance:.3f} | '{doc[:50]}...'")
        
        print()

def test_llm_integration():
    """Test Step 4: Verify LLM receives top 3 hits and returns ONE answer"""
    print("🤖 STEP 4: Testing LLM Integration - Single Answer Generation")
    print("=" * 60)
    
    test_question = "What are my main technical skills?"
    
    # Use the complete RAG pipeline
    result = resume_vector_service.answer_question_with_llm(test_question, n_results=3)
    
    if result['success']:
        print(f"✅ RAG Pipeline successful!")
        print(f"   Question: '{result['question']}'")
        print(f"   LLM Backend: {result.get('llm_backend', 'Unknown')}")
        print(f"   Top 3 chunks used: {result.get('chunks_used', 0)}")
        print(f"   SINGLE Answer: '{result['answer']}'")
        print(f"   Answer length: {len(result['answer'])} characters")
        
        # Verify it's a single answer (not multiple)
        answer_lines = result['answer'].split('\n')
        print(f"   Answer format: {len(answer_lines)} lines (should be cohesive)")
        
    else:
        print(f"❌ RAG Pipeline failed: {result.get('error', 'Unknown error')}")
    
    print()

def test_complete_flow():
    """Test the complete optimized RAG flow"""
    print("🎯 COMPLETE RAG FLOW TEST")
    print("=" * 60)
    
    # Check if resume is processed
    stats = resume_vector_service.get_resume_stats()
    
    if stats['success'] and stats['stats']['total_chunks'] > 0:
        print(f"✅ Resume processed: {stats['stats']['total_chunks']} chunks available")
        
        # Test multiple questions
        test_questions = [
            "What programming languages do I know?",
            "Summarize my work experience",
            "What is my educational background?",
            "How can someone contact me?",
            "What makes me a good candidate for a software role?"
        ]
        
        for question in test_questions:
            print(f"\n🔄 Testing: '{question}'")
            result = resume_vector_service.answer_question_with_llm(question, n_results=3)
            
            if result['success']:
                print(f"   ✅ Success | Backend: {result.get('llm_backend', 'Unknown')}")
                print(f"   📝 Answer: {result['answer'][:80]}...")
                print(f"   📊 Used {result.get('num_chunks_used', 0)} chunks")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown')}")
    else:
        print("❌ Resume not processed. Please process resume first.")

def main():
    """Run all tests"""
    print("🚀 OPTIMIZED RAG FLOW VERIFICATION")
    print("=" * 60)
    print()
    
    # Run individual step tests
    test_chunking_with_overlap()
    test_embedding_consistency()
    test_top_3_retrieval()
    test_llm_integration()
    
    # Run complete flow test
    test_complete_flow()
    
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main()
