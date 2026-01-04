"""
LLM Service for intelligent document assistance
Supports multiple LLM backends: Ollama, Hugging Face, OpenAI
"""
import os
import logging
from typing import List, Dict, Optional
import requests
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, backend='auto'):
        """
        Initialize LLM service with specified backend
        
        Args:
            backend (str): 'ollama', 'huggingface', 'openai', or 'auto'
        """
        self.backend = backend
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        self.ollama_url = "http://localhost:11434"
        
        # Initialize based on backend preference
        if backend == 'auto':
            self._auto_initialize()
        else:
            self._initialize_backend(backend)
    
    def _auto_initialize(self):
        """Automatically detect and initialize the best available backend"""
        # Try Ollama first (fastest for local)
        if self._check_ollama():
            logger.info("✅ Using Ollama backend")
            self.backend = 'ollama'
            return
        
        # Try Hugging Face (good for deployment)
        try:
            self._initialize_huggingface()
            logger.info("✅ Using Hugging Face backend")
            self.backend = 'huggingface'
            return
        except Exception as e:
            logger.warning(f"Hugging Face initialization failed: {e}")
        
        # Fallback to simple mode
        logger.info("⚠️ Using fallback mode (basic text processing)")
        self.backend = 'fallback'
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _initialize_backend(self, backend: str):
        """Initialize specific backend"""
        if backend == 'ollama':
            if not self._check_ollama():
                raise Exception("Ollama not available")
        elif backend == 'huggingface':
            self._initialize_huggingface()
        elif backend == 'openai':
            self._initialize_openai()
    
    def _initialize_huggingface(self):
        """Initialize Hugging Face model"""
        try:
            # Use a lightweight model for deployment
            model_name = "microsoft/DialoGPT-small"
            
            # Check if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            logger.info(f"Loading Hugging Face model: {model_name} on {device}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(model_name)
            
            if device == "cuda":
                self.model = self.model.to(device)
            
            # Add padding token if not present
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face: {e}")
            raise
    
    def _initialize_openai(self):
        """Initialize OpenAI (if API key provided)"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception("OpenAI API key not found")
        
        import openai
        openai.api_key = api_key
        self.openai_client = openai
    
    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate intelligent answer using available LLM
        
        Args:
            question (str): User's question
            context (str): Relevant context from resume
            
        Returns:
            str: Generated answer
        """
        try:
            if self.backend == 'ollama':
                return self._generate_ollama(question, context)
            elif self.backend == 'huggingface':
                return self._generate_huggingface(question, context)
            elif self.backend == 'openai':
                return self._generate_openai(question, context)
            else:
                return self._generate_fallback(question, context)
                
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_fallback(question, context)
    
    def _generate_ollama(self, question: str, context: str) -> str:
        """Generate using Ollama"""
        try:
            prompt = self._create_prompt(question, context)
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "llama2",  # or "mistral", "codellama"
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "max_tokens": 300
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            
        return self._generate_fallback(question, context)
    
    def _generate_huggingface(self, question: str, context: str) -> str:
        """Generate using Hugging Face model"""
        try:
            if not self.model or not self.tokenizer:
                return self._generate_fallback(question, context)
            
            prompt = self._create_prompt(question, context)
            
            # Tokenize input
            inputs = self.tokenizer.encode(
                prompt, 
                return_tensors="pt", 
                max_length=512, 
                truncation=True
            )
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 100,
                    temperature=0.7,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response
            response = self.tokenizer.decode(
                outputs[0][inputs.shape[1]:], 
                skip_special_tokens=True
            )
            
            return response.strip() if response.strip() else self._generate_fallback(question, context)
            
        except Exception as e:
            logger.error(f"Hugging Face generation failed: {e}")
            return self._generate_fallback(question, context)
    
    def _generate_openai(self, question: str, context: str) -> str:
        """Generate using OpenAI"""
        try:
            prompt = self._create_prompt(question, context)
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that answers questions about a resume based on the provided context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return self._generate_fallback(question, context)
    
    def _generate_fallback(self, question: str, context: str) -> str:
        """Fallback text processing when LLM is not available"""
        # Extract key information from context
        lines = context.split('\n')
        relevant_lines = []
        
        # Simple keyword matching
        question_words = question.lower().split()
        for line in lines:
            line_words = line.lower().split()
            if any(word in line_words for word in question_words):
                relevant_lines.append(line.strip())
        
        if relevant_lines:
            return f"Based on the resume: {' '.join(relevant_lines[:3])}"
        else:
            return f"Based on the available information: {context[:200]}..."
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create a well-formatted prompt for LLM"""
        return f"""Based on the following resume information, please answer the question clearly and concisely.

Resume Context:
{context}

Question: {question}

Answer:"""

    def get_available_models(self) -> List[str]:
        """Get list of available models based on backend"""
        if self.backend == 'ollama':
            try:
                response = requests.get(f"{self.ollama_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    return [model['name'] for model in data.get('models', [])]
            except:
                pass
        
        return [f"{self.backend} (active)"]
    
    def get_status(self) -> Dict:
        """Get current LLM service status"""
        return {
            "backend": self.backend,
            "status": "active" if self.backend != 'fallback' else "fallback",
            "models": self.get_available_models(),
            "capabilities": {
                "text_generation": self.backend != 'fallback',
                "context_aware": True,
                "local_processing": self.backend in ['ollama', 'huggingface']
            }
        }


# Global LLM service instance
llm_service = None

def get_llm_service() -> LLMService:
    """Get or create global LLM service instance"""
    global llm_service
    if llm_service is None:
        llm_service = LLMService(backend='auto')
    return llm_service


def initialize_llm_service(backend='auto'):
    """Initialize LLM service with specific backend"""
    global llm_service
    llm_service = LLMService(backend=backend)
    return llm_service
