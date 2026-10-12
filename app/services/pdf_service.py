import io
from datetime import datetime, timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from app.schemas.response import FinalReportResponse


def generate_pdf_report(report: FinalReportResponse) -> bytes:
    """Generate a clean, professional PDF performance report from a FinalReportResponse."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=14,
    )
    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#334155"),
        spaceBefore=12,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )
    body_bold = ParagraphStyle(
        "BodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a"),
    )
    answer_quote_style = ParagraphStyle(
        "AnswerQuote",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )

    elements = []

    # Title Banner
    elements.append(Paragraph("InterviewIQ - Performance Evaluation Report", title_style))
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    elements.append(
        Paragraph(
            f"Generated on {date_str} | Session ID: {report.interview_id[:8]}",
            subtitle_style,
        )
    )
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#6366f1"), spaceAfter=14))

    # Overview Summary Box
    summary_data = [
        [
            Paragraph("<b>Domain / Category:</b>", body_style),
            Paragraph(report.category, body_bold),
            Paragraph("<b>Overall Score:</b>", body_style),
            Paragraph(f"{report.total_score} / {report.max_possible_score} ({report.percentage_score}%)", body_bold),
        ],
        [
            Paragraph("<b>Difficulty Level:</b>", body_style),
            Paragraph(report.difficulty, body_bold),
            Paragraph("<b>Evaluation Grade:</b>", body_style),
            Paragraph(f"{report.grade} ({report.average_score}/10 avg)", body_bold),
        ],
        [
            Paragraph("<b>Total Questions:</b>", body_style),
            Paragraph(str(report.total_questions), body_bold),
            Paragraph("<b>Storage Policy:</b>", body_style),
            Paragraph("Zero-Persistence (In-Memory Only)", body_bold),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[110, 150, 110, 160])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    # Criteria Breakdown Table
    elements.append(Paragraph("Rubric Criteria Breakdown", section_heading_style))
    criteria_table_data = [
        [
            Paragraph("<b>Criterion</b>", body_bold),
            Paragraph("<b>Earned Points</b>", body_bold),
            Paragraph("<b>Max Points</b>", body_bold),
            Paragraph("<b>Percentage</b>", body_bold),
            Paragraph("<b>Evaluation Focus</b>", body_bold),
        ]
    ]
    for crit in report.criteria_breakdown:
        criteria_table_data.append(
            [
                Paragraph(crit.criterion, body_style),
                Paragraph(str(crit.earned_points), body_style),
                Paragraph(str(crit.max_points), body_style),
                Paragraph(f"{crit.percentage}%", body_style),
                Paragraph(crit.description, body_style),
            ]
        )

    crit_table = Table(criteria_table_data, colWidths=[120, 75, 75, 75, 185])
    crit_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(crit_table)
    elements.append(Spacer(1, 14))

    # Detailed Question-by-Question Review
    elements.append(Paragraph("Question-by-Question Detailed Review", section_heading_style))
    for q in report.question_results:
        q_elements = []
        q_header = (
            f"<b>Question {q.question_number}:</b> {q.question} "
            f"<b>[Score: {q.score}/10 pts &bull; Correctness: {q.correctness_score}/4, Relevance: {q.relevance_score}/2, Completeness: {q.completeness_score}/2, Clarity: {q.clarity_score}/2]</b>"
        )
        q_elements.append(Paragraph(q_header, body_style))
        q_elements.append(Spacer(1, 4))

        # Submitted answer quote
        ans_text = f"<b>Candidate Answer:</b> {q.user_answer}"
        q_elements.append(Paragraph(ans_text, answer_quote_style))
        q_elements.append(Spacer(1, 4))

        # Feedback & Recommendation
        q_elements.append(Paragraph(f"<b>Evaluator Feedback:</b> {q.feedback}", body_style))
        q_elements.append(Spacer(1, 3))
        q_elements.append(Paragraph(f"<b>Right / Reference Answer:</b> {q.ideal_answer}", body_style))
        q_elements.append(Spacer(1, 3))
        q_elements.append(Paragraph(f"<b>Recommendation:</b> {q.improvement_tip}", body_style))
        q_elements.append(Spacer(1, 8))
        q_elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=8))

        elements.append(KeepTogether(q_elements))

    # Frequently Missing Concepts & Prioritized Recommendations
    elements.append(Paragraph("Targeted Areas for Improvement", section_heading_style))
    if report.frequently_missing_concepts:
        missing_str = ", ".join(report.frequently_missing_concepts)
        elements.append(Paragraph(f"<b>Frequently Omitted Concepts:</b> {missing_str}", body_style))
        elements.append(Spacer(1, 4))

    elements.append(Paragraph("<b>Prioritized Recommendations:</b>", body_style))
    for i, rec in enumerate(report.prioritized_recommendations, start=1):
        elements.append(Paragraph(f"{i}. {rec}", body_style))
        elements.append(Spacer(1, 2))

    elements.append(Spacer(1, 14))

    # Disclaimers
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#94a3b8"), spaceAfter=6))
    elements.append(Paragraph(f"Note: {report.grading_band_note}", disclaimer_style))
    elements.append(Spacer(1, 2))
    elements.append(Paragraph(f"Disclaimer: {report.evaluation_disclaimer}", disclaimer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
