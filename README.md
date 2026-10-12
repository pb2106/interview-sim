# InterviewIQ — 1-on-1 AI Interview Simulator

InterviewIQ is an academic AI interview simulator built with Python, FastAPI, and the official Groq Python SDK. It provides an authentic 1-on-1 conversational interview experience with an AI interviewer ("Alex"). Candidate answers are evaluated against a fixed, 4-component rubric in real time using minimal tokens, purely in-memory session state, zero persistent storage, and downloadable PDF performance reports.

---

## 1. What InterviewIQ Does

1. **1-on-1 Conversational Interview Flow**:
   - The user selects an interview category (**Software Development**, **Python**, **SQL**, **Data Structures and Algorithms**, **General Engineering**, or **Behavioural**).
   - The user selects a difficulty (**Beginner**, **Intermediate**, or **Advanced**) and question count (**5**, **10**, or **15**).
   - The session initiates a live 1-on-1 chat stream with an AI interviewer persona ("Alex").
   - Questions are presented one by one as natural conversation prompts.

2. **Minimal After-Answer Feedback with Direct Answers**:
   - Feedback after each question is kept concise (1 to 2 short sentences) to maintain the realistic pace of an interview.
   - **Direct Right-Answer Disclosure**: If an answer is wrong or incomplete, the interviewer directly states the correct answer without writing long paragraphs or unnecessary explanations.
   - Candidates smoothly advance through questions using the **"Continue to Question N"** action in the chat stream.

3. **Objective Python-Calculated 10-Point Rubric**:
   - Every answer is scored on four criteria, and the final score ($0\text{--}10$) is **calculated strictly in Python** by summing the components (never trusting LLM arithmetic):
     - **Technical Correctness**: $0\text{--}4$ points
     - **Relevance**: $0\text{--}2$ points
     - **Completeness**: $0\text{--}2$ points
     - **Clarity**: $0\text{--}2$ points
   - The evaluator accepts alternative technically valid solutions, distinguishes incorrect facts from omitted details, does not reward filler verbosity, and calibrates scoring to the selected difficulty.

4. **Zero Persistence Guarantee**:
   - **No databases, no file-based storage, no SQLite, and no browser storage** (`localStorage`, `sessionStorage`, cookies, or IndexedDB).
   - All interview sessions and evaluations exist exclusively in server memory (`app/state.py`).
   - When the server process restarts, all interview data vanishes immediately.

5. **Pre-Submission Confidentiality**:
   - Questions are generated once at interview creation.
   - Expected concepts and reference answers are **never sent to the client** prior to answer submission.

6. **Comprehensive End-of-Interview PDF Report**:
   - When the interview concludes, candidates view a full performance dashboard and can download a formatted **PDF report** (`/api/interviews/{id}/pdf`) containing:
     - Overall score, percentage, and application-defined grade ($90\text{--}100\%$ Excellent, $75\text{--}89\%$ Good, $60\text{--}74\%$ Satisfactory, $40\text{--}59\%$ Needs Improvement, $<40\%$ Poor).
     - Breakdown across each of the 4 evaluation criteria.
     - Question-by-question review with candidate answers, component scores, and reference answers.
     - Frequently omitted technical concepts.
     - Three prioritized improvement recommendations.
     - Grading band notes and AI evaluation disclaimers.

7. **Zero Emojis**:
   - Clean, professional design with zero emojis across the interface, chat messages, and reports.

---

## 2. Tech Stack

- **Backend Framework**: Python 3.10+ / **FastAPI**
- **AI Engine**: **Groq API** via the official `groq` Python SDK
  - Tested & active model: `qwen/qwen3.8-27b` (configurable via `GROQ_MODEL`)
- **Validation**: **Pydantic v2** & `pydantic-settings`
- **PDF Engine**: **ReportLab** (Pure Python in-memory PDF generation)
- **Frontend**: **Vanilla HTML5, CSS3, JavaScript**
  - Zero external UI dependencies (no React, Tailwind, or CDNs)
  - Dark mode with ambient SVG motion graphics
  - Single-page application architecture
- **Web Server**: **Uvicorn**
- **Testing**: **pytest**, `pytest-asyncio`, `httpx` (26 automated tests passing offline)

---

## 3. Project Structure

```
interview-Sim/
├── app/
│   ├── main.py              # FastAPI application, static file mounts, routes
│   ├── config.py            # Environment configuration (groq_API / GROQ_API_KEY)
│   ├── state.py             # Thread-safe in-memory session store (zero persistence)
│   ├── models/
│   │   ├── __init__.py
│   │   └── interview.py     # Session, Question, and Answer dataclasses & enums
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── ai.py            # Pydantic schemas for Groq LLM validation
│   │   ├── request.py       # Pydantic request validation schemas
│   │   └── response.py      # Public API response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── groq_service.py  # Groq API client with bounded retry & minimal feedback prompt
│   │   ├── pdf_service.py   # PDF report generator using ReportLab
│   │   └── report_service.py # Report analytics, grading bands, and recommendations
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoint
│   │   └── interviews.py    # Interview session & PDF endpoints
│   └── static/
│       ├── index.html       # Single-page application 1-on-1 chatbot UI
│       ├── style.css        # Responsive dark theme with ambient motion graphics (zero emojis)
│       └── app.js           # Client-side chat manager (zero browser persistence)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and mock responses
│   ├── test_api.py          # API route tests (creation, validation, answers, PDF, results)
│   ├── test_evaluator.py    # Component scoring bounds, tiers, rate limits, timeouts
│   ├── test_report.py       # Python calculations, grading bands, recommendations
│   └── test_state.py        # In-memory isolation and zero disk persistence checks
├── .env                     # Private environment variables (contains Groq API key)
├── .env.example             # Example environment configuration
├── .gitignore               # Ignores .env, .venv, __pycache__, caches
├── requirements.txt         # Pinned Python package dependencies
└── README.md                # Project documentation
```

---

## 4. How to Start the Application

### Step 1: Clone & Navigate to Project
```bash
git clone git@github.com:pb2106/interview-sim.git
cd interview-sim
```

### Step 2: Set Up Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Ensure a `.env` file exists in the root directory:
```env
# Groq API key (supports groq_API or GROQ_API_KEY)
groq_API=gsk_your_groq_api_key_here

# Groq Model (tested and active: qwen/qwen3.8-27b)
GROQ_MODEL=qwen/qwen3.8-27b

# Server configuration
HOST=127.0.0.1
PORT=8000
```

### Step 5: Start the Server
```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Step 6: Open in Browser
- **Web App**: Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger API Docs**: Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 5. Running Automated Tests

Run the full automated test suite using `pytest`:
```bash
source .venv/bin/activate
pytest -v
```

All 26 automated tests execute completely offline by mocking Groq API calls, consuming zero API credits and verifying:
- Successful interview creation and hiding secrets from responses.
- Input validation bounds for categories, difficulties, and question counts ($5$, $10$, $15$).
- Strict Python arithmetic calculation of final score from components.
- Prevention of duplicate answer submissions.
- Sequential question navigation.
- Generation and download of the complete PDF report (`GET /api/interviews/{id}/pdf`).
- Premature query protection (cannot get results/PDF before completion).
- Bounded retry and error translation for Groq rate limits ($429$) and timeouts ($504$).
- Verification that zero database files (`.db`, `.sqlite`) exist on disk.

---

## 6. API Reference & Example Requests

### 1. Health Check
```bash
curl -X GET http://127.0.0.1:8000/api/health
```
**Response:**
```json
{
  "status": "ok",
  "app": "InterviewIQ",
  "model": "qwen/qwen3.8-27b",
  "active_in_memory_sessions": 0
}
```

### 2. Create Interview Session
```bash
curl -X POST http://127.0.0.1:8000/api/interviews \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Python",
    "difficulty": "Intermediate",
    "question_count": 5
  }'
```
**Response:**
```json
{
  "interview_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "category": "Python",
  "difficulty": "Intermediate",
  "total_questions": 5,
  "current_question_index": 0,
  "current_question": {
    "question_number": 1,
    "total_questions": 5,
    "question": "How does Python handle hash collisions in dictionaries?"
  }
}
```

### 3. Get Interview Progress
```bash
curl -X GET http://127.0.0.1:8000/api/interviews/<interview_id>
```

### 4. Submit Answer
```bash
curl -X POST http://127.0.0.1:8000/api/interviews/<interview_id>/answers \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Python dictionaries use open addressing with pseudo-random probing to resolve collisions. When load factor exceeds 2/3, the table resizes."
  }'
```
**Response:**
```json
{
  "question_number": 1,
  "user_answer": "Python dictionaries use open addressing...",
  "score": 10,
  "correctness_score": 4,
  "relevance_score": 2,
  "completeness_score": 2,
  "clarity_score": 2,
  "strengths": ["Accurately identifies open addressing and probing."],
  "weaknesses": [],
  "missing_concepts": [],
  "feedback": "Spot on. You accurately covered open addressing, probing, and the 2/3 load factor threshold.",
  "ideal_answer": "Python dictionaries use open addressing with pseudo-random probing...",
  "improvement_tip": "Keep providing precise numerical thresholds in system design questions.",
  "is_interview_completed": false,
  "next_question_index": 1
}
```

### 5. Get Final Performance Report (JSON)
```bash
curl -X GET http://127.0.0.1:8000/api/interviews/<interview_id>/results
```

### 6. Download Full Performance Report (PDF)
```bash
curl -X GET http://127.0.0.1:8000/api/interviews/<interview_id>/pdf -o interview_report.pdf
```
