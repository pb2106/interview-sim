import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.models.interview import (
    AnswerEvaluation,
    InterviewCategory,
    InterviewDifficulty,
    InterviewSession,
    InterviewStatus,
    Question,
)
from app.state import interview_store


# Predefined sample answers for testing different evaluation tiers
PREDEFINED_ANSWERS = {
    "correct": (
        "Python dictionaries use a hash table with open addressing to resolve hash collisions. "
        "When an index collides, pseudo-random probing searches for the next slot. "
        "To maintain O(1) average lookup complexity, CPython resizes and rehashes entries "
        "when the load factor exceeds 2/3."
    ),
    "partially_correct": (
        "Dictionaries use hash tables and probing for collisions. When full, they resize."
    ),
    "incorrect": (
        "Python dictionaries resolve collisions using binary search trees where keys are sorted alphabetically."
    ),
    "irrelevant": (
        "I really like Python because it has clean syntax and pandas is great for data analysis."
    ),
}


@pytest.fixture(autouse=True)
def clean_in_memory_store():
    """Ensure in-memory store is clean before and after every test."""
    interview_store.clear()
    yield
    interview_store.clear()


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


@pytest.fixture
def mock_questions():
    """Sample generated questions for testing."""
    return [
        Question(
            question_id=1,
            question="How does Python handle hash collisions in dictionaries?",
            expected_concepts=["open addressing", "probing", "load factor", "resize"],
            reference_answer="Python uses open addressing with probing and resizes when load factor exceeds 2/3.",
        ),
        Question(
            question_id=2,
            question="Explain the Global Interpreter Lock (GIL) and its impact on multithreading.",
            expected_concepts=["GIL", "CPython mutex", "CPU-bound vs IO-bound", "multiprocessing"],
            reference_answer="The GIL is a mutex preventing multiple native threads from executing Python bytecode simultaneously.",
        ),
        Question(
            question_id=3,
            question="What is the difference between deepcopy and shallow copy in Python?",
            expected_concepts=["references", "nested objects", "copy module", "memory"],
            reference_answer="Shallow copy duplicates the container referencing original child objects; deepcopy recursively duplicates all children.",
        ),
        Question(
            question_id=4,
            question="How does Python's garbage collection handle cyclic references?",
            expected_concepts=["reference counting", "generational GC", "gc module", "cyclic references"],
            reference_answer="Python combines reference counting with a generational cyclic garbage collector.",
        ),
        Question(
            question_id=5,
            question="Describe Python generator functions and the yield keyword.",
            expected_concepts=["generators", "yield", "lazy evaluation", "iterator protocol"],
            reference_answer="Generators produce values on demand using yield, maintaining state between iterations and saving memory.",
        ),
    ]


@pytest.fixture
def sample_session(mock_questions):
    """An initialized in-memory session with 5 questions."""
    session = InterviewSession(
        interview_id="test-session-1234",
        category=InterviewCategory.PYTHON,
        difficulty=InterviewDifficulty.INTERMEDIATE,
        total_questions=5,
        questions=mock_questions,
        current_question_index=0,
        status=InterviewStatus.IN_PROGRESS,
    )
    interview_store.save(session)
    return session
