from typing import List, Optional
from pydantic import BaseModel, Field


class QuestionPublicResponse(BaseModel):
    question_number: int
    total_questions: int
    question: str


class CreateInterviewResponse(BaseModel):
    interview_id: str
    category: str
    difficulty: str
    total_questions: int
    current_question_index: int
    current_question: QuestionPublicResponse


class InterviewProgressResponse(BaseModel):
    interview_id: str
    category: str
    difficulty: str
    total_questions: int
    answered_questions: int
    current_question_index: int
    status: str
    is_completed: bool
    current_question: Optional[QuestionPublicResponse] = None


class EvaluationResponse(BaseModel):
    question_number: int
    user_answer: str
    score: int = Field(..., ge=0, le=10)
    correctness_score: int = Field(..., ge=0, le=4)
    relevance_score: int = Field(..., ge=0, le=2)
    completeness_score: int = Field(..., ge=0, le=2)
    clarity_score: int = Field(..., ge=0, le=2)
    strengths: List[str]
    weaknesses: List[str]
    missing_concepts: List[str]
    feedback: str
    ideal_answer: str
    improvement_tip: str
    is_interview_completed: bool
    next_question_index: Optional[int] = None


class CriterionBreakdown(BaseModel):
    criterion: str
    earned_points: int
    max_points: int
    percentage: float
    description: str


class QuestionResultItem(BaseModel):
    question_number: int
    question: str
    user_answer: str
    score: int
    max_score: int = 10
    correctness_score: int
    relevance_score: int
    completeness_score: int
    clarity_score: int
    feedback: str
    strengths: List[str]
    weaknesses: List[str]
    missing_concepts: List[str]
    ideal_answer: str
    improvement_tip: str


class FinalReportResponse(BaseModel):
    interview_id: str
    category: str
    difficulty: str
    total_questions: int
    total_score: int
    max_possible_score: int
    average_score: float
    percentage_score: float
    grade: str
    grade_description: str
    grading_band_note: str
    evaluation_disclaimer: str
    criteria_breakdown: List[CriterionBreakdown]
    question_results: List[QuestionResultItem]
    strongest_answer: Optional[QuestionResultItem] = None
    weakest_answer: Optional[QuestionResultItem] = None
    frequently_missing_concepts: List[str]
    prioritized_recommendations: List[str]
