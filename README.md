# InterviewIQ — AI Interview Simulator

InterviewIQ is an academic AI-powered interview simulator built with Python, FastAPI, and the official Groq Python SDK. It evaluates candidate responses against a rigorous, component-based rubric in real time using minimal tokens, purely in-memory session state, and zero persistent storage.

---

## Key Highlights & Architectural Guarantees

1. **Zero Persistence Guarantee**:
   - **No databases, no file-based storage, no SQLite, and no browser storage** (`localStorage`, `sessionStorage`, or cookies).
   - All interview sessions and evaluations exist exclusively in server memory (`app/state.py`).
   - When the server process restarts, all interview data vanishes immediately.

2. **Objective Python-Calculated Scoring**:
   - Final scores ($0\text{--}10$) are **computed in Python** from the sum of four rubric component scores rather than relying on LLM arithmetic:
     - **Technical Correctness**: $0\text{--}4$ points
     - **Relevance**: $0\text{--}2$ points
     - **Completeness**: $0\text{--}2$ points
     - **Clarity**: $0\text{--}2$ points
   - Evaluator recognizes alternative technically correct solutions, separates missing concepts from factual inaccuracies, and penalizes irrelevant verbosity.

3. **Confidentiality Pre-Submission**:
   - Questions are generated once at interview creation.
   - Expected concepts and reference answers are **never sent to the client** prior to answer submission.

4. **Comprehensive Performance Analytics**:
   - Total score and maximum score ($10 \times N$).
   - Average score out of $10$ and percentage score.
   - Criterion-by-criterion breakdown across all questions.
   - Highlight of highest-scoring and lowest-scoring answers.
   - Aggregated frequently missing concepts.
   - Three prioritized improvement recommendations.
   - Application-defined grading bands ($90\text{--}100\%$ Excellent, $75\text{--}89\%$ Good, $60\text{--}74\%$ Satisfactory, $40\text{--}59\%$ Needs Improvement, $<40\%$ Poor).

5. **Aesthetics & Motion**:
   - Responsive dark-mode interface with ambient SVG motion graphics.
   - Dynamic score meters with SVG stroke dash animations.
   - Pure vanilla JavaScript with zero external frontend libraries.

---

## Tech Stack

- **Backend**: Python 3.10+ / FastAPI
- **AI Engine**: Groq API via official `groq` Python SDK
- **Validation**: Pydantic v2
- **Frontend**: HTML5, Vanilla CSS3 (Custom design system), Vanilla JavaScript
- **Server**: Uvicorn
- **Testing**: pytest, pytest-asyncio, httpx

---

## Project Structure

```
interview-Sim/
├── app/
│   ├── main.py              # FastAPI application, static file mounts, routes
│   ├── config.py            # Environment configuration (groq_API / GROQ_API_KEY)
│   ├── state.py             # Thread-safe in-memory session store (no disk persistence)
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
│   │   ├── groq_service.py  # Groq API client with bounded retry & rubric prompt
│   │   └── report_service.py # Report analytics, grading bands, and recommendations
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoint
│   │   └── interviews.py    # Interview session endpoints
│   └── static/
│       ├── index.html       # Single-page application UI
│       ├── style.css        # Responsive dark theme with ambient motion graphics
│       └── app.js           # Client-side state manager (zero browser persistence)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Pytest fixtures and mock responses
│   ├── test_api.py          # API route tests (creation, validation, answers, results)
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

## Installation & Setup

### 1. Prerequisites
- Linux / macOS / Windows with Python 3.10 or higher.

### 2. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure `.env`
Create or edit `.env` in the root directory:
```env
# Groq API key (supports groq_API or GROQ_API_KEY)
groq_API=gsk_your_groq_api_key_here

# Groq model (tested and active: qwen/qwen3.8-27b)
GROQ_MODEL=qwen/qwen3.8-27b

# Server configuration
HOST=127.0.0.1
PORT=8000
```

---

## Running the Application

Launch the Uvicorn server:
```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Once started, open your web browser and navigate to:
```
http://127.0.0.1:8000/
```

Interactive API documentation (Swagger UI) is available at:
```
http://127.0.0.1:8000/docs
```

---

## Running Automated Tests

Run the full automated test suite with pytest:
```bash
source .venv/bin/activate
pytest -v
```

All 24 automated tests run completely offline by mocking Groq API calls, consuming zero API credits and verifying:
- Successful interview creation and hiding secrets from responses.
- Validation bounds for categories, difficulties, and question counts ($5$, $10$, $15$).
- Strict Python arithmetic calculation of the final score from components.
- Prevention of duplicate answer submissions.
- Rejection of premature result queries prior to interview completion.
- Bounded retry and error translation for Groq rate limits ($429$) and timeouts ($504$).
- Verification that zero database files (`.db`, `.sqlite`) exist on disk.

---

## API Endpoints Reference

### 1. `GET /api/health`
Health check and active session count.
```bash
curl -X GET http://127.0.0.1:8000/api/health
```

### 2. `POST /api/interviews`
Initializes an interview session and generates questions once in server memory.
```bash
curl -X POST http://127.0.0.1:8000/api/interviews \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Python",
    "difficulty": "Intermediate",
    "question_count": 5
  }'
```

### 3. `GET /api/interviews/{interview_id}`
Retrieves current progress and question prompt.
```bash
curl -X GET http://127.0.0.1:8000/api/interviews/<interview_id>
```

### 4. `POST /api/interviews/{interview_id}/answers`
Evaluates a candidate answer against the 4-component rubric.
```bash
curl -X POST http://127.0.0.1:8000/api/interviews/<interview_id>/answers \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Python dictionaries use a hash table with open addressing and pseudo-random probing to resolve collisions. It resizes when load factor exceeds 2/3."
  }'
```

### 5. `GET /api/interviews/{interview_id}/results`
Retrieves the comprehensive final performance report once all questions are answered.
```bash
curl -X GET http://127.0.0.1:8000/api/interviews/<interview_id>/results
```
