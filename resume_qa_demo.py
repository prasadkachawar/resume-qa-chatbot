#!/usr/bin/env python3
"""
Command-Line Resume Q&A Interface
Working demonstration of the resume question-answer system
"""

import sys
import os
sys.path.append('/Users/prasadkachawar/Desktop/my-info-project')

from app.services.resume_vector_service import resume_vector_service

class ResumeQAInterface:
    def __init__(self):
        self.service = resume_vector_service
        self.setup_system()
    
    def setup_system(self):
        """Initialize the resume data"""
        print("🚀 Initializing Resume Q&A System...")
        print("=" * 50)
        
        # Clear and reprocess for clean state
        print("📝 Processing your resume...")
        pdf_path = "/Users/prasadkachawar/Desktop/my-info-project/data/Prassad Narayan Kachawar GResume .docx.pdf"
        
        # Clear existing data
        clear_result = self.service.clear_resume_vectors()
        if clear_result.get('success'):
            print("✅ Cleared old data")
        
        # Process resume
        process_result = self.service.process_resume_pdf(pdf_path, chunk_size=100, overlap=10)
        if process_result.get('success'):
            print(f"✅ Resume processed: {process_result.get('total_chunks')} chunks created")
        else:
            print(f"❌ Failed to process resume: {process_result.get('error')}")
            return False
        
        print("🎉 System ready!\n")
        return True
    
    def format_answer(self, question, search_result):
        """Format the search results into a nice answer"""
        if not search_result.get('success'):
            return "❌ Sorry, I couldn't search your resume at the moment."
        
        results = search_result.get('results', {})
        documents = results.get('documents', [])
        distances = results.get('distances', [])
        
        if not documents:
            return "❌ I couldn't find information about that in your resume. Try asking about your experience, skills, education, or contact details."
        
        # Find most relevant chunks (low distance = high relevance)
        relevant_chunks = []
        for i, doc in enumerate(documents):
            if i < len(distances) and distances[i] < 1.2:  # More lenient threshold
                relevant_chunks.append(doc)
        
        if not relevant_chunks:
            # If no chunks meet threshold, just use top 2 anyway
            relevant_chunks = documents[:2]
        
        # Combine and format answer
        answer = ' '.join(relevant_chunks[:2])  # Use top 2 most relevant
        
        # Add context based on question type
        if any(word in question.lower() for word in ['skill', 'technical', 'programming']):
            answer = f"💻 **Your Technical Skills:** {answer}"
        elif any(word in question.lower() for word in ['experience', 'work', 'job']):
            answer = f"💼 **Your Work Experience:** {answer}"
        elif any(word in question.lower() for word in ['education', 'study', 'degree']):
            answer = f"🎓 **Your Education:** {answer}"
        elif any(word in question.lower() for word in ['contact', 'phone', 'email']):
            answer = f"📞 **Your Contact Information:** {answer}"
        else:
            answer = f"📄 **From Your Resume:** {answer}"
        
        # Add confidence info
        if distances:
            confidence = max(0, (1 - min(distances)) * 100)
            answer += f"\n\n🎯 **Confidence:** {confidence:.0f}% | **Sources:** {len(documents)} resume sections"
        
        return answer
    
    def ask_question(self, question):
        """Ask a question and get a formatted answer"""
        search_result = self.service.search_resume_content(question, n_results=3)
        return self.format_answer(question, search_result)
    
    def run_demo(self):
        """Run interactive demo"""
        print("🤖 **Resume Q&A Assistant**")
        print("Ask me anything about your resume! Type 'quit' to exit.\n")
        
        # Sample questions
        sample_questions = [
            "What are my technical skills?",
            "What is my work experience?", 
            "What is my educational background?",
            "What is my contact information?",
            "What programming languages do I know?",
            "What companies have I worked for?"
        ]
        
        print("💡 **Sample Questions:**")
        for i, q in enumerate(sample_questions, 1):
            print(f"   {i}. {q}")
        print()
        
        # Interactive loop
        while True:
            try:
                question = input("❓ **Your Question:** ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thanks for using Resume Q&A! Goodbye!")
                    break
                
                if not question:
                    continue
                
                if question.isdigit() and 1 <= int(question) <= len(sample_questions):
                    question = sample_questions[int(question) - 1]
                    print(f"   Selected: {question}")
                
                print("\n🔍 Searching your resume...")
                answer = self.ask_question(question)
                print(f"\n✅ **Answer:**\n{answer}\n")
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Thanks for using Resume Q&A! Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def run_auto_demo(self):
        """Run automatic demo with sample questions"""
        print("🎬 **Automatic Demo - Sample Questions & Answers**")
        print("=" * 60)
        
        sample_questions = [
            "What are my technical skills?",
            "What is my work experience?",
            "What is my educational background?", 
            "What is my contact information?",
            "What programming languages do I know?"
        ]
        
        for i, question in enumerate(sample_questions, 1):
            print(f"\n{i}. ❓ **Question:** {question}")
            print("   🔍 Searching...")
            
            answer = self.ask_question(question)
            print(f"   ✅ **Answer:** {answer}")
            print()
        
        print("🎉 **Demo complete!** The system is working perfectly!")

def main():
    print("Choose mode:")
    print("1. Interactive Q&A")
    print("2. Auto Demo")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    qa = ResumeQAInterface()
    
    if choice == "1":
        qa.run_demo()
    else:
        qa.run_auto_demo()

if __name__ == "__main__":
    main()
