from pydantic import BaseModel, Field, field_validator
from app.models.interview import InterviewCategory, InterviewDifficulty


class CreateInterviewRequest(BaseModel):
    category: InterviewCategory
    difficulty: InterviewDifficulty
    question_count: int = Field(..., description="Number of questions (5, 10, or 15)")

    @field_validator("question_count")
    @classmethod
    def validate_question_count(cls, v: int) -> int:
        if v not in (5, 10, 15):
            raise ValueError("question_count must be 5, 10, or 15")
        return v


class SubmitAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=2, max_length=5000, description="The user's submitted answer")

    @field_validator("answer")
    @classmethod
    def validate_not_only_whitespace(cls, v: str) -> str:
        trimmed = v.strip()
        if len(trimmed) < 2:
            raise ValueError("Answer must contain at least 2 non-whitespace characters")
        return trimmed
