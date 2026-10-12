import json
import logging
import time
from typing import List, Optional
from groq import (
    APIConnectionError,
    APITimeoutError,
    Groq,
    InternalServerError,
    RateLimitError,
)
from app.config import settings
from app.models.interview import (
    AnswerEvaluation,
    InterviewCategory,
    InterviewDifficulty,
    Question,
)
from app.schemas.ai import AIAssessmentResponse, AIGeneratedQuestionList

logger = logging.getLogger(__name__)


class GroqServiceException(Exception):
    """Base exception for Groq service operations."""
    pass


class GroqRateLimitException(GroqServiceException):
    """Raised when Groq API rate limit is exceeded."""
    pass


class GroqTimeoutException(GroqServiceException):
    """Raised when Groq API request times out."""
    pass


class GroqValidationException(GroqServiceException):
    """Raised when Groq API response cannot be parsed or validated."""
    pass


class GroqService:
    def __init__(self, client: Optional[Groq] = None, model: Optional[str] = None):
        self._model = model or settings.groq_model
        if client is not None:
            self._client = client
        else:
            try:
                self._client = Groq(
                    api_key=settings.api_key,
                    timeout=settings.groq_timeout_seconds,
                )
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
                self._client = None

    @property
    def model(self) -> str:
        return self._model

    def _execute_with_retry(self, fn):
        """Execute a Groq call with bounded exponential backoff retries."""
        last_error = None
        for attempt in range(settings.groq_max_retries + 1):
            try:
                return fn()
            except RateLimitError as e:
                logger.warning(f"Groq RateLimitError on attempt {attempt + 1}: {e}")
                last_error = GroqRateLimitException("Groq API rate limit reached. Please wait a moment and try again.")
                if attempt < settings.groq_max_retries:
                    time.sleep(1.5 * (attempt + 1))
            except APITimeoutError as e:
                logger.warning(f"Groq APITimeoutError on attempt {attempt + 1}: {e}")
                last_error = GroqTimeoutException("Groq request timed out. Please try again.")
                if attempt < settings.groq_max_retries:
                    time.sleep(1.0 * (attempt + 1))
            except APIConnectionError as e:
                logger.warning(f"Groq APIConnectionError on attempt {attempt + 1}: {e}")
                last_error = GroqServiceException(f"Network error connecting to Groq API: {e}")
                if attempt < settings.groq_max_retries:
                    time.sleep(1.0 * (attempt + 1))
            except InternalServerError as e:
                logger.warning(f"Groq InternalServerError on attempt {attempt + 1}: {e}")
                last_error = GroqServiceException("Groq server temporarily unavailable. Please retry.")
                if attempt < settings.groq_max_retries:
                    time.sleep(1.5 * (attempt + 1))
            except Exception as e:
                logger.error(f"Groq call failed with unexpected error: {type(e)} {e}")
                raise GroqServiceException(f"Groq API error: {str(e)}") from e

        if last_error:
            raise last_error
        raise GroqServiceException("Groq API call failed after retries.")

    def generate_questions(
        self,
        category: InterviewCategory,
        difficulty: InterviewDifficulty,
        count: int,
    ) -> List[Question]:
        """Generate structured interview questions once for an interview."""
        if not self._client:
            raise GroqServiceException("Groq API client is not configured. Check your .env file.")

        system_prompt = (
            "You are an expert technical interviewer. Output valid, parseable JSON only. "
            "Never include commentary outside the JSON object."
        )

        user_prompt = f"""Generate exactly {count} distinct interview questions for category '{category.value}' at '{difficulty.value}' level.

Output format must be a JSON object with a single key 'questions' containing an array of objects.
Each question object MUST have:
- "question": clear, professional interview question (string)
- "expected_concepts": array of 2 to 5 essential technical concepts/keywords (array of strings)
- "reference_answer": concise reference answer explaining the ideal key points (string, 2 to 4 sentences)

Requirements:
- Questions must be appropriately challenging for {difficulty.value} level.
- No duplicate or overlapping questions.
- Keep output concise to minimize token usage.
"""

        def _call():
            return self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2200,
            )

        resp = self._execute_with_retry(_call)
        raw_text = resp.choices[0].message.content or ""

        try:
            parsed = AIGeneratedQuestionList.model_validate_json(raw_text)
        except Exception as err:
            logger.error(f"Failed to parse generated questions: {err}. Raw: {raw_text[:300]}")
            raise GroqValidationException(f"Malformed questions generated by AI: {err}") from err

        if len(parsed.questions) < count:
            logger.warning(
                f"Generated fewer questions than requested ({len(parsed.questions)} < {count})"
            )

        # Convert to domain Question objects
        questions: List[Question] = []
        for idx, q_data in enumerate(parsed.questions[:count], start=1):
            questions.append(
                Question(
                    question_id=idx,
                    question=q_data.question.strip(),
                    expected_concepts=[c.strip() for c in q_data.expected_concepts if c.strip()],
                    reference_answer=q_data.reference_answer.strip(),
                    user_answer=None,
                    evaluation=None,
                )
            )

        return questions

    def evaluate_answer(
        self,
        question: Question,
        user_answer: str,
        category: InterviewCategory,
        difficulty: InterviewDifficulty,
    ) -> AnswerEvaluation:
        """Evaluate a submitted interview answer against rubric using Groq."""
        if not self._client:
            raise GroqServiceException("Groq API client is not configured. Check your .env file.")

        system_prompt = (
            "You are an expert technical and behavioural interview evaluator. "
            "Output valid JSON only matching the specified rubric fields. "
            "Never produce markdown formatting outside JSON."
        )

        expected_concepts_str = ", ".join(question.expected_concepts)
        user_prompt = f"""Evaluate this interview answer according to the rubric.

Context:
Category: {category.value}
Difficulty: {difficulty.value}
Question: {question.question}
Expected concepts: {expected_concepts_str}
Reference answer: {question.reference_answer}

Candidate answer:
\"\"\"{user_answer}\"\"\"

Evaluation Rules:
1. Accept alternative technically correct solutions or terminology.
2. Distinguish completely incorrect information from simply missing details.
3. Do not award points for verbose, irrelevant fluff.
4. Calibrate expectations to {difficulty.value} difficulty level.

Rubric:
- correctness_score: 0 to 4 (0=completely incorrect/misleading, 1=minimal accuracy, 2=partially accurate, 3=mostly accurate, 4=thoroughly correct)
- relevance_score: 0 to 2 (0=off-topic, 1=partially addresses prompt, 2=directly addresses prompt)
- completeness_score: 0 to 2 (0=omits all key concepts, 1=covers some concepts, 2=covers essential concepts)
- clarity_score: 0 to 2 (0=incoherent or very confusing, 1=understandable with effort, 2=clear, articulate, structured)

Output JSON structure:
{{
  "correctness_score": int (0-4),
  "relevance_score": int (0-2),
  "completeness_score": int (0-2),
  "clarity_score": int (0-2),
  "strengths": ["string", ...],
  "weaknesses": ["string", ...],
  "missing_concepts": ["string", ...],
  "feedback": "string (concise explanation of score)",
  "ideal_answer": "string (model answer for comparison)",
  "improvement_tip": "string (one actionable tip)"
}}"""

        def _call():
            return self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
                max_tokens=900,
            )

        resp = self._execute_with_retry(_call)
        raw_text = resp.choices[0].message.content or ""

        try:
            parsed = AIAssessmentResponse.model_validate_json(raw_text)
        except Exception as err:
            logger.error(f"Failed to parse evaluation response: {err}. Raw: {raw_text[:300]}")
            raise GroqValidationException(f"Malformed evaluation response from AI: {err}") from err

        # CRITICAL: Calculate score in Python from the four component scores!
        # Component ranges: correctness (0-4), relevance (0-2), completeness (0-2), clarity (0-2) -> Total: 0-10
        calculated_score = (
            parsed.correctness_score
            + parsed.relevance_score
            + parsed.completeness_score
            + parsed.clarity_score
        )
        calculated_score = max(0, min(10, calculated_score))

        return AnswerEvaluation(
            score=calculated_score,
            correctness_score=parsed.correctness_score,
            relevance_score=parsed.relevance_score,
            completeness_score=parsed.completeness_score,
            clarity_score=parsed.clarity_score,
            strengths=parsed.strengths,
            weaknesses=parsed.weaknesses,
            missing_concepts=parsed.missing_concepts,
            feedback=parsed.feedback.strip(),
            ideal_answer=parsed.ideal_answer.strip(),
            improvement_tip=parsed.improvement_tip.strip(),
        )


# Default service instance
groq_service = GroqService()
