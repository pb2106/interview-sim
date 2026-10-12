from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class AIGeneratedQuestion(BaseModel):
    question: str = Field(..., min_length=10, description="The interview question")
    expected_concepts: List[str] = Field(
        ..., min_length=1, description="List of key concepts candidate should touch on"
    )
    reference_answer: str = Field(
        ..., min_length=10, description="A comprehensive reference answer"
    )


class AIGeneratedQuestionList(BaseModel):
    questions: List[AIGeneratedQuestion] = Field(
        ..., min_length=1, description="List of generated questions"
    )


class AIAssessmentResponse(BaseModel):
    score: Optional[int] = Field(
        None, description="Reported score (will be overridden by sum of components)"
    )
    correctness_score: int = Field(
        ..., ge=0, le=4, description="Technical correctness score between 0 and 4"
    )
    relevance_score: int = Field(
        ..., ge=0, le=2, description="Relevance score between 0 and 2"
    )
    completeness_score: int = Field(
        ..., ge=0, le=2, description="Completeness score between 0 and 2"
    )
    clarity_score: int = Field(
        ..., ge=0, le=2, description="Clarity score between 0 and 2"
    )
    strengths: List[str] = Field(
        default_factory=list, description="Demonstrated strengths in the answer"
    )
    weaknesses: List[str] = Field(
        default_factory=list, description="Areas where the answer fell short"
    )
    missing_concepts: List[str] = Field(
        default_factory=list, description="Key concepts expected but omitted"
    )
    feedback: str = Field(
        ..., min_length=5, description="Concise explanation of the evaluation"
    )
    ideal_answer: str = Field(
        ..., min_length=10, description="A model answer for comparison"
    )
    improvement_tip: str = Field(
        ..., min_length=5, description="One actionable recommendation for improvement"
    )

    @field_validator("strengths", "weaknesses", "missing_concepts", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v.strip()]
        if isinstance(v, list):
            return [str(item).strip() for item in v if str(item).strip()]
        return []
