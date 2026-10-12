from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


class InterviewCategory(str, Enum):
    GENERAL = "General"
    SOFTWARE_DEVELOPMENT = "Software Development"
    PYTHON = "Python"
    SQL = "SQL"
    DATA_STRUCTURES_AND_ALGORITHMS = "Data Structures and Algorithms"
    BEHAVIOURAL = "Behavioural"


class InterviewDifficulty(str, Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class InterviewStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class AnswerEvaluation:
    score: int  # 0-10, calculated in Python: correctness + relevance + completeness + clarity
    correctness_score: int  # 0-4
    relevance_score: int  # 0-2
    completeness_score: int  # 0-2
    clarity_score: int  # 0-2
    strengths: List[str]
    weaknesses: List[str]
    missing_concepts: List[str]
    feedback: str
    ideal_answer: str
    improvement_tip: str


@dataclass
class Question:
    question_id: int
    question: str
    expected_concepts: List[str]
    reference_answer: str
    user_answer: Optional[str] = None
    evaluation: Optional[AnswerEvaluation] = None


@dataclass
class InterviewSession:
    interview_id: str
    category: InterviewCategory
    difficulty: InterviewDifficulty
    total_questions: int
    questions: List[Question]
    current_question_index: int = 0
    status: InterviewStatus = InterviewStatus.IN_PROGRESS
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_completed(self) -> bool:
        return self.status == InterviewStatus.COMPLETED or (
            len(self.questions) > 0
            and all(q.evaluation is not None for q in self.questions)
        )

    def current_question(self) -> Optional[Question]:
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
