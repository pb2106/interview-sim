from collections import Counter
from typing import List, Optional
from app.models.interview import InterviewSession, Question
from app.schemas.response import (
    CriterionBreakdown,
    FinalReportResponse,
    QuestionResultItem,
)


class ReportService:
    @staticmethod
    def calculate_grade(percentage: float) -> tuple[str, str]:
        """Map percentage to application-defined grading bands."""
        if percentage >= 90.0:
            return (
                "Excellent",
                "Outstanding demonstration of technical accuracy, relevance, and conceptual clarity.",
            )
        elif percentage >= 75.0:
            return (
                "Good",
                "Strong overall competency with solid technical reasoning and minor gaps.",
            )
        elif percentage >= 60.0:
            return (
                "Satisfactory",
                "Adequate baseline understanding; some key concepts require further depth and refinement.",
            )
        elif percentage >= 40.0:
            return (
                "Needs Improvement",
                "Incomplete or imprecise explanations across multiple core interview concepts.",
            )
        else:
            return (
                "Poor",
                "Significant knowledge gaps and inaccuracies. Comprehensive review recommended.",
            )

    @classmethod
    def generate_report(cls, session: InterviewSession) -> FinalReportResponse:
        """Calculate complete performance report strictly in Python."""
        evaluated_questions: List[Question] = [
            q for q in session.questions if q.evaluation is not None
        ]

        if not evaluated_questions:
            raise ValueError("Cannot generate report: No questions have been evaluated yet.")

        total_questions = len(evaluated_questions)
        max_possible_score = total_questions * 10

        total_score = sum(q.evaluation.score for q in evaluated_questions)
        average_score = round(total_score / total_questions, 2)
        percentage_score = round((total_score / max_possible_score) * 100, 2)

        grade, grade_desc = cls.calculate_grade(percentage_score)

        # Component sums
        total_correctness = sum(q.evaluation.correctness_score for q in evaluated_questions)
        total_relevance = sum(q.evaluation.relevance_score for q in evaluated_questions)
        total_completeness = sum(q.evaluation.completeness_score for q in evaluated_questions)
        total_clarity = sum(q.evaluation.clarity_score for q in evaluated_questions)

        max_correctness = total_questions * 4
        max_relevance = total_questions * 2
        max_completeness = total_questions * 2
        max_clarity = total_questions * 2

        criteria_breakdown = [
            CriterionBreakdown(
                criterion="Technical Correctness",
                earned_points=total_correctness,
                max_points=max_correctness,
                percentage=round((total_correctness / max_correctness) * 100, 1),
                description="Factual accuracy, algorithmic correctness, and depth of technical reasoning.",
            ),
            CriterionBreakdown(
                criterion="Relevance",
                earned_points=total_relevance,
                max_points=max_relevance,
                percentage=round((total_relevance / max_relevance) * 100, 1),
                description="Directness in addressing the interview prompt without extraneous filler.",
            ),
            CriterionBreakdown(
                criterion="Completeness",
                earned_points=total_completeness,
                max_points=max_completeness,
                percentage=round((total_completeness / max_completeness) * 100, 1),
                description="Coverage of essential trade-offs, edge cases, and foundational concepts.",
            ),
            CriterionBreakdown(
                criterion="Clarity",
                earned_points=total_clarity,
                max_points=max_clarity,
                percentage=round((total_clarity / max_clarity) * 100, 1),
                description="Structure, articulation, and coherence of technical communication.",
            ),
        ]

        # Individual Question Items
        question_results: List[QuestionResultItem] = []
        for q in evaluated_questions:
            ev = q.evaluation
            question_results.append(
                QuestionResultItem(
                    question_number=q.question_id,
                    question=q.question,
                    user_answer=q.user_answer or "",
                    score=ev.score,
                    max_score=10,
                    correctness_score=ev.correctness_score,
                    relevance_score=ev.relevance_score,
                    completeness_score=ev.completeness_score,
                    clarity_score=ev.clarity_score,
                    feedback=ev.feedback,
                    strengths=ev.strengths,
                    weaknesses=ev.weaknesses,
                    missing_concepts=ev.missing_concepts,
                    ideal_answer=ev.ideal_answer,
                    improvement_tip=ev.improvement_tip,
                )
            )

        # Strongest & Weakest Answers
        sorted_by_score = sorted(
            question_results,
            key=lambda x: (x.score, x.correctness_score, x.completeness_score),
        )
        weakest_answer = sorted_by_score[0] if sorted_by_score else None
        strongest_answer = sorted_by_score[-1] if sorted_by_score else None

        # Frequently Missing Concepts
        missing_counter = Counter()
        for q in evaluated_questions:
            for concept in q.evaluation.missing_concepts:
                clean_concept = concept.strip()
                if clean_concept:
                    missing_counter[clean_concept.lower()] += 1

        frequently_missing = [item[0].title() for item in missing_counter.most_common(5)]

        # 3 Prioritized Improvement Recommendations
        prioritized_recommendations = cls._derive_recommendations(
            criteria_breakdown=criteria_breakdown,
            question_results=question_results,
            frequently_missing=frequently_missing,
        )

        return FinalReportResponse(
            interview_id=session.interview_id,
            category=session.category.value,
            difficulty=session.difficulty.value,
            total_questions=total_questions,
            total_score=total_score,
            max_possible_score=max_possible_score,
            average_score=average_score,
            percentage_score=percentage_score,
            grade=grade,
            grade_description=grade_desc,
            grading_band_note="Calculated using application-defined grading bands (90%+ Excellent, 75%+ Good, 60%+ Satisfactory, 40%+ Needs Improvement, <40% Poor), not official industry standards.",
            evaluation_disclaimer="AI-generated scores provide automated formative feedback based on the evaluation rubric and do not represent a perfect or objective assessment of candidate capability.",
            criteria_breakdown=criteria_breakdown,
            question_results=question_results,
            strongest_answer=strongest_answer,
            weakest_answer=weakest_answer,
            frequently_missing_concepts=frequently_missing,
            prioritized_recommendations=prioritized_recommendations,
        )

    @classmethod
    def _derive_recommendations(
        cls,
        criteria_breakdown: List[CriterionBreakdown],
        question_results: List[QuestionResultItem],
        frequently_missing: List[str],
    ) -> List[str]:
        recommendations: List[str] = []

        # Find lowest scoring criterion
        sorted_criteria = sorted(criteria_breakdown, key=lambda c: c.percentage)
        lowest_crit = sorted_criteria[0] if sorted_criteria else None
        if lowest_crit and lowest_crit.percentage < 85.0:
            recommendations.append(
                f"Prioritize {lowest_crit.criterion} ({lowest_crit.percentage}%): Focus on {lowest_crit.description.lower()}"
            )

        # Collect actionable improvement tips from lower-scoring questions
        low_scoring_questions = [q for q in question_results if q.score <= 7]
        if not low_scoring_questions:
            low_scoring_questions = sorted(question_results, key=lambda q: q.score)

        for q in low_scoring_questions:
            if q.improvement_tip and q.improvement_tip not in recommendations:
                recommendations.append(f"Q{q.question_number} Focus: {q.improvement_tip}")
                if len(recommendations) >= 3:
                    break

        # Fallback if we still don't have 3
        if len(recommendations) < 3 and frequently_missing:
            recommendations.append(
                f"Conceptual review: Solidify fundamentals on {', '.join(frequently_missing[:3])}."
            )

        if len(recommendations) < 3:
            recommendations.append(
                "Structured communication: Use the STAR or Problem-Solution-Tradeoff method to frame answers thoroughly."
            )

        return recommendations[:3]
