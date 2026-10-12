import pytest
from app.models.interview import (
    AnswerEvaluation,
    InterviewCategory,
    InterviewDifficulty,
    InterviewSession,
    InterviewStatus,
    Question,
)
from app.services.report_service import ReportService


def test_grading_bands_mapping():
    """Verify application-defined grading bands match requirements."""
    assert ReportService.calculate_grade(100.0)[0] == "Excellent"
    assert ReportService.calculate_grade(90.0)[0] == "Excellent"
    assert ReportService.calculate_grade(89.9)[0] == "Good"
    assert ReportService.calculate_grade(75.0)[0] == "Good"
    assert ReportService.calculate_grade(74.9)[0] == "Satisfactory"
    assert ReportService.calculate_grade(60.0)[0] == "Satisfactory"
    assert ReportService.calculate_grade(59.9)[0] == "Needs Improvement"
    assert ReportService.calculate_grade(40.0)[0] == "Needs Improvement"
    assert ReportService.calculate_grade(39.9)[0] == "Poor"
    assert ReportService.calculate_grade(0.0)[0] == "Poor"


def test_report_generation_with_different_scores():
    """Verify totals, averages, percentages, breakdown, and recommendations."""
    questions = [
        Question(
            question_id=1,
            question="What is an index in SQL?",
            expected_concepts=["B-Tree", "lookup performance", "write penalty"],
            reference_answer="An index accelerates lookup...",
            user_answer="It is a B-Tree structure for faster SELECTs.",
            evaluation=AnswerEvaluation(
                score=10,
                correctness_score=4,
                relevance_score=2,
                completeness_score=2,
                clarity_score=2,
                strengths=["Excellent accuracy"],
                weaknesses=[],
                missing_concepts=[],
                feedback="Flawless explanation.",
                ideal_answer="Model answer 1",
                improvement_tip="Keep up the clear explanations.",
            ),
        ),
        Question(
            question_id=2,
            question="Explain ACID properties.",
            expected_concepts=["Atomicity", "Consistency", "Isolation", "Durability"],
            reference_answer="ACID ensures reliability...",
            user_answer="It means transactions are safe.",
            evaluation=AnswerEvaluation(
                score=3,
                correctness_score=1,
                relevance_score=1,
                completeness_score=0,
                clarity_score=1,
                strengths=["Basic awareness"],
                weaknesses=["Did not list any ACID letters"],
                missing_concepts=["Atomicity", "Consistency", "Isolation", "Durability"],
                feedback="Vague answer missing all 4 components.",
                ideal_answer="Model answer 2",
                improvement_tip="Memorize and explain all four ACID pillars individually.",
            ),
        ),
    ]

    session = InterviewSession(
        interview_id="test-rep-session",
        category=InterviewCategory.SQL,
        difficulty=InterviewDifficulty.BEGINNER,
        total_questions=2,
        questions=questions,
        current_question_index=2,
        status=InterviewStatus.COMPLETED,
    )

    report = ReportService.generate_report(session)

    # 10 + 3 = 13 total score out of 20 max
    assert report.total_score == 13
    assert report.max_possible_score == 20
    assert report.average_score == 6.5
    assert report.percentage_score == 65.0
    assert report.grade == "Satisfactory"

    # Criteria breakdown
    # Correctness: 4 + 1 = 5 / 8 (62.5%)
    # Relevance: 2 + 1 = 3 / 4 (75.0%)
    # Completeness: 2 + 0 = 2 / 4 (50.0%)
    # Clarity: 2 + 1 = 3 / 4 (75.0%)
    by_name = {c.criterion: c for c in report.criteria_breakdown}
    assert by_name["Technical Correctness"].earned_points == 5
    assert by_name["Technical Correctness"].max_points == 8
    assert by_name["Completeness"].earned_points == 2
    assert by_name["Completeness"].max_points == 4

    # Strongest and Weakest
    assert report.strongest_answer.question_number == 1
    assert report.strongest_answer.score == 10
    assert report.weakest_answer.question_number == 2
    assert report.weakest_answer.score == 3

    # Frequently missing concepts
    assert "Atomicity" in report.frequently_missing_concepts
    assert "Durability" in report.frequently_missing_concepts

    # 3 Prioritized Recommendations
    assert len(report.prioritized_recommendations) == 3

    # Disclaimers present
    assert "application-defined" in report.grading_band_note.lower()
    assert "not represent a perfect or objective assessment" in report.evaluation_disclaimer.lower()


def test_cannot_generate_report_without_evaluations():
    """Verify ValueError is raised if attempting to generate report with zero evaluations."""
    session = InterviewSession(
        interview_id="empty-session",
        category=InterviewCategory.GENERAL,
        difficulty=InterviewDifficulty.BEGINNER,
        total_questions=1,
        questions=[
            Question(
                question_id=1,
                question="What is an API?",
                expected_concepts=["interface"],
                reference_answer="An API is...",
                evaluation=None,
            )
        ],
    )
    with pytest.raises(ValueError, match="No questions have been evaluated"):
        ReportService.generate_report(session)
