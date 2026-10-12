from unittest.mock import patch
import pytest
from app.models.interview import AnswerEvaluation, InterviewCategory, InterviewDifficulty, Question
from app.state import interview_store
from tests.conftest import PREDEFINED_ANSWERS


def test_health_check(client):
    """GET /api/health returns status ok and model information."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["app"] == "InterviewIQ"
    assert "active_in_memory_sessions" in data


def test_serve_index_html(client):
    """GET / serves the SPA frontend."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "InterviewIQ" in res.text


def test_create_interview_success(client, mock_questions):
    """POST /api/interviews generates questions and hides secrets from response."""
    with patch("app.routes.interviews.groq_service.generate_questions", return_value=mock_questions):
        payload = {
            "category": "Python",
            "difficulty": "Intermediate",
            "question_count": 5,
        }
        res = client.post("/api/interviews", json=payload)
        assert res.status_code == 201
        data = res.json()

        assert "interview_id" in data
        assert data["category"] == "Python"
        assert data["difficulty"] == "Intermediate"
        assert data["total_questions"] == 5
        assert data["current_question_index"] == 0

        # Critical security check: expected_concepts and reference_answer MUST NOT be in response!
        curr_q = data["current_question"]
        assert "question" in curr_q
        assert "expected_concepts" not in curr_q
        assert "reference_answer" not in curr_q


@pytest.mark.parametrize(
    "invalid_payload,expected_field",
    [
        ({"category": "NonExistentDomain", "difficulty": "Beginner", "question_count": 5}, "category"),
        ({"category": "Python", "difficulty": "SuperExpert", "question_count": 5}, "difficulty"),
        ({"category": "Python", "difficulty": "Beginner", "question_count": 7}, "question_count"),
        ({"category": "Python", "difficulty": "Beginner", "question_count": 20}, "question_count"),
    ],
)
def test_create_interview_validation_failures(client, invalid_payload, expected_field):
    """POST /api/interviews rejects invalid category, difficulty, or question count."""
    res = client.post("/api/interviews", json=invalid_payload)
    assert res.status_code == 422


def test_get_interview_progress_unknown_id(client):
    """GET /api/interviews/{id} returns 404 for unknown session."""
    res = client.get("/api/interviews/non-existent-uuid")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_get_interview_progress_success(client, sample_session):
    """GET /api/interviews/{id} returns in-progress details."""
    res = client.get(f"/api/interviews/{sample_session.interview_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["interview_id"] == sample_session.interview_id
    assert data["answered_questions"] == 0
    assert data["total_questions"] == 5
    assert data["is_completed"] is False
    assert data["current_question"]["question_number"] == 1


def test_submit_answer_validation(client, sample_session):
    """POST /api/interviews/{id}/answers enforces minimum non-whitespace length."""
    # Blank or whitespace
    res = client.post(f"/api/interviews/{sample_session.interview_id}/answers", json={"answer": "   "})
    assert res.status_code == 422

    # Too short (< 2 chars)
    res2 = client.post(f"/api/interviews/{sample_session.interview_id}/answers", json={"answer": "a"})
    assert res2.status_code == 422


def test_submit_answer_success_and_duplicate_prevention(client, sample_session):
    """Submit answer evaluates correctly and prevents duplicate submission."""
    mock_eval = AnswerEvaluation(
        score=9,
        correctness_score=4,
        relevance_score=2,
        completeness_score=2,
        clarity_score=1,
        strengths=["Clear mechanism explanation"],
        weaknesses=["Slightly informal tone"],
        missing_concepts=[],
        feedback="Great answer covering all key mechanisms.",
        ideal_answer="Python uses open addressing...",
        improvement_tip="Refine technical terminology.",
    )

    with patch("app.routes.interviews.groq_service.evaluate_answer", return_value=mock_eval):
        # First submission succeeds
        res = client.post(
            f"/api/interviews/{sample_session.interview_id}/answers",
            json={"answer": PREDEFINED_ANSWERS["correct"]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["score"] == 9
        assert data["correctness_score"] == 4
        assert data["relevance_score"] == 2
        assert data["completeness_score"] == 2
        assert data["clarity_score"] == 1
        assert data["is_interview_completed"] is False
        assert data["next_question_index"] == 1

        # Check in session: question 1 now has evaluation and pointer moved
        updated_session = interview_store.get(sample_session.interview_id)
        assert updated_session.questions[0].evaluation is not None
        assert updated_session.current_question_index == 1

        # If a duplicate submission is attempted directly on question 1 (or after pointer is moved)
        # Testing pointer guard: if someone tries to submit to an already answered question
        updated_session.current_question_index = 0  # simulate replay
        res_dup = client.post(
            f"/api/interviews/{sample_session.interview_id}/answers",
            json={"answer": "Trying to answer again"},
        )
        assert res_dup.status_code == 400
        assert "already been evaluated" in res_dup.json()["detail"].lower()


def test_cannot_get_results_before_interview_completion(client, sample_session):
    """GET /api/interviews/{id}/results returns 400 if interview is incomplete."""
    res = client.get(f"/api/interviews/{sample_session.interview_id}/results")
    assert res.status_code == 400
    assert "not completed yet" in res.json()["detail"].lower()


def test_full_interview_flow_to_completion(client, sample_session):
    """Answer all questions sequentially to completion and verify final report."""
    mock_eval = AnswerEvaluation(
        score=8,
        correctness_score=3,
        relevance_score=2,
        completeness_score=1,
        clarity_score=2,
        strengths=["Good conceptual explanation"],
        weaknesses=["Missed load factor threshold"],
        missing_concepts=["Load factor 2/3"],
        feedback="Solid answer with minor detail omitted.",
        ideal_answer="Model answer text.",
        improvement_tip="Mention exact threshold numbers.",
    )

    with patch("app.routes.interviews.groq_service.evaluate_answer", return_value=mock_eval):
        # Answer all 5 questions
        for i in range(5):
            res = client.post(
                f"/api/interviews/{sample_session.interview_id}/answers",
                json={"answer": f"Answer for question {i + 1} with sufficient length."},
            )
            assert res.status_code == 200
            data = res.json()
            if i < 4:
                assert data["is_interview_completed"] is False
            else:
                assert data["is_interview_completed"] is True
                assert data["next_question_index"] is None

        # Interview is now completed
        # Attempting another answer submission should fail with 400
        res_extra = client.post(
            f"/api/interviews/{sample_session.interview_id}/answers",
            json={"answer": "Another answer after finish."},
        )
        assert res_extra.status_code == 400
        assert "already been completed" in res_extra.json()["detail"].lower()

        # Fetching final report should now succeed
        res_results = client.get(f"/api/interviews/{sample_session.interview_id}/results")
        assert res_results.status_code == 200
        report = res_results.json()

        assert report["interview_id"] == sample_session.interview_id
        assert report["total_questions"] == 5
        assert report["total_score"] == 40  # 5 * 8
        assert report["max_possible_score"] == 50
        assert report["average_score"] == 8.0
        assert report["percentage_score"] == 80.0
        assert report["grade"] == "Good"
        assert len(report["criteria_breakdown"]) == 4
        assert len(report["question_results"]) == 5
        assert report["strongest_answer"] is not None
        assert report["weakest_answer"] is not None
        assert "Load Factor 2/3" in report["frequently_missing_concepts"]
        assert len(report["prioritized_recommendations"]) == 3

        # Downloading PDF report should now succeed
        res_pdf = client.get(f"/api/interviews/{sample_session.interview_id}/pdf")
        assert res_pdf.status_code == 200
        assert res_pdf.headers["content-type"] == "application/pdf"
        assert res_pdf.content.startswith(b"%PDF")
        assert len(res_pdf.content) > 500


def test_cannot_download_pdf_before_interview_completion(client, sample_session):
    """GET /api/interviews/{id}/pdf returns 400 if interview is incomplete."""
    res = client.get(f"/api/interviews/{sample_session.interview_id}/pdf")
    assert res.status_code == 400
    assert "not completed yet" in res.json()["detail"].lower()


def test_download_pdf_unknown_id(client):
    """GET /api/interviews/{id}/pdf returns 404 for unknown session."""
    res = client.get("/api/interviews/non-existent-uuid/pdf")
    assert res.status_code == 404
