#!/usr/bin/env python3
"""
Debug script to test resume Q&A functionality
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def test_resume_search():
    print("🔍 Testing Resume Search API")
    print("=" * 40)
    
    # Test questions
    questions = [
        "What are my technical skills?",
        "What is my experience?",
        "What is my education?",
        "contact information",
        "Prasad"
    ]
    
    for question in questions:
        print(f"\n❓ Testing: '{question}'")
        
        try:
            response = requests.post(f"{BASE_URL}/resume/search", 
                                   json={"query": question, "n_results": 3})
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Success: {result.get('success', False)}")
                
                if result.get('success') and result.get('results'):
                    results = result['results']
                    print(f"Documents found: {len(results.get('documents', []))}")
                    print(f"Total count: {results.get('count', 0)}")
                    
                    # Show actual results
                    if results.get('documents'):
                        for i, doc in enumerate(results['documents'][:2]):  # Show first 2
                            distance = results.get('distances', [None])[i]
                            print(f"  📄 Result {i+1}: {doc[:100]}...")
                            if distance is not None:
                                print(f"      Distance: {distance:.4f}")
                    else:
                        print("  ❌ No documents in results")
                else:
                    print("  ❌ No results or not successful")
                    print(f"  Raw response: {result}")
            else:
                print(f"  ❌ HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Also test stats
    print(f"\n📊 Testing Resume Stats:")
    try:
        response = requests.get(f"{BASE_URL}/resume/stats")
        if response.status_code == 200:
            result = response.json()
            print(f"Stats: {result}")
        else:
            print(f"Stats error: {response.text}")
    except Exception as e:
        print(f"Stats error: {e}")

if __name__ == "__main__":
    test_resume_search()
