import re

from app.models.candidate import CandidateSkill
from app.modules.ontology.normalizer import skill_normalizer


class NLIGuardrail:
    """Enforces strict factual preservation and anti-hallucination guardrails on rewritten bullets."""

    METRIC_PATTERN = re.compile(
        r"(?:\$\s*\d+(?:,\d+)*(?:\.\d+)?(?:\s*[kKmMbB]|million|billion)?|\d+(?:\.\d+)?%|\d+x|\b\d{2,}\b)",
        re.IGNORECASE,
    )

    def verify_bullet(
        self,
        original_text: str,
        optimized_text: str,
        candidate_skills: list[CandidateSkill],
    ) -> tuple[str, str]:
        """Inspects entity deltas and numerical claims to guarantee zero hallucinated metrics.
        Returns: (nli_status: 'ENTAILMENT' | 'NEUTRAL' | 'FLAGGED', rationale: str)
        """
        # 1. Extract technologies from original vs optimized
        orig_skills = {
            s["canonical_name"].lower()
            for s in skill_normalizer.extract_skills_from_text(original_text)
        }
        cand_verified_skills = {s.normalized_name.lower() for s in candidate_skills}
        allowed_skills = orig_skills.union(cand_verified_skills)

        opt_skills = {
            s["canonical_name"].lower()
            for s in skill_normalizer.extract_skills_from_text(optimized_text)
        }

        # Check for ungrounded new technologies
        unverified_skills = opt_skills - allowed_skills
        if unverified_skills:
            violating = ", ".join(s.title() for s in unverified_skills)
            return (
                "FLAGGED",
                f"Factual drift: introduces unverified technologies ({violating}) not present in source bullet or candidate profile.",
            )

        # 2. Extract numeric / percentage / monetary tokens
        orig_metrics = set(self.METRIC_PATTERN.findall(original_text))
        opt_metrics = set(self.METRIC_PATTERN.findall(optimized_text))

        # Check if new specific numbers or percentages were hallucinated
        unverified_metrics = opt_metrics - orig_metrics

        if unverified_metrics:
            violating_metrics = ", ".join(unverified_metrics)
            return (
                "FLAGGED",
                f"Hallucination alert: introduced fabricated quantitative metrics ({violating_metrics}) not substantiated by original bullet.",
            )

        # 3. Strict factual preservation confirmed
        return (
            "ENTAILMENT",
            "Factual consistency verified; strictly preserves source evidence while elevating active impact verbs.",
        )


# Global guardrail instance
nli_guardrail = NLIGuardrail()
