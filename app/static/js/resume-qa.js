// Resume Q&A JavaScript functionality

class ResumeQA {
    constructor() {
        this.apiBase = '/api/resume';
        this.chatContainer = document.getElementById('chatContainer');
        this.questionInput = document.getElementById('questionInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.typingIndicator = document.getElementById('typingIndicator');
        this.welcomeMessage = document.getElementById('welcomeMessage');
        
        // Initialize
        this.checkResumeStatus();
        this.questionInput.focus();
    }
    
    async checkResumeStatus() {
        try {
            const response = await fetch(`${this.apiBase}/stats`);
            const result = await response.json();
            
            const statusElement = document.getElementById('resume-status');
            const infoElement = document.getElementById('resume-info');
            
            if (result.success && result.stats.total_chunks > 0) {
                statusElement.textContent = 'Ready';
                statusElement.className = 'badge bg-success';
                infoElement.textContent = `${result.stats.total_chunks} chunks loaded and ready for questions`;
            } else {
                statusElement.textContent = 'Not Processed';
                statusElement.className = 'badge bg-warning';
                infoElement.textContent = 'Resume needs to be processed first';
                
                // Auto-process if not ready
                await this.processResume();
            }
        } catch (error) {
            console.error('Error checking resume status:', error);
            document.getElementById('resume-status').textContent = 'Error';
            document.getElementById('resume-status').className = 'badge bg-danger';
            document.getElementById('resume-info').textContent = 'Unable to check status';
        }
    }
    
    async processResume() {
        try {
            document.getElementById('resume-status').textContent = 'Processing...';
            document.getElementById('resume-status').className = 'badge bg-info';
            document.getElementById('resume-info').textContent = 'Processing your resume, please wait...';
            
            const response = await fetch(`${this.apiBase}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    chunk_size: 100,
                    overlap: 10
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                document.getElementById('resume-status').textContent = 'Ready';
                document.getElementById('resume-status').className = 'badge bg-success';
                document.getElementById('resume-info').textContent = `${result.total_chunks} chunks processed and ready`;
                
                this.addSystemMessage('🎉 Your resume has been processed and is ready for questions!', 'success');
            } else {
                throw new Error(result.message || 'Processing failed');
            }
        } catch (error) {
            console.error('Error processing resume:', error);
            document.getElementById('resume-status').textContent = 'Error';
            document.getElementById('resume-status').className = 'badge bg-danger';
            document.getElementById('resume-info').textContent = 'Processing failed';
            
            this.addSystemMessage('❌ Failed to process resume. Please try again.', 'error');
        }
    }
    
    async askQuestion(question = null) {
        const questionText = question || this.questionInput.value.trim();
        
        if (!questionText) {
            this.questionInput.focus();
            return;
        }
        
        // Clear input and disable send button
        if (!question) {
            this.questionInput.value = '';
        }
        this.sendBtn.disabled = true;
        
        // Hide welcome message if visible
        if (this.welcomeMessage.style.display !== 'none') {
            this.welcomeMessage.style.display = 'none';
        }
        
        // Add question bubble
        this.addQuestionBubble(questionText);
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Make API call
            const response = await fetch(`${this.apiBase}/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    query: questionText,
                    n_results: 3
                })
            });
            
            const result = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            if (result.success && result.results.documents.length > 0) {
                // Generate a contextual answer
                const answer = this.generateAnswer(questionText, result.results);
                this.addAnswerBubble(answer, result.results);
            } else {
                this.addAnswerBubble(
                    "I couldn't find specific information about that in your resume. Try asking about your experience, skills, education, or contact information.",
                    null
                );
            }
            
        } catch (error) {
            console.error('Error asking question:', error);
            this.hideTypingIndicator();
            this.addAnswerBubble(
                "Sorry, I encountered an error while searching your resume. Please try again.",
                null
            );
        } finally {
            // Re-enable send button and focus input
            this.sendBtn.disabled = false;
            this.questionInput.focus();
        }
    }
    
    generateAnswer(question, results) {
        const documents = results.documents;
        const distances = results.distances;
        
        // Find the most relevant chunks (lowest distance)
        const relevantChunks = documents
            .map((doc, index) => ({ doc, distance: distances[index] }))
            .filter(item => item.distance < 1.2) // More lenient threshold
            .sort((a, b) => a.distance - b.distance)
            .slice(0, 2) // Take top 2 most relevant
            .map(item => item.doc);
        
        if (relevantChunks.length === 0) {
            // If no chunks meet threshold, use top 2 anyway
            return documents.slice(0, 2).join(' ').trim();
        }
        
        // Combine the chunks into a coherent answer
        let answer = relevantChunks.join(' ').trim();
        
        // Clean up the answer
        answer = this.cleanAnswer(answer);
        
        // Add context based on question type
        if (question.toLowerCase().includes('skill')) {
            answer = this.formatSkillsAnswer(answer);
        } else if (question.toLowerCase().includes('experience') || question.toLowerCase().includes('work')) {
            answer = this.formatExperienceAnswer(answer);
        } else if (question.toLowerCase().includes('education')) {
            answer = this.formatEducationAnswer(answer);
        } else if (question.toLowerCase().includes('contact')) {
            answer = this.formatContactAnswer(answer);
        }
        
        return answer;
    }
    
    cleanAnswer(text) {
        // Remove excessive whitespace and clean up text
        return text
            .replace(/\s+/g, ' ')
            .replace(/([.!?])\s*([A-Z])/g, '$1 $2')
            .trim();
    }
    
    formatSkillsAnswer(answer) {
        if (answer.toLowerCase().includes('skill')) {
            return `Based on your resume, here are your technical skills: ${answer}`;
        }
        return `Here's what I found about your skills: ${answer}`;
    }
    
    formatExperienceAnswer(answer) {
        if (answer.toLowerCase().includes('experience')) {
            return `Your professional experience includes: ${answer}`;
        }
        return `Here's information about your work experience: ${answer}`;
    }
    
    formatEducationAnswer(answer) {
        if (answer.toLowerCase().includes('education') || answer.toLowerCase().includes('engineering')) {
            return `Your educational background: ${answer}`;
        }
        return `Here's your education information: ${answer}`;
    }
    
    formatContactAnswer(answer) {
        return `Your contact details: ${answer}`;
    }
    
    addQuestionBubble(question) {
        const questionDiv = document.createElement('div');
        questionDiv.className = 'question-bubble';
        questionDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <div class="flex-grow-1">
                    <strong>You:</strong><br>
                    ${this.escapeHtml(question)}
                </div>
                <i class="fas fa-user ms-2"></i>
            </div>
        `;
        
        this.chatContainer.appendChild(questionDiv);
        this.scrollToBottom();
    }
    
    addAnswerBubble(answer, results = null) {
        const answerDiv = document.createElement('div');
        answerDiv.className = 'answer-bubble';
        
        let sourceInfo = '';
        if (results && results.documents.length > 0) {
            const chunkCount = results.documents.length;
            const avgDistance = results.distances.reduce((a, b) => a + b, 0) / results.distances.length;
            const confidence = Math.max(0, (1 - avgDistance) * 100).toFixed(0);
            
            sourceInfo = `
                <div class="answer-source">
                    <i class="fas fa-info-circle me-1"></i>
                    Found in ${chunkCount} resume section${chunkCount > 1 ? 's' : ''} 
                    (${confidence}% confidence)
                </div>
            `;
        }
        
        answerDiv.innerHTML = `
            <div class="d-flex align-items-start">
                <i class="fas fa-robot me-2 text-primary" style="margin-top: 2px;"></i>
                <div class="flex-grow-1">
                    <strong class="text-primary">Resume Assistant:</strong><br>
                    ${this.escapeHtml(answer)}
                    ${sourceInfo}
                </div>
            </div>
        `;
        
        this.chatContainer.appendChild(answerDiv);
        this.scrollToBottom();
    }
    
    addSystemMessage(message, type = 'info') {
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${type} mx-3 my-2`;
        messageDiv.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            ${this.escapeHtml(message)}
        `;
        
        this.chatContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
    }
    
    scrollToBottom() {
        setTimeout(() => {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }, 100);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.askQuestion();
        }
    }
    
    askSampleQuestion(question) {
        this.questionInput.value = question;
        this.askQuestion();
    }
    
    clearChat() {
        // Remove all chat bubbles and alerts
        const bubbles = this.chatContainer.querySelectorAll('.question-bubble, .answer-bubble, .alert');
        bubbles.forEach(bubble => bubble.remove());
        
        // Show welcome message again
        this.welcomeMessage.style.display = 'block';
    }
    
    async reprocessResume() {
        if (confirm('This will clear existing data and reprocess your resume. Continue?')) {
            await this.processResume();
            this.addSystemMessage('Resume has been reprocessed successfully!', 'success');
        }
    }
}

// Global functions for template
function handleKeyPress(event) {
    window.resumeQA.handleKeyPress(event);
}

function askQuestion() {
    window.resumeQA.askQuestion();
}

function askSampleQuestion(question) {
    window.resumeQA.askSampleQuestion(question);
}

function checkResumeStatus() {
    window.resumeQA.checkResumeStatus();
}

function clearChat() {
    window.resumeQA.clearChat();
}

function reprocessResume() {
    window.resumeQA.reprocessResume();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    window.resumeQA = new ResumeQA();
});
