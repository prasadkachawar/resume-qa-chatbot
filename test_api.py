#!/usr/bin/env python3
"""
API Testing Script for ChromaDB Resume Processing
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001/api"

def test_api_endpoints():
    """Test all the resume processing API endpoints"""
    
    print("🧪 Testing ChromaDB Resume Processing API Endpoints")
    print("=" * 60)
    
    # Test 1: Process Resume
    print("\n1️⃣  Testing Resume Processing...")
    try:
        response = requests.post(f"{BASE_URL}/resume/process", 
                               json={
                                   "chunk_size": 100,
                                   "overlap": 10
                               })
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Resume processed successfully!")
            print(f"   📊 Total chunks: {result['total_chunks']}")
            print(f"   📄 Total characters: {result['total_characters']}")
            print(f"   🔍 Sample chunk: {result['sample_chunk'][:80]}...")
        else:
            print(f"❌ Processing failed: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure Flask app is running on localhost:5000")
        return
    
    # Test 2: Get Stats
    print("\n2️⃣  Testing Resume Statistics...")
    response = requests.get(f"{BASE_URL}/resume/stats")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Stats retrieved successfully!")
        print(f"   📚 Collection: {result['stats']['collection_name']}")
        print(f"   📊 Total chunks: {result['stats']['total_chunks']}")
    else:
        print(f"❌ Stats retrieval failed: {response.text}")
    
    # Test 3: Search Functionality
    print("\n3️⃣  Testing Search Functionality...")
    search_queries = [
        "experience with software development",
        "technical skills programming",
        "education engineering",
        "projects machine learning",
        "contact information"
    ]
    
    for query in search_queries:
        print(f"\n   🔍 Searching: '{query}'")
        response = requests.post(f"{BASE_URL}/resume/search", 
                               json={"query": query, "n_results": 2})
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Found {result['results']['count']} results")
            
            if result['results']['documents']:
                for i, doc in enumerate(result['results']['documents'][:2]):
                    distance = result['results']['distances'][i] if i < len(result['results']['distances']) else 'N/A'
                    print(f"      📝 Result {i+1}: {doc[:60]}... (distance: {distance:.3f})")
        else:
            print(f"   ❌ Search failed: {response.text}")
    
    # Test 4: Reprocess (clear and reload)
    print("\n4️⃣  Testing Reprocessing...")
    response = requests.post(f"{BASE_URL}/resume/reprocess", 
                           json={
                               "chunk_size": 50,  # Different chunk size for testing
                               "overlap": 5
                           })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Resume reprocessed with new settings!")
        print(f"   📊 New total chunks: {result['total_chunks']}")
        print(f"   ⚙️  New chunk size: {result['chunk_size']}")
    else:
        print(f"❌ Reprocessing failed: {response.text}")
    
    print("\n" + "=" * 60)
    print("🎉 API Testing Complete!")

if __name__ == "__main__":
    test_api_endpoints()
