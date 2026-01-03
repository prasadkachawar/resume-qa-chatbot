# 🚀 Deploy Your Resume Q&A Chatbot

## Quick Deployment Guide

Your Resume Q&A chatbot is ready to deploy! Here's how to share it with your friend via a live link:

### Option 1: Render (Free & Recommended)

1. **Push to GitHub:**
   ```bash
   # First, create a new repository on GitHub.com
   # Then add it as remote:
   git remote add origin https://github.com/YOUR_USERNAME/my-info-project.git
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to [render.com](https://render.com) and sign up (free)
   - Connect your GitHub account
   - Click "New Web Service"
   - Select your repository
   - Use these settings:
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `python run.py`
     - **Environment:** Python 3
   - Click "Create Web Service"
   - Wait 5-10 minutes for deployment

3. **Share the link:**
   - You'll get a URL like: `https://your-app-name.onrender.com`
   - Share this with your friend!

### Option 2: Railway (Alternative)

1. Go to [railway.app](https://railway.app)
2. Connect GitHub and select your repo
3. It will auto-deploy your Flask app
4. Get shareable link

### Option 3: Heroku (Paid but Popular)

1. Install Heroku CLI
2. `heroku create your-app-name`
3. `git push heroku main`
4. Share the heroku URL

## 📋 Pre-Deployment Checklist

- ✅ All files committed to Git
- ✅ `Procfile` created for web service
- ✅ `requirements.txt` updated
- ✅ `.gitignore` configured
- ✅ App configured for production (host='0.0.0.0')

## 🌐 What Your Friend Will See

Once deployed, your friend can:
- Visit the live URL
- Ask questions about your resume
- Get intelligent AI-powered answers
- See the beautiful web interface
- Try sample questions

## 🔗 Sample Deployment Commands

```bash
# Step 1: Create GitHub repo and push
git remote add origin https://github.com/YOUR_USERNAME/resume-qa-bot.git
git push -u origin main

# Step 2: Deploy (choose one platform above)
# Step 3: Share the live URL with your friend!
```

## 💡 Tips for Sharing

- The live URL will look like: `https://your-resume-qa.onrender.com`
- Your friend can bookmark it
- It works on mobile and desktop
- No installation needed for your friend
- Your resume data is safely embedded in the vector database

## 🛡️ Privacy Note

Your resume content is processed into vector embeddings and stored in the ChromaDB. The original PDF is included in the deployment, so make sure you're comfortable sharing your resume information via this method.
