# 🧭 PathFinder AI

> **AI-powered career navigation for underprivileged job seekers**  
> B.Tech Final Year Project · Python 3.11 · FastAPI · Google Gemini · spaCy · Sentence-BERT

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Folder Structure](#folder-structure)
4. [Prerequisites](#prerequisites)
5. [Step-by-Step Local Setup](#step-by-step-local-setup)
6. [Running the Server](#running-the-server)
7. [API Endpoints](#api-endpoints)
8. [Running Tests](#running-tests)
9. [Environment Variables Reference](#environment-variables-reference)
10. [Common Errors & Fixes](#common-errors--fixes)
11. [Tech Stack Summary](#tech-stack-summary)

---

## Project Overview

PathFinder AI bridges the gap between underprivileged job seekers and career opportunities by:

| Feature | Description |
|---|---|
| 📄 **Resume Parser** | Uploads a PDF, extracts text (PyPDF2), detects skills via spaCy NLP |
| 🎯 **Job Match Engine** | Compares resume skills to a job description using Sentence-BERT semantic similarity |
| 🤖 **XAI Feedback** | Google Gemini 2.5 Flash explains *why* skills matter and generates a free learning roadmap |
| 💼 **GitHub Portfolio** | Fetches public repositories via GitHub REST API v3 as portfolio evidence |
| 🎥 **YouTube Resources** | Finds free tutorial videos via YouTube Data API v3 for every skill gap |
| ✍️ **Corporate Translator** | Rewrites informal experience ("fixed computers for neighbours") into professional bullet points |

---

## System Architecture

```
React Frontend (port 3000)
        │
        │ HTTP/JSON
        ▼
  FastAPI Backend (port 8000)
  ┌─────────────────────────────┐
  │  routers/                   │
  │    resume.py                │
  │    jobs.py                  │
  │    feedback.py              │
  │    github.py                │
  │    youtube.py               │
  │    translator.py            │
  │                             │
  │  services/                  │
  │    pdf_parser  ← PyPDF2     │
  │    nlp_extractor ← spaCy    │
  │    similarity_engine ← SBERT│
  │    gemini_service ← Gemini  │
  │    github_service ← GH API │
  │    youtube_service ← YT API│
  │                             │
  │  MongoDB (motor async)      │
  └─────────────────────────────┘
```

---

## Folder Structure

```
pathfinder-ai/
│
├── main.py                  # FastAPI app entry point, CORS, lifespan
├── config.py                # Loads .env via pydantic-settings
├── requirements.txt         # All Python dependencies with pinned versions
├── .env.example             # Template for your .env file
├── .gitignore
├── README.md
│
├── routers/                 # One file per feature — URL routing only
│   ├── __init__.py
│   ├── resume.py            # POST /api/resume/upload
│   ├── jobs.py              # POST /api/jobs/match
│   ├── feedback.py          # POST /api/feedback/generate
│   ├── github.py            # GET  /api/github/portfolio/{username}
│   ├── youtube.py           # GET  /api/youtube/resources
│   └── translator.py        # POST /api/translator/translate
│
├── services/                # Business logic — no HTTP here
│   ├── __init__.py
│   ├── database.py          # MongoDB connect/disconnect helpers
│   ├── pdf_parser.py        # PyPDF2 text extraction
│   ├── nlp_extractor.py     # spaCy skill / education / experience extraction
│   ├── similarity_engine.py # Sentence-BERT cosine similarity
│   ├── gemini_service.py    # Gemini XAI feedback + Corporate Translator
│   ├── github_service.py    # GitHub REST API v3 wrapper
│   └── youtube_service.py   # YouTube Data API v3 wrapper
│
├── models/                  # Pydantic request / response schemas
│   ├── __init__.py
│   ├── resume.py
│   ├── job.py
│   ├── feedback.py
│   ├── github.py
│   ├── youtube.py
│   └── translator.py
│
├── utils/                   # Shared helpers
│   ├── __init__.py
│   ├── text_cleaner.py      # Unicode normalise, truncate, sentence split
│   └── validators.py        # GitHub username, PDF filename, skill list sanity
│
├── tests/                   # pytest test suite
│   ├── __init__.py
│   ├── test_health.py       # Smoke tests for /health and /
│   └── test_utils.py        # Unit tests for utility functions
│
└── uploads/                 # Auto-created at runtime — stores uploaded PDFs
```

---

## Prerequisites

Make sure you have the following installed **before** starting:

| Tool | Version | Check command |
|---|---|---|
| Python | 3.11.x | `python --version` |
| pip | latest | `pip --version` |
| Git | any | `git --version` |
| MongoDB | 6.x or 7.x | `mongod --version` |

> **MongoDB alternative**: You can use [MongoDB Atlas](https://www.mongodb.com/atlas) (free tier) instead of installing locally. Just copy the connection string into your `.env`.

---

## Step-by-Step Local Setup

### Step 1 — Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/pathfinder-ai.git
cd pathfinder-ai
```

### Step 2 — Create a Python Virtual Environment

A virtual environment keeps your project's packages separate from your system Python.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On macOS / Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt. ✅

### Step 3 — Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> ⏳ This will take 3–8 minutes the first time — PyTorch and sentence-transformers are large packages.

### Step 4 — Download the spaCy Language Model

```bash
python -m spacy download en_core_web_sm
```

### Step 5 — Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env
```

Now open `.env` in any text editor and fill in your API keys:

```
GEMINI_API_KEY=your_actual_gemini_key_here
GITHUB_TOKEN=your_actual_github_token_here
YOUTUBE_API_KEY=your_actual_youtube_key_here
```

**Where to get the API keys:**

| Key | Where to get it | Cost |
|---|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | Free tier available |
| `GITHUB_TOKEN` | [github.com/settings/tokens](https://github.com/settings/tokens) → New fine-grained token → `public_repo` read | Free |
| `YOUTUBE_API_KEY` | [console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → YouTube Data API v3 | Free quota |

### Step 6 — Start MongoDB

**Local MongoDB:**
```bash
# macOS (Homebrew)
brew services start mongodb-community

# Ubuntu / Debian
sudo systemctl start mongod

# Windows — start from Services or:
net start MongoDB
```

**OR** — if using MongoDB Atlas, just make sure `MONGODB_URL` in your `.env` points to your Atlas connection string.

### Step 7 — (Optional) Pre-download the Sentence-BERT Model

The model is downloaded automatically on first request, but you can pre-download it:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

---

## Running the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or simply:
```bash
python main.py
```

The server will start at **http://localhost:8000**

| URL | Description |
|---|---|
| http://localhost:8000/health | Health check — should return `{"status":"ok"}` |
| http://localhost:8000/docs | Swagger UI — interactive API documentation |
| http://localhost:8000/redoc | ReDoc — alternative API documentation |

---

## API Endpoints

### 🟢 System
| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |

### 📄 Resume
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/resume/upload` | Upload PDF → extract skills |

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/api/resume/upload" \
  -H "accept: application/json" \
  -F "file=@/path/to/your_resume.pdf"
```

### 🎯 Jobs
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/jobs/match` | Compare skills to job description |

**Example body:**
```json
{
  "resume_skills": ["python", "sql", "pandas"],
  "job_description": "Looking for a Data Analyst with Python, SQL, Tableau, Power BI..."
}
```

### 🤖 AI Feedback
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/feedback/generate` | Generate XAI feedback + learning roadmap |

### 💼 GitHub
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/github/portfolio/{username}` | Fetch GitHub repos |

**Example:**
```bash
curl "http://localhost:8000/api/github/portfolio/torvalds?limit=5"
```

### 🎥 YouTube
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/youtube/resources?skill=python+for+beginners` | Find tutorial videos |

### ✍️ Translator
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/translator/translate` | Rewrite informal experience |

**Example body:**
```json
{
  "informal_text": "i used to fix computers for my neighbours for money",
  "target_role": "IT Support Engineer"
}
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pip install pytest-cov
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `APP_ENV` | No | `development` | `development` or `production` |
| `APP_PORT` | No | `8000` | Port to run the server on |
| `SECRET_KEY` | Yes (prod) | placeholder | For JWT signing (future auth) |
| `ALLOWED_ORIGINS` | No | `http://localhost:3000` | CORS origins (comma-separated) |
| `MONGODB_URL` | No | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | No | `pathfinder_ai` | Database name |
| `GEMINI_API_KEY` | **Yes** | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model to use |
| `GITHUB_TOKEN` | Recommended | — | Raises GitHub rate limit from 60 to 5000 req/hr |
| `YOUTUBE_API_KEY` | **Yes** | — | YouTube Data API v3 key |
| `SPACY_MODEL` | No | `en_core_web_sm` | spaCy model name |
| `SBERT_MODEL` | No | `all-MiniLM-L6-v2` | Sentence-BERT model name |
| `MAX_UPLOAD_SIZE_MB` | No | `5` | PDF upload limit |

---

## Common Errors & Fixes

### ❌ `OSError: [E050] Can't find model 'en_core_web_sm'`
```bash
python -m spacy download en_core_web_sm
```

### ❌ `ModuleNotFoundError: No module named 'google.generativeai'`
```bash
pip install google-generativeai==0.8.3
```

### ❌ `Connection refused` (MongoDB)
Make sure MongoDB is running:
```bash
sudo systemctl start mongod     # Linux
brew services start mongodb-community  # macOS
```

### ❌ `GEMINI_API_KEY not set` / Gemini 403 error
Open `.env` and paste your real key for `GEMINI_API_KEY`.

### ❌ Port 8000 already in use
```bash
uvicorn main:app --reload --port 8001
```

### ❌ Slow first request
The Sentence-BERT model downloads (~90 MB) on first use. This is normal — subsequent requests are fast.

---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| **Backend Framework** | FastAPI 0.115 + Uvicorn |
| **PDF Parsing** | PyPDF2 3.0 |
| **NLP** | spaCy 3.8 (`en_core_web_sm`) |
| **Semantic Similarity** | Sentence-BERT (`all-MiniLM-L6-v2`) |
| **Generative AI** | Google Gemini 2.5 Flash |
| **Database** | MongoDB + Motor (async) |
| **External APIs** | GitHub REST API v3, YouTube Data API v3 |
| **Config Management** | pydantic-settings + python-dotenv |
| **Testing** | pytest + pytest-asyncio |
| **Frontend** *(separate)* | React.js + Tailwind CSS |

---

*Made with ❤️ for underprivileged job seekers across India.*