#!/usr/bin/env python3
"""
Resume Q&A Demo Script
Shows how the question-answer system works with sample questions
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:5001"

def test_qa_system():
    """Test the Resume Q&A system with sample questions"""
    
    print("🤖 Resume Q&A System Demo")
    print("=" * 50)
    
    # Sample questions to test
    questions = [
        "What is my experience in software development?",
        "What are my technical skills?", 
        "What is my educational background?",
        "What is my contact information?",
        "What programming languages do I know?",
        "What companies have I worked for?",
        "What projects have I worked on?",
        "What is my specialization?"
    ]
    
    # First, check if resume is processed
    print("\n1. Checking resume status...")
    try:
        response = requests.get(f"{BASE_URL}/api/resume/stats")
        if response.status_code == 200:
            result = response.json()
            if result['success'] and result['stats']['total_chunks'] > 0:
                print(f"✅ Resume ready: {result['stats']['total_chunks']} chunks available")
            else:
                print("⏳ Processing resume first...")
                # Process resume
                response = requests.post(f"{BASE_URL}/api/resume/process", 
                                       json={"chunk_size": 100, "overlap": 10})
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Resume processed: {result['total_chunks']} chunks created")
                else:
                    print("❌ Failed to process resume")
                    return
        else:
            print("❌ Cannot check resume status")
            return
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Flask app. Make sure it's running on localhost:5001")
        return
    
    print("\n2. Testing Q&A with sample questions...")
    print("-" * 50)
    
    for i, question in enumerate(questions, 1):
        print(f"\n❓ Question {i}: {question}")
        print("🤔 Searching...")
        
        try:
            response = requests.post(f"{BASE_URL}/api/resume/search", 
                                   json={"query": question, "n_results": 3})
            
            if response.status_code == 200:
                result = response.json()
                
                if result['success'] and result['results']['documents']:
                    # Generate a simple answer from the chunks
                    documents = result['results']['documents']
                    distances = result['results']['distances']
                    
                    # Find the most relevant chunks
                    relevant_chunks = []
                    for j, doc in enumerate(documents):
                        if j < len(distances) and distances[j] < 0.8:  # Filter relevant results
                            relevant_chunks.append(doc)
                    
                    if relevant_chunks:
                        answer = ' '.join(relevant_chunks[:2])  # Take top 2 chunks
                        answer = answer.strip()
                        
                        print(f"✅ Answer: {answer[:200]}{'...' if len(answer) > 200 else ''}")
                        print(f"📊 Found {len(documents)} relevant sections")
                        if distances:
                            confidence = max(0, (1 - min(distances)) * 100)
                            print(f"🎯 Confidence: {confidence:.0f}%")
                    else:
                        print("❌ No relevant information found")
                else:
                    print("❌ No results found")
            else:
                print(f"❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        # Small delay between questions
        time.sleep(0.5)
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")
    print(f"\n🌐 Open your browser and visit: {BASE_URL}/resume-qa")
    print("   to try the interactive Q&A interface!")

if __name__ == "__main__":
    test_qa_system()
