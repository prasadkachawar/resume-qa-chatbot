#!/usr/bin/env python3
"""
Comprehensive Test Suite for Resume Q&A Application
Tests API endpoints, services, and overall functionality
"""
import sys
import os
import time
import requests
import json
sys.path.append('/Users/prasadkachawar/Desktop/my-info-project')

def test_api_endpoint():
    """Test the main Q&A API endpoint"""
    print("🔍 Testing API Endpoint...")
    
    try:
        url = 'http://localhost:5004/api/resume/ask'
        test_questions = [
            "What is my contact information?",
            "What are my technical skills?",
            "What work experience do I have?"
        ]
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Test {i}: {question}")
            
            response = requests.post(
                url, 
                json={'question': question}, 
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"✅ Success: {result.get('success', False)}")
                print(f"🤖 Backend: {result.get('llm_backend', 'Unknown')}")
                print(f"📚 Chunks: {result.get('chunks_used', 'Unknown')}")
                print(f"💬 Answer: {result.get('answer', 'No answer')[:100]}...")
                
                if not result.get('success'):
                    print(f"❌ Error: {result.get('error', 'Unknown')}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
        
        print(f"\n🎉 All API tests passed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Flask app not running on port 5004")
        return False
    except Exception as e:
        print(f"❌ API Test Error: {e}")
        return False

def test_service_layer():
    """Test the service layer directly"""
    print("\n🔧 Testing Service Layer...")
    
    try:
        from app.services.resume_vector_service import ResumeVectorService
        
        service = ResumeVectorService()
        print("✅ Service initialized")
        
        # Test question processing
        question = "What is my contact information?"
        result = service.answer_question_with_llm(question, n_results=3)
        
        print(f"✅ Question processed: {result.get('success', False)}")
        print(f"🤖 Backend: {result.get('llm_backend', 'Unknown')}")
        print(f"📚 Chunks: {result.get('chunks_used', 'Unknown')}")
        print(f"💬 Answer length: {len(result.get('answer', ''))} characters")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Service Test Error: {e}")
        return False

def test_ner_integration():
    """Test NER integration"""
    print("\n🧠 Testing NER Integration...")
    
    try:
        from app.services.resume_vector_service import ResumeVectorService
        
        service = ResumeVectorService()
        pdf_path = "data/Prassad Narayan Kachawar GResume .docx.pdf"
        
        # Test entity extraction
        entity_result = service.extract_resume_entities(pdf_path=pdf_path)
        
        print(f"✅ Entity extraction: {entity_result.get('success', False)}")
        print(f"📊 Total entities: {entity_result.get('summary', {}).get('total_entities', 0)}")
        
        entities = entity_result.get('entities', {})
        for entity_type, values in list(entities.items())[:3]:  # Show first 3
            if values:
                print(f"  • {entity_type}: {values}")
        
        # Test enhanced Q&A
        enhanced_result = service.answer_with_entity_context(
            "What is my contact information?", 
            pdf_path=pdf_path
        )
        
        print(f"✅ Enhanced Q&A: {enhanced_result.get('success', False)}")
        print(f"🚀 Enhancement: {enhanced_result.get('enhancement', 'standard')}")
        
        return entity_result.get('success', False) and enhanced_result.get('success', False)
        
    except Exception as e:
        print(f"❌ NER Test Error: {e}")
        return False

def test_database_stats():
    """Test database statistics"""
    print("\n📊 Testing Database Stats...")
    
    try:
        # Test via API
        response = requests.get('http://localhost:5004/api/resume/stats', timeout=10)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats API: {stats.get('success', False)}")
            print(f"📚 Total chunks: {stats.get('stats', {}).get('total_chunks', 0)}")
            print(f"🏗️ Collection exists: {stats.get('stats', {}).get('collection_exists', False)}")
            
            return stats.get('success', False)
        else:
            print(f"❌ Stats API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Database Stats Error: {e}")
        return False

def main():
    """Run comprehensive test suite"""
    print("🚀 Resume Q&A Application - Comprehensive Test Suite")
    print("=" * 60)
    print(f"🕐 Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Database Stats", test_database_stats),
        ("Service Layer", test_service_layer),
        ("NER Integration", test_ner_integration),
        ("API Endpoint", test_api_endpoint),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Final Summary
    print(f"\n{'='*60}")
    print("🎯 TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n📊 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Your Resume Q&A system is fully functional!")
        print("🌐 Access your application at: http://localhost:5004/resume-qa")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    print(f"🕐 Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return passed == total

if __name__ == "__main__":
    main()
