import json
from unittest.mock import MagicMock, patch
import pytest
from groq import APIConnectionError, APITimeoutError, RateLimitError
from app.models.interview import InterviewCategory, InterviewDifficulty, Question
from app.schemas.ai import AIAssessmentResponse
from app.services.groq_service import (
    GroqRateLimitException,
    GroqService,
    GroqServiceException,
    GroqTimeoutException,
    GroqValidationException,
)
from tests.conftest import PREDEFINED_ANSWERS


def test_final_score_calculated_strictly_in_python():
    """Verify that Python calculates score from components and overrides any model arithmetic."""
    # Suppose the LLM incorrectly claimed score = 10 despite low component scores
    raw_ai_data = {
        "score": 10,  # Model's hallucinated arithmetic
        "correctness_score": 2,
        "relevance_score": 1,
        "completeness_score": 1,
        "clarity_score": 1,
        "strengths": ["Recognized hash tables"],
        "weaknesses": ["Missed open addressing specifics"],
        "missing_concepts": ["Load factor", "Probing"],
        "feedback": "Partially accurate response.",
        "ideal_answer": "Complete answer...",
        "improvement_tip": "Review collision techniques.",
    }

    mock_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = json.dumps(raw_ai_data)
    mock_client.chat.completions.create.return_value = mock_resp

    service = GroqService(client=mock_client)
    sample_q = Question(
        question_id=1,
        question="How does Python handle hash collisions?",
        expected_concepts=["open addressing", "load factor"],
        reference_answer="Open addressing with probing...",
    )

    eval_result = service.evaluate_answer(
        question=sample_q,
        user_answer="They use probing.",
        category=InterviewCategory.PYTHON,
        difficulty=InterviewDifficulty.INTERMEDIATE,
    )

    # Sum must be 2 + 1 + 1 + 1 = 5, NOT the model's 10!
    assert eval_result.score == 5
    assert eval_result.correctness_score == 2
    assert eval_result.relevance_score == 1
    assert eval_result.completeness_score == 1
    assert eval_result.clarity_score == 1


def test_component_score_validation_bounds():
    """Verify Pydantic rejects out-of-range component scores."""
    # Correctness must be 0-4
    with pytest.raises(Exception):
        AIAssessmentResponse(
            correctness_score=5,  # Invalid: > 4
            relevance_score=2,
            completeness_score=2,
            clarity_score=2,
            feedback="Great",
            ideal_answer="Ideal",
            improvement_tip="Tip",
        )

    # Relevance must be 0-2
    with pytest.raises(Exception):
        AIAssessmentResponse(
            correctness_score=4,
            relevance_score=3,  # Invalid: > 2
            completeness_score=2,
            clarity_score=2,
            feedback="Great",
            ideal_answer="Ideal",
            improvement_tip="Tip",
        )


def test_predefined_answers_different_scoring_tiers():
    """Verify evaluation logic with mocked tiers for correct, partial, incorrect, and irrelevant."""
    mock_client = MagicMock()
    service = GroqService(client=mock_client)
    sample_q = Question(
        question_id=1,
        question="How does Python handle hash collisions in dictionaries?",
        expected_concepts=["open addressing", "probing", "load factor", "resize"],
        reference_answer="Python uses open addressing...",
    )

    tiers = [
        ("correct", 4, 2, 2, 2, 10),
        ("partially_correct", 2, 2, 1, 1, 6),
        ("incorrect", 0, 1, 0, 1, 2),
        ("irrelevant", 0, 0, 0, 1, 1),
    ]

    for key, c, r, comp, cl, expected_total in tiers:
        raw_data = {
            "correctness_score": c,
            "relevance_score": r,
            "completeness_score": comp,
            "clarity_score": cl,
            "strengths": ["Strengths for " + key],
            "weaknesses": ["Weaknesses for " + key],
            "missing_concepts": ["Concepts for " + key] if comp < 2 else [],
            "feedback": f"Evaluation for {key}",
            "ideal_answer": "Model answer",
            "improvement_tip": f"Actionable tip for {key}",
        }
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps(raw_data)
        mock_client.chat.completions.create.return_value = mock_resp

        result = service.evaluate_answer(
            question=sample_q,
            user_answer=PREDEFINED_ANSWERS[key],
            category=InterviewCategory.PYTHON,
            difficulty=InterviewDifficulty.INTERMEDIATE,
        )

        assert result.score == expected_total
        assert result.correctness_score == c
        assert result.relevance_score == r


def test_groq_rate_limit_error_handling(client, sample_session):
    """Verify RateLimitError raises GroqRateLimitException and returns HTTP 429."""
    with patch("app.routes.interviews.groq_service._client.chat.completions.create") as mock_call:
        mock_call.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429, headers={}),
            body=None,
        )

        res = client.post(
            f"/api/interviews/{sample_session.interview_id}/answers",
            json={"answer": "Some answer text to test rate limit."},
        )
        assert res.status_code == 429
        assert "rate limit" in res.json()["detail"].lower()


def test_groq_timeout_error_handling(client, sample_session):
    """Verify APITimeoutError raises GroqTimeoutException and returns HTTP 504."""
    with patch("app.routes.interviews.groq_service._client.chat.completions.create") as mock_call:
        mock_call.side_effect = APITimeoutError(request=MagicMock())

        res = client.post(
            f"/api/interviews/{sample_session.interview_id}/answers",
            json={"answer": "Some answer text to test timeout."},
        )
        assert res.status_code == 504
        assert "timed out" in res.json()["detail"].lower()


def test_groq_malformed_response_fails_cleanly(client, sample_session):
    """Never silently assign a score when evaluation fails; return 502 with error details."""
    with patch("app.routes.interviews.groq_service._client.chat.completions.create") as mock_call:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = "Not a json response {broken"
        mock_call.return_value = mock_resp

        res = client.post(
            f"/api/interviews/{sample_session.interview_id}/answers",
            json={"answer": "Valid answer text"},
        )
        assert res.status_code == 502
        assert "malformed" in res.json()["detail"].lower()
