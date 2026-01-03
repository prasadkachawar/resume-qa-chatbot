#!/usr/bin/env python3
"""
Fix Resume Q&A by clearing duplicates and reinitializing properly
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001/api"

def fix_resume_qa():
    print("🔧 Fixing Resume Q&A System")
    print("=" * 40)
    
    # Step 1: Clear existing data
    print("1. Clearing existing resume vectors...")
    try:
        response = requests.delete(f"{BASE_URL}/resume/clear")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Successfully cleared existing vectors")
            else:
                print(f"❌ Failed to clear: {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ Clear request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error clearing vectors: {e}")
        return False
    
    # Step 2: Reprocess resume with correct settings
    print("\n2. Processing resume with proper settings...")
    try:
        response = requests.post(f"{BASE_URL}/resume/process", json={
            "chunk_size": 100,
            "overlap": 10
        })
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ Resume processed successfully!")
                print(f"   📊 Total chunks: {result.get('total_chunks', 'N/A')}")
                print(f"   📄 Total characters: {result.get('total_characters', 'N/A')}")
                print(f"   🔍 Sample chunk: {result.get('sample_chunk', 'N/A')[:80]}...")
            else:
                print(f"❌ Processing failed: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ Process request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error processing resume: {e}")
        return False
    
    # Step 3: Test search functionality
    print("\n3. Testing search functionality...")
    test_questions = [
        "What are my technical skills?",
        "What is my experience?", 
        "What is my education?",
        "contact information"
    ]
    
    for question in test_questions:
        print(f"\n   🔍 Testing: '{question}'")
        try:
            response = requests.post(f"{BASE_URL}/resume/search", json={
                "query": question,
                "n_results": 3
            })
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('results', {}).get('documents'):
                    docs = result['results']['documents']
                    print(f"   ✅ Found {len(docs)} relevant results")
                    if docs:
                        print(f"      📝 Top result: {docs[0][:60]}...")
                else:
                    print(f"   ❌ No results found")
                    print(f"      Response: {result}")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                print(f"      Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Small delay
    
    # Step 4: Check final stats
    print("\n4. Final system status...")
    try:
        response = requests.get(f"{BASE_URL}/resume/stats")
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                stats = result.get('stats', {})
                print(f"✅ System ready!")
                print(f"   📚 Collection: {stats.get('collection_name', 'N/A')}")
                print(f"   📊 Total chunks: {stats.get('total_chunks', 'N/A')}")
                print(f"   🤖 Model: {stats.get('embedding_model', 'N/A')}")
            else:
                print("❌ Stats retrieval failed")
        else:
            print(f"❌ Stats request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
    
    print("\n" + "=" * 40)
    print("🎉 Resume Q&A system should now be working!")
    print("🌐 Visit: http://localhost:5001/resume-qa")
    return True

if __name__ == "__main__":
    fix_resume_qa()
