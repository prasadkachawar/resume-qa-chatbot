# 🤖 LLM Integration Guide

## Overview
Your Resume Q&A chatbot now supports multiple open-source LLM backends for intelligent document assistance!

## 🎯 **Supported LLM Backends**

### 1. **Ollama (Recommended for Local)**
- **Best for:** Local development and privacy
- **Models:** Llama2, Mistral, CodeLlama, Phi-3
- **Setup:**
  ```bash
  # Install Ollama
  curl -fsSL https://ollama.com/install.sh | sh
  
  # Pull a model (choose one)
  ollama pull llama2        # Good general model
  ollama pull mistral       # Fast and efficient
  ollama pull phi3:mini     # Smaller, faster
  ```
- **Usage:** Automatically detected when Ollama is running on localhost:11434

### 2. **Hugging Face Transformers (Good for Deployment)**
- **Best for:** Cloud deployment (Render, Railway, etc.)
- **Models:** DialoGPT-small (lightweight), GPT2, etc.
- **Setup:** Automatically installed via requirements.txt
- **Usage:** Fallback when Ollama not available

### 3. **OpenAI API (Optional)**
- **Best for:** Production with API budget
- **Models:** GPT-3.5-turbo, GPT-4
- **Setup:** Set `OPENAI_API_KEY` environment variable
- **Usage:** Premium option for best answers

## 🚀 **How It Works**

1. **Auto-Detection:** System automatically chooses the best available backend
2. **Intelligent Fallback:** If LLM fails, falls back to semantic search
3. **Context-Aware:** Uses ChromaDB search results as context for LLM
4. **Optimized Prompts:** Specially crafted prompts for resume Q&A

## 🔧 **API Endpoints**

### Enhanced Question Answering
```javascript
POST /api/resume/ask
{
    "question": "What programming languages do I know?",
    "n_results": 5
}
```

### LLM Status Check
```javascript
GET /api/llm/status
```

## 📊 **Performance Comparison**

| Backend | Speed | Quality | Privacy | Cost |
|---------|-------|---------|---------|------|
| Ollama | Fast | High | 100% | Free |
| HuggingFace | Medium | Good | High | Free |
| OpenAI | Fast | Highest | Low | Paid |

## 🛠️ **Local Development Setup**

### Option 1: Ollama (Recommended)
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a lightweight model
ollama pull phi3:mini

# Start your chatbot
python launch_app.py
```

### Option 2: Hugging Face Only
```bash
# Just start - it will auto-initialize HuggingFace
python launch_app.py
```

## 🌐 **Production Deployment**

### Render/Railway
- Uses Hugging Face backend automatically
- Lightweight models for fast startup
- No additional configuration needed

### Advanced Setup
```bash
# Set environment variables
export LLM_BACKEND=huggingface  # or ollama, openai
export OPENAI_API_KEY=your_key  # optional
```

## 🎯 **Sample Questions with LLM**

Try these enhanced questions:
- "Summarize my work experience in 2 sentences"
- "What makes me a good candidate for a Python developer role?"
- "List my technical skills in bullet points"
- "What's my educational background?"
- "How can someone contact me?"

## 🔍 **Technical Details**

- **Context Window:** Uses 5 most relevant resume chunks
- **Temperature:** 0.7 for balanced creativity/accuracy
- **Max Tokens:** 300 for concise answers
- **Fallback Chain:** LLM → Semantic Search → Simple Text Match

## 🚨 **Troubleshooting**

### LLM Not Working?
1. Check `/api/llm/status` endpoint
2. Look for "backend": "fallback" (means LLM failed)
3. Check logs for specific errors

### Ollama Issues?
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve
```

### Hugging Face Issues?
- Model downloads automatically on first use
- May take 1-2 minutes for first question
- Check available disk space (models ~500MB)

## 💡 **Tips for Best Results**

1. **Specific Questions:** "What Python frameworks do I know?" vs "Tell me about skills"
2. **Context Matters:** LLM uses resume chunks to provide accurate answers
3. **Model Choice:** Phi3:mini for speed, Llama2 for quality
4. **Fallback Ready:** System gracefully handles LLM failures
