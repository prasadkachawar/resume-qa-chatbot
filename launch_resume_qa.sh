#!/bin/bash

# Resume Q&A Launcher Script
# This script starts the Flask app and opens the Q&A interface in your browser

echo "🚀 Starting Resume Q&A System..."
echo "=================================="

# Change to the project directory
cd "/Users/prasadkachawar/Desktop/my-info-project"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Kill any existing Flask processes on port 5001
echo "🧹 Cleaning up any existing processes..."
lsof -ti:5001 | xargs kill -9 2>/dev/null || true

# Start Flask app in background
echo "🔧 Starting Flask application..."
PORT=5001 .venv/bin/python run.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Check if Flask started successfully
if ps -p $FLASK_PID > /dev/null; then
    echo "✅ Flask app started successfully (PID: $FLASK_PID)"
    
    # Open the Q&A interface in default browser
    echo "🌐 Opening Resume Q&A interface in browser..."
    open "http://localhost:5001/resume-qa"
    
    echo ""
    echo "🎉 Resume Q&A System is ready!"
    echo "=================================="
    echo "📱 Web Interface: http://localhost:5001/resume-qa"
    echo "🏠 Dashboard: http://localhost:5001/"
    echo ""
    echo "💡 You can now:"
    echo "   • Ask questions about your resume"
    echo "   • Click sample questions to get started"
    echo "   • Get instant intelligent answers"
    echo ""
    echo "⏹️  To stop the app: Press Ctrl+C or run 'kill $FLASK_PID'"
    echo ""
    
    # Keep the script running to show Flask logs
    echo "📊 Application logs:"
    echo "==================="
    wait $FLASK_PID
    
else
    echo "❌ Failed to start Flask app"
    exit 1
fi
