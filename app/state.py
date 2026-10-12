import threading
from typing import Dict, Optional
from app.models.interview import InterviewSession


class InMemoryInterviewStore:
    """Thread-safe purely in-memory store for active interview sessions.

    No persistence to disk, database, or external cache.
    All data vanishes immediately upon server process restart.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._sessions: Dict[str, InterviewSession] = {}

    def save(self, session: InterviewSession) -> None:
        with self._lock:
            self._sessions[session.interview_id] = session

    def get(self, interview_id: str) -> Optional[InterviewSession]:
        with self._lock:
            return self._sessions.get(interview_id)

    def delete(self, interview_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(interview_id, None) is not None

    def clear(self) -> None:
        """Clear all active sessions (e.g., during tests)."""
        with self._lock:
            self._sessions.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._sessions)


# Global in-memory singleton
interview_store = InMemoryInterviewStore()
