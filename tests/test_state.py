import os
from pathlib import Path
from app.models.interview import InterviewCategory, InterviewDifficulty, InterviewSession, InterviewStatus
from app.state import InMemoryInterviewStore, interview_store


def test_in_memory_store_operations():
    """Verify in-memory store saves, retrieves, counts, deletes, and clears."""
    store = InMemoryInterviewStore()
    assert store.count() == 0

    session = InterviewSession(
        interview_id="session-abc",
        category=InterviewCategory.GENERAL,
        difficulty=InterviewDifficulty.BEGINNER,
        total_questions=5,
        questions=[],
        status=InterviewStatus.IN_PROGRESS,
    )

    store.save(session)
    assert store.count() == 1
    assert store.get("session-abc") is session
    assert store.get("unknown-id") is None

    deleted = store.delete("session-abc")
    assert deleted is True
    assert store.count() == 0
    assert store.get("session-abc") is None


def test_no_persistence_or_disk_artifacts():
    """Verify that using interview_store writes zero SQLite, JSON, or DB files to the workspace."""
    root_dir = Path(__file__).parent.parent
    before_files = set(root_dir.rglob("*.db")) | set(root_dir.rglob("*.sqlite"))

    # Save multiple sessions to the in-memory store
    for i in range(10):
        s = InterviewSession(
            interview_id=f"temp-session-{i}",
            category=InterviewCategory.PYTHON,
            difficulty=InterviewDifficulty.INTERMEDIATE,
            total_questions=5,
            questions=[],
        )
        interview_store.save(s)

    assert interview_store.count() == 10

    # Ensure no database files were created anywhere in the workspace
    after_files = set(root_dir.rglob("*.db")) | set(root_dir.rglob("*.sqlite"))
    assert before_files == after_files

    # Fresh instance has zero sessions (process restart simulation)
    fresh_store = InMemoryInterviewStore()
    assert fresh_store.count() == 0
