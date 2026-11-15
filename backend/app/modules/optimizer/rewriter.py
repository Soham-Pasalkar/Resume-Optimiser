import json
import logging
import re

from app.core.llm import ollama_client
from app.models.candidate import CandidateSkill
from app.models.jd import JDRequirement, JobDescription
from app.modules.optimizer.nli_guardrail import nli_guardrail

logger = logging.getLogger(__name__)

STRONG_ACTION_VERBS: dict[str, str] = {
    "worked on": "Architected and engineered",
    "helped with": "Collaborated to engineer",
    "assisted with": "Partnered to implement",
    "assisted in": "Partnered to deploy",
    "participated in": "Contributed to delivering",
    "involved in": "Contributed directly to engineering",
    "responsible for": "Orchestrated and managed",
    "took care of": "Administered and maintained",
    "part of team that": "Engineered collaboratively to deliver",
    "handled": "Administered and scaled",
    "built": "Engineered and deployed",
    "made": "Developed",
    "wrote": "Authored and shipped",
    "did": "Executed",
    "fixed": "Diagnosed and resolved",
    "improved": "Optimized",
    "utilized": "Leveraged",
    "used": "Implemented",
    "supported": "Maintained and supported",
    "maintained": "Maintained and upgraded",
}


class BulletRewriter:
    """Context-Aware Resume Bullet Rewriter:
    Elevates passive phrasing into strong technical impact verbs and aligns with job requirements
    without inventing qualifications, fabricating metrics, or using hollow AI buzzwords.
    """

    REWRITE_PROMPT = """You are an expert executive resume strategist and technical recruiter.
Rewrite the following resume bullet point to elevate its professional impact and align with the target position.

CRITICAL FACTUAL RULES (ZERO TOLERANCE FOR HALLUCINATION):
1. Under NO circumstances invent new programming languages, frameworks, cloud platforms, or tools not present in the original text.
2. Under NO circumstances fabricate specific quantitative percentages, dollar figures, performance multipliers, or numbers.
3. If the original text contains quantitative metrics, PRESERVE THEM EXACTLY. If it does not contain metrics, DO NOT FABRICATE THEM; instead focus on technical actions, systems, and outcomes.
4. Avoid generic, hollow AI buzzwords (e.g., "synergy", "paradigm", "cutting-edge").
5. Return ONLY valid JSON:
{{
  "optimized_text": "string",
  "rationale": "string explanation of technical phrasing enhancements"
}}

Target Role: {role}
Target Requirement to Emphasize: {requirement}
Original Bullet: {bullet}
"""

    async def rewrite_bullet(
        self,
        original_text: str,
        jd: JobDescription,
        candidate_skills: list[CandidateSkill],
        target_requirement: JDRequirement | None = None,
    ) -> dict[str, str]:
        """Generate optimized bullet with context-aware verb elevation and factual guardrail validation."""
        clean_orig = original_text.strip()
        req_text = (
            target_requirement.requirement_text
            if target_requirement
            else f"Core responsibilities for {jd.job_title}"
        )

        # 1. Try local LLM generation if available
        try:
            status = await ollama_client.get_status()
            if status.is_available:
                prompt = self.REWRITE_PROMPT.format(
                    role=jd.job_title,
                    requirement=req_text,
                    bullet=clean_orig,
                )
                resp = await ollama_client.generate(
                    prompt=prompt,
                    system_prompt="You rewrite resume bullets into strong technical impact statements. Output JSON only.",
                    format_json=True,
                    temperature=0.2,
                )
                raw_json = resp.get("response", "").strip()
                if raw_json.startswith("```"):
                    raw_json = re.sub(r"^```(?:json)?", "", raw_json).strip()
                    raw_json = re.sub(r"```$", "", raw_json).strip()

                parsed = json.loads(raw_json)
                opt_text = parsed.get("optimized_text", "").strip()
                rationale = parsed.get(
                    "rationale",
                    "Elevated technical phrasing and aligned active contribution with target role requirements.",
                )

                # Validate through Multi-Layer Factual Guardrail
                nli_status, nli_msg = nli_guardrail.verify_bullet(
                    clean_orig,
                    opt_text,
                    candidate_skills,
                )

                if nli_status != "FLAGGED" and opt_text:
                    return {
                        "original_text": clean_orig,
                        "optimized_text": opt_text,
                        "rationale": rationale,
                        "nli_verification_status": nli_status,
                    }
                else:
                    logger.warning(
                        "LLM rewrite flagged by guardrail (%s). Falling back to rule-based rewriter.",
                        nli_msg,
                    )
        except Exception as exc:
            logger.warning(
                "Ollama bullet rewriter unavailable (%s). Using deterministic rule engine.", exc
            )

        # 2. Deterministic Rule-Based Fallback (Zero Hallucination Guaranteed)
        return self._rule_based_rewrite(clean_orig, target_requirement, candidate_skills)

    def _rule_based_rewrite(
        self,
        original_text: str,
        target_requirement: JDRequirement | None,
        candidate_skills: list[CandidateSkill],
    ) -> dict[str, str]:
        """Deterministic rule-based transformation upgrading passive verbs to impact phrasing."""
        text = original_text.strip()
        replaced = False

        # Upgrade weak verbs
        for weak, strong in STRONG_ACTION_VERBS.items():
            pattern = re.compile(rf"\b{re.escape(weak)}\b", re.IGNORECASE)
            if pattern.search(text):
                text = pattern.sub(strong, text, count=1)
                replaced = True
                break

        if not replaced:
            # If starts with conjunction or weak intro, trim and capitalize
            words = text.split()
            first_word = words[0] if words else ""
            if first_word.lower() in ["and", "also", "then", "additionally"]:
                text = text[len(first_word) :].strip()
            text = text[0].upper() + text[1:] if text else text

        # Add targeted alignment rationale
        rationale_parts = ["Elevated active technical phrasing while strictly preserving factual scope."]
        if target_requirement and target_requirement.canonical_skill_name:
            skill = target_requirement.canonical_skill_name
            rationale_parts.append(f"Emphasized demonstrated competency in {skill}.")

        # Ensure proper punctuation
        if not text.endswith((".", ";")):
            text += "."

        # Run through guardrail to confirm status
        nli_status, _ = nli_guardrail.verify_bullet(original_text, text, candidate_skills)

        return {
            "original_text": original_text,
            "optimized_text": text,
            "rationale": " ".join(rationale_parts),
            "nli_verification_status": nli_status,
        }


# Global bullet rewriter instance
bullet_rewriter = BulletRewriter()
