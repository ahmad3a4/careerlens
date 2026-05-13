# CareerLens - CV Matcher Platform

> AI-powered career matching system that analyzes CVs, identifies skill gaps, and matches candidates with job opportunities.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick Start (Docker - Recommended)](#quick-start-docker--recommended)
- [Alternative: Local Setup](#alternative-local-setup)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)

## ✨ Features

- **CV Parsing**: Extract and structure data from CVs (PDF, DOCX)
- **Job Matching**: Find relevant job opportunities based on skills
- **Skill Gap Analysis**: Identify missing skills with scores
- **PDF Reports**: Generate comprehensive career reports
- **DOCX Export**: Export matched jobs in editable format
- **Career Roadmaps**: Get personalized learning paths
- **Background Jobs**: Automatic job search scheduling
- **User Preferences**: Save custom search criteria and notifications

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Database**: SQLAlchemy (supports SQLite, PostgreSQL, MySQL)
- **AI Models**: Sentence Transformers, Google Gemini API
- **Job Search**: RapidAPI
- **Document Processing**: python-docx, ReportLab
- **API Gateway**: OpenRouter (for LLM access)

## 📦 Prerequisites

Before you start, ensure you have:

### For Docker Setup (Recommended):
- **Docker** (v20.10+) - [Install Docker](https://docs.docker.com/get-docker/)
- **Docker Compose** (v1.29+) - Usually included with Docker Desktop

### For Local Setup:
- **Python** 3.11+ - [Install Python](https://www.python.org/downloads/)
- **pip** (comes with Python)
- **Git** (optional, for cloning the repo)

### API Keys (Required for Both):
1. **OpenRouter API Key** - [Get it here](https://openrouter.ai/keys)
2. **RapidAPI Key** - [Get it here](https://rapidapi.com/subscribe)
3. **Database URL** (optional - SQLite is default)

---

## 🚀 Quick Start (Docker - Recommended)

### Step 1: Clone or Download the Project

```bash
git clone <repository-url>
cd cv_matcher_V2
```

### Step 2: Create Environment File

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
OPENROUTER_API_KEY=your_key_here
RAPID_API_KEY=your_key_here
DATABASE_URL=sqlite:///./cv_matcher.db
```

**Getting Your API Keys:**

- **OpenRouter**: Visit https://openrouter.ai/keys, sign up, create an API key
- **RapidAPI**: Visit https://rapidapi.com, sign up, find job search APIs, get your key
- **Database**: Use the default SQLite or configure PostgreSQL/MySQL

### Step 3: Build and Run with Docker Compose

```bash
# Build the image (first time only)
docker-compose build

# Start the application
docker-compose up -d

# View logs
docker-compose logs -f careerlens
```

### Step 4: Access the Application

- **API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

### Step 5: Verify It's Running

```bash
# Check container status
docker-compose ps

# Test the API
curl http://localhost:8000/health
```

### Useful Docker Commands

```bash
# Stop the application
docker-compose down

# Remove everything (images, volumes, etc.)
docker-compose down -v

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Access container shell
docker exec -it careerlens-api bash

# View real-time logs
docker-compose logs -f

# View only errors
docker-compose logs --tail=100 careerlens | grep ERROR
```

---

## 🔧 Alternative: Local Setup

### Step 1: Clone or Download the Project

```bash
git clone <repository-url>
cd cv_matcher_V2
```

### Step 2: Create Virtual Environment

**On Windows (PowerShell):**
```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# If you get execution policy error, run:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

**On macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your API keys
# - OPENROUTER_API_KEY
# - RAPID_API_KEY
# - DATABASE_URL (optional, defaults to SQLite)
```

### Step 5: Run the Application

```bash
# From the project root directory
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 6: Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Logs**: Check terminal output

### Stopping the Local Server

Press `Ctrl+C` in the terminal where the server is running.

---

## ⚙️ Configuration

### Environment Variables

All configuration is done through the `.env` file. Here's what each variable does:

```env
# ============ REQUIRED ============

# Your OpenRouter API key (for LLM access)
OPENROUTER_API_KEY=sk_...

# Your RapidAPI key (for job search API)
RAPID_API_KEY=...

# Database connection string
DATABASE_URL=sqlite:///./cv_matcher.db
# Alternatives:
# DATABASE_URL=postgresql://user:pass@localhost:5432/cv_matcher
# DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/cv_matcher

# ============ OPTIONAL ============

# LLM Model (defaults to openai/gpt-4o-mini)
OPENROUTER_MODEL=openai/gpt-4o-mini

# OpenRouter Base URL (defaults to https://openrouter.ai/api/v1)
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# HTTP Referer (optional but recommended for rate limiting)
OPENROUTER_HTTP_REFERER=localhost

# App title (defaults to CareerLens)
OPENROUTER_APP_TITLE=CareerLens
```

### Database Configuration

**SQLite (Default - No Setup Required):**
```env
DATABASE_URL=sqlite:///./cv_matcher.db
```

**PostgreSQL:**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/cv_matcher_db
```

**MySQL:**
```env
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/cv_matcher_db
```

---

## 🔌 API Endpoints

### Health Check
```
GET /health
```

### CV Analysis
```
POST /upload
- Accepts: PDF, DOCX files
- Extracts: Skills, experience, education
```

### Job Search
```
POST /search-jobs
- Query: Job title or skills
- Returns: List of matching jobs
```

### Scoring
```
POST /score
- Compares CV with job description
- Returns: Match score (0-100)
```

### Roadmap
```
POST /roadmap
- Generates: Learning path for skill gaps
- Returns: Structured roadmap
```

### PDF/DOCX Export
```
POST /export-pdf
POST /export-docx
- Generates: Formatted reports
```

For complete API documentation, visit: http://localhost:8000/docs

---

## 🐛 Troubleshooting

### Docker Issues

#### Container won't start
```bash
# Check logs for errors
docker-compose logs careerlens

# Common causes:
# 1. Missing .env file - Create it with: cp .env.example .env
# 2. Invalid API keys - Check .env file
# 3. Port 8000 already in use - Change in docker-compose.yml
```

#### Port 8000 already in use
```bash
# Change the port in docker-compose.yml:
# ports:
#   - "8001:8000"  # Use 8001 instead

docker-compose up -d
```

#### API key errors
```bash
# Verify your .env file has:
OPENROUTER_API_KEY=your_actual_key_not_placeholder
RAPID_API_KEY=your_actual_key_not_placeholder

# Restart the container
docker-compose restart careerlens
```

### Local Setup Issues

#### Module not found error
```bash
# Ensure virtual environment is activated:
# Windows: .\venv\Scripts\Activate.ps1
# macOS/Linux: source venv/bin/activate

# Reinstall dependencies:
pip install -r requirements.txt --force-reinstall
```

#### Database locked error
```bash
# SQLite database is locked - delete and recreate:
rm cv_matcher.db
# Restart the application
```

#### Permission denied (UNIX)
```bash
# Grant execute permission:
chmod +x venv/bin/activate
source venv/bin/activate
```

### API Issues

#### 422 Unprocessable Entity
- Check request body format in API docs
- Ensure file uploads are correct type (PDF, DOCX)

#### 429 Too Many Requests
- You've hit API rate limits
- Increase OPENROUTER_HTTP_REFERER in .env
- Wait before retrying

#### Invalid API Key
```bash
# Verify keys are correct in .env:
# 1. OpenRouter: https://openrouter.ai/keys
# 2. RapidAPI: https://rapidapi.com/my-apps
```

---

## 📁 Project Structure

```
cv_matcher_V2/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── core/
│   │   ├── config.py          # Configuration & environment variables
│   │   ├── database.py        # Database setup & models
│   │   └── llm.py             # LLM integration
│   └── services/
│       ├── cv_parser.py       # CV extraction
│       ├── job_search.py      # Job search API
│       ├── matcher.py         # Job matching logic
│       ├── scorer.py          # Scoring engine
│       ├── roadmap.py         # Learning roadmap generation
│       ├── pdf_generator.py   # PDF export
│       └── docx_generator.py  # DOCX export
├── Dockerfile                  # Docker image definition
├── docker-compose.yml         # Multi-container orchestration
├── requirements.txt           # Python dependencies
├── .env.example              # Example environment variables
├── .dockerignore             # Files to exclude from Docker
└── README.md                 # This file
```

---

## 📝 First Steps After Installation

1. **Access the API Documentation**
   - Open http://localhost:8000/docs in your browser

2. **Test the API**
   - Try the "Try it out" buttons in the Swagger docs
   - Upload a sample CV to test CV parsing

3. **Save Your Preferences**
   - Use the preferences endpoint to save job search criteria
   - Set up job alert intervals

4. **Monitor Logs**
   - Docker: `docker-compose logs -f`
   - Local: Check terminal output

---

## 🆘 Getting Help

If you encounter issues:

1. **Check the Troubleshooting section above**
2. **View logs** for detailed error messages
3. **Verify API keys** are correct and have available credits
4. **Ensure all prerequisites** are installed
5. **Check Docker/Python versions** meet requirements

---

**Last Updated**: May 12, 2026
**Version**: 1.0.0
