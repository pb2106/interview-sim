import logging
import uuid
from fastapi import APIRouter, HTTPException, status
from app.models.interview import InterviewSession, InterviewStatus
from app.schemas.request import CreateInterviewRequest, SubmitAnswerRequest
from app.schemas.response import (
    CreateInterviewResponse,
    EvaluationResponse,
    FinalReportResponse,
    InterviewProgressResponse,
    QuestionPublicResponse,
)
from app.services.groq_service import (
    GroqRateLimitException,
    GroqServiceException,
    GroqTimeoutException,
    GroqValidationException,
    groq_service,
)
from app.services.report_service import ReportService
from app.state import interview_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


@router.post("", response_model=CreateInterviewResponse, status_code=status.HTTP_201_CREATED)
def create_interview(payload: CreateInterviewRequest):
    """Generate interview questions using Groq and initialize an in-memory interview session."""
    try:
        questions = groq_service.generate_questions(
            category=payload.category,
            difficulty=payload.difficulty,
            count=payload.question_count,
        )
    except GroqRateLimitException as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except GroqTimeoutException as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except (GroqValidationException, GroqServiceException) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error creating interview: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected server error while initializing interview.",
        )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate any valid interview questions.",
        )

    interview_id = str(uuid.uuid4())
    session = InterviewSession(
        interview_id=interview_id,
        category=payload.category,
        difficulty=payload.difficulty,
        total_questions=len(questions),
        questions=questions,
        current_question_index=0,
        status=InterviewStatus.IN_PROGRESS,
    )
    interview_store.save(session)

    first_q = questions[0]
    return CreateInterviewResponse(
        interview_id=interview_id,
        category=session.category.value,
        difficulty=session.difficulty.value,
        total_questions=session.total_questions,
        current_question_index=0,
        current_question=QuestionPublicResponse(
            question_number=first_q.question_id,
            total_questions=session.total_questions,
            question=first_q.question,
        ),
    )


@router.get("/{interview_id}", response_model=InterviewProgressResponse)
def get_interview_progress(interview_id: str):
    """Retrieve current progress of an active interview session."""
    session = interview_store.get(interview_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session '{interview_id}' not found.",
        )

    answered_count = sum(1 for q in session.questions if q.evaluation is not None)
    current_q_obj = session.current_question()
    current_q_resp = None
    if current_q_obj and not session.is_completed:
        current_q_resp = QuestionPublicResponse(
            question_number=current_q_obj.question_id,
            total_questions=session.total_questions,
            question=current_q_obj.question,
        )

    return InterviewProgressResponse(
        interview_id=session.interview_id,
        category=session.category.value,
        difficulty=session.difficulty.value,
        total_questions=session.total_questions,
        answered_questions=answered_count,
        current_question_index=session.current_question_index,
        status=session.status.value,
        is_completed=session.is_completed,
        current_question=current_q_resp,
    )


@router.post("/{interview_id}/answers", response_model=EvaluationResponse)
def submit_answer(interview_id: str, payload: SubmitAnswerRequest):
    """Evaluate an answer for the current question in the interview."""
    session = interview_store.get(interview_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session '{interview_id}' not found.",
        )

    if session.is_completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interview has already been completed. No further answers can be submitted.",
        )

    idx = session.current_question_index
    if idx >= len(session.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All questions have already been answered.",
        )

    question = session.questions[idx]

    # Duplicate answer prevention
    if question.evaluation is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question {question.question_id} has already been evaluated.",
        )

    try:
        evaluation = groq_service.evaluate_answer(
            question=question,
            user_answer=payload.answer,
            category=session.category,
            difficulty=session.difficulty,
        )
    except GroqRateLimitException as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except GroqTimeoutException as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except (GroqValidationException, GroqServiceException) as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Answer evaluation failed: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during answer evaluation: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while evaluating answer.",
        )

    # Record answer & evaluation in server memory
    question.user_answer = payload.answer
    question.evaluation = evaluation

    # Advance pointer
    session.current_question_index += 1
    if session.current_question_index >= len(session.questions):
        session.status = InterviewStatus.COMPLETED

    interview_store.save(session)

    next_idx = session.current_question_index if not session.is_completed else None

    return EvaluationResponse(
        question_number=question.question_id,
        user_answer=payload.answer,
        score=evaluation.score,
        correctness_score=evaluation.correctness_score,
        relevance_score=evaluation.relevance_score,
        completeness_score=evaluation.completeness_score,
        clarity_score=evaluation.clarity_score,
        strengths=evaluation.strengths,
        weaknesses=evaluation.weaknesses,
        missing_concepts=evaluation.missing_concepts,
        feedback=evaluation.feedback,
        ideal_answer=evaluation.ideal_answer,
        improvement_tip=evaluation.improvement_tip,
        is_interview_completed=session.is_completed,
        next_question_index=next_idx,
    )


@router.get("/{interview_id}/results", response_model=FinalReportResponse)
def get_interview_results(interview_id: str):
    """Retrieve final comprehensive performance report once all questions are answered."""
    session = interview_store.get(interview_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interview session '{interview_id}' not found.",
        )

    # Check if all questions have been answered and evaluated
    unanswered = [q for q in session.questions if q.evaluation is None]
    if unanswered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Interview is not completed yet. {len(unanswered)} of {session.total_questions} questions remaining.",
        )

    try:
        report = ReportService.generate_report(session)
        return report
    except Exception as e:
        logger.error(f"Error compiling interview report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance report: {str(e)}",
        )
