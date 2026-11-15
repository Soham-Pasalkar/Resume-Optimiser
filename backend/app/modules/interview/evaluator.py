import json
import logging
import re
from typing import Any

from app.core.llm import ollama_client
from app.models.career import InterviewQuestion

logger = logging.getLogger(__name__)


class AnswerEvaluator:
    """Evaluates candidate practice responses against technical, STAR, and gap-defense rubrics."""

    EVAL_PROMPT = """You are a Principal Technical Interviewer evaluating a candidate's practice interview response.

Question Type: {qtype}
Question: {question}
Target Competency: {target}
Evaluation Rubric: {criteria}

Candidate's Answer:
\"\"\"{answer}\"\"\"

Provide rigorous, constructive evaluation in JSON format:
{{
  "score": 85.0,
  "strengths": [
    "string concrete strength 1",
    "string concrete strength 2"
  ],
  "improvements": [
    "string actionable area for improvement 1",
    "string actionable area for improvement 2"
  ],
  "critique": "string detailed paragraph with structural advice and phrasing refinement"
}}
Return ONLY valid JSON.
"""

    async def evaluate_response(
        self,
        question: InterviewQuestion,
        candidate_response: str,
    ) -> dict[str, Any]:
        clean_resp = candidate_response.strip()
        if not clean_resp or len(clean_resp) < 15:
            return {
                "score": 35.0,
                "strengths": ["Attempted to answer the prompt."],
                "improvements": [
                    "Response is too brief to evaluate competency.",
                    "Provide concrete details following the STAR method (Situation, Task, Action, Result).",
                ],
                "critique": "Your response lacks the necessary depth and detail. In technical and behavioral interviews, aim for structured responses with clear context, your specific technical actions, and measurable outcomes.",
            }

        # 1. Try local Ollama evaluation
        try:
            status = await ollama_client.get_status()
            if status.is_available:
                prompt = self.EVAL_PROMPT.format(
                    qtype=question.question_type,
                    question=question.question_text,
                    target=question.target_skill_or_gap or "General",
                    criteria=question.evaluation_criteria,
                    answer=clean_resp,
                )
                resp = await ollama_client.generate(
                    prompt=prompt,
                    system_prompt="You evaluate candidate interview answers strictly against technical rubrics. Output JSON only.",
                    format_json=True,
                    temperature=0.2,
                )
                raw_json = resp.get("response", "").strip()
                if raw_json.startswith("```"):
                    raw_json = re.sub(r"^```(?:json)?", "", raw_json).strip()
                    raw_json = re.sub(r"```$", "", raw_json).strip()

                parsed = json.loads(raw_json)
                if "score" in parsed and "critique" in parsed:
                    return parsed
        except Exception as exc:
            logger.warning(
                "Ollama interview evaluator unavailable (%s). Using rubric evaluation engine.", exc
            )

        # 2. Deterministic Rubric Fallback
        return self._rubric_evaluate_fallback(question, clean_resp)

    def _rubric_evaluate_fallback(
        self,
        question: InterviewQuestion,
        response: str,
    ) -> dict[str, Any]:
        words = response.split()
        word_count = len(words)

        score = 60.0
        strengths = []
        improvements = []

        # Length check
        if word_count >= 80:
            score += 15.0
            strengths.append("Thorough and detailed response demonstrating depth.")
        elif word_count >= 40:
            score += 10.0
            strengths.append("Sufficient length covering the primary question context.")
        else:
            improvements.append(
                "Expand your answer with more specific implementation context and architectural trade-offs."
            )

        # Check for STAR markers or structured transitions
        has_action = any(
            v in response.lower()
            for v in [
                "built",
                "designed",
                "architected",
                "implemented",
                "resolved",
                "opted",
                "chose",
                "led",
                "decided",
            ]
        )
        has_result = any(
            v in response.lower()
            for v in [
                "result",
                "reduced",
                "increased",
                "outcome",
                "improved",
                "saved",
                "enabled",
                "delivered",
                "successfully",
            ]
        )

        if has_action:
            score += 10.0
            strengths.append(
                "Explicitly highlights concrete personal actions and technical execution."
            )
        else:
            improvements.append(
                "Focus more clearly on the specific actions YOU took, rather than what the team did in general."
            )

        if has_result:
            score += 10.0
            strengths.append("Articulates measurable business or engineering impact.")
        else:
            improvements.append(
                "Conclude with a definitive result: what was the quantitative impact or long-term engineering outcome?"
            )

        # Check for target skill mention
        target = question.target_skill_or_gap
        if target and target.lower() in response.lower():
            score += 5.0
            strengths.append(f"Directly addressed the target competency: {target}.")

        final_score = round(min(100.0, max(40.0, score)), 1)

        critique = (
            f"Your response demonstrates solid foundational awareness with a score of {final_score}/100. "
            f"To elevate this answer to a staff/principal level: "
            f"1) Clearly frame the business stakes upfront, "
            f"2) Detail the architectural alternatives you rejected and why, and "
            f"3) Quantify the final engineering impact (e.g. latency, throughput, reliability)."
        )

        return {
            "score": final_score,
            "strengths": strengths or ["Clear and articulate communication."],
            "improvements": improvements
            or ["Consider adding deeper technical trade-off analysis."],
            "critique": critique,
        }


# Global evaluator instance
answer_evaluator = AnswerEvaluator()
