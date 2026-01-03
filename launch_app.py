#!/usr/bin/env python3
"""
One-Click Resume Q&A Launcher
Simple launcher that starts the app and opens it in your browser
"""

import subprocess
import time
import webbrowser
import signal
import sys
import os

class ResumeQALauncher:
    def __init__(self):
        self.project_dir = "/Users/prasadkachawar/Desktop/my-info-project"
        self.port = 5001
        self.url = f"http://localhost:{self.port}/resume-qa"
        self.flask_process = None
    
    def cleanup_existing_processes(self):
        """Kill any existing processes on the port"""
        try:
            subprocess.run(f"lsof -ti:{self.port} | xargs kill -9", 
                         shell=True, capture_output=True)
            print("🧹 Cleaned up existing processes")
        except:
            pass
    
    def start_flask_app(self):
        """Start the Flask application"""
        print("🔧 Starting Flask application...")
        
        # Change to project directory
        os.chdir(self.project_dir)
        
        # Start Flask app
        env = os.environ.copy()
        env['PORT'] = str(self.port)
        
        python_path = os.path.join(self.project_dir, '.venv', 'bin', 'python')
        
        self.flask_process = subprocess.Popen(
            [python_path, 'run.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        return self.flask_process.pid
    
    def wait_for_app(self, max_wait=10):
        """Wait for the Flask app to be ready"""
        print("⏳ Waiting for app to start...")
        
        for i in range(max_wait):
            try:
                import urllib.request
                urllib.request.urlopen(f"http://localhost:{self.port}/api/resume/stats", timeout=1)
                return True
            except:
                time.sleep(1)
                print(f"   Waiting... ({i+1}/{max_wait})")
        
        return False
    
    def open_browser(self):
        """Open the Q&A interface in browser"""
        print("🌐 Opening Resume Q&A interface in browser...")
        webbrowser.open(self.url)
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n⏹️  Shutting down...")
        if self.flask_process:
            self.flask_process.terminate()
            print("✅ Flask app stopped")
        sys.exit(0)
    
    def launch(self):
        """Main launch function"""
        print("🚀 Resume Q&A One-Click Launcher")
        print("=" * 40)
        
        # Setup signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # Step 1: Cleanup
            self.cleanup_existing_processes()
            
            # Step 2: Start Flask app
            pid = self.start_flask_app()
            print(f"✅ Flask app started (PID: {pid})")
            
            # Step 3: Wait for app to be ready
            if self.wait_for_app():
                print("✅ App is ready!")
                
                # Step 4: Open browser
                self.open_browser()
                
                print("\n🎉 Resume Q&A System is ready!")
                print("=" * 40)
                print(f"📱 Web Interface: {self.url}")
                print(f"🏠 Dashboard: http://localhost:{self.port}/")
                print("\n💡 You can now:")
                print("   • Ask questions about your resume")
                print("   • Click sample questions to get started") 
                print("   • Get instant intelligent answers")
                print("\n⏹️  Press Ctrl+C to stop the application")
                print("\n📊 Application is running...")
                
                # Keep running
                while True:
                    time.sleep(1)
                    
            else:
                print("❌ App failed to start within timeout")
                if self.flask_process:
                    self.flask_process.terminate()
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Error: {e}")
            if self.flask_process:
                self.flask_process.terminate()
            sys.exit(1)

if __name__ == "__main__":
    launcher = ResumeQALauncher()
    launcher.launch()
