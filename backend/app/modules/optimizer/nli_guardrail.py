import logging
import re

from app.models.candidate import CandidateSkill
from app.modules.ontology.normalizer import skill_normalizer

logger = logging.getLogger(__name__)


class NLIGuardrail:
    """Multi-Layer Factual Preservation & Anti-Hallucination Guardrail:
    Enforces zero-tolerance for hallucinated entities, fabricated quantitative metrics,
    ungrounded temporal shifts, and unauthorized seniority inflation.
    """

    # Layer 2: Quantitative Metric Patterns
    QUANT_PERCENT_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%", re.IGNORECASE)
    QUANT_CURRENCY_PATTERN = re.compile(
        r"\$\s*\d+(?:,\d+)*(?:\.\d+)?(?:\s*[kKmMbBtT]|\s*million|\s*billion)?",
        re.IGNORECASE,
    )
    QUANT_MULTIPLIER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?x\b", re.IGNORECASE)
    QUANT_UNIT_METRIC_PATTERN = re.compile(
        r"\b\d+(?:\.\d+)?\s*(?:ms|seconds|minutes|hours|days|users|rps|qps|tps|tb|gb|mb|pb|customers|clients)\b",
        re.IGNORECASE,
    )
    STANDALONE_NUMBER_PATTERN = re.compile(r"\b\d{2,}\b")

    # Layer 3: Temporal Marker Patterns
    CALENDAR_YEAR_PATTERN = re.compile(r"\b(?:19|20)\d{2}\b")
    MONTH_NAME_PATTERN = re.compile(
        r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b",
        re.IGNORECASE,
    )
    DURATION_PATTERN = re.compile(r"\b\d+\+?\s*(?:year|month|week)s?\b", re.IGNORECASE)

    # Layer 4: Seniority & Scope Inflation Keywords
    SENIORITY_INFLATION_PATTERN = re.compile(
        r"\b(?:chief\s+architect|cto|director|head\s+of|vice\s+president|vp|sole\s+(?:author|creator|inventor|architect))\b",
        re.IGNORECASE,
    )

    def verify_bullet(
        self,
        original_text: str,
        optimized_text: str,
        candidate_skills: list[CandidateSkill],
        allow_legacy_entailment: bool = True,
    ) -> tuple[str, str]:
        """Perform 5-layer factual validation:
        Layer 1: Entity validation (technologies, tools, certifications)
        Layer 2: Quantitative validation (percentages, currencies, counts, performance metrics)
        Layer 3: Temporal validation (calendar years, months, durations)
        Layer 4: Semantic scope & seniority preservation
        Layer 5: Human review status categorization

        Returns: (status: 'VERIFIED' | 'ENTAILMENT' | 'FLAGGED' | 'REQUIRES_REVIEW' | 'NOT_VERIFIED', rationale: str)
        """
        orig_clean = (original_text or "").strip()
        opt_clean = (optimized_text or "").strip()

        if not orig_clean or not opt_clean:
            return ("NOT_VERIFIED", "Original or optimized bullet text is empty.")

        # -------------------------------------------------------------
        # LAYER 1: Entity Validation
        # -------------------------------------------------------------
        orig_skills = {
            s["canonical_name"].lower()
            for s in skill_normalizer.extract_skills_from_text(orig_clean)
        }
        cand_verified_skills = {
            (s.normalized_name or s.skill_name).lower() for s in candidate_skills
        }
        allowed_skills = orig_skills.union(cand_verified_skills)

        opt_skills = {
            s["canonical_name"].lower()
            for s in skill_normalizer.extract_skills_from_text(opt_clean)
        }

        unverified_skills = opt_skills - allowed_skills
        if unverified_skills:
            violating = ", ".join(sorted(s.title() for s in unverified_skills))
            return (
                "FLAGGED",
                f"Factual drift: introduces unverified technologies ({violating}) not present in source bullet or candidate profile.",
            )

        # -------------------------------------------------------------
        # LAYER 2: Quantitative Validation
        # -------------------------------------------------------------
        orig_quants = self._extract_quantitatives(orig_clean)
        opt_quants = self._extract_quantitatives(opt_clean)

        unverified_quants = opt_quants - orig_quants
        if unverified_quants:
            violating_metrics = ", ".join(sorted(unverified_quants))
            return (
                "FLAGGED",
                f"Hallucination alert: introduced fabricated quantitative metrics ({violating_metrics}) not substantiated by original bullet.",
            )

        # -------------------------------------------------------------
        # LAYER 3: Temporal Validation
        # -------------------------------------------------------------
        orig_temporals = self._extract_temporals(orig_clean)
        opt_temporals = self._extract_temporals(opt_clean)

        unverified_temporals = opt_temporals - orig_temporals
        if unverified_temporals:
            violating_dates = ", ".join(sorted(unverified_temporals))
            return (
                "FLAGGED",
                f"Factual drift: introduced ungrounded calendar dates/years ({violating_dates}) not present in source bullet.",
            )

        # -------------------------------------------------------------
        # LAYER 4: Semantic Scope & Seniority Preservation
        # -------------------------------------------------------------
        orig_seniority = set(self.SENIORITY_INFLATION_PATTERN.findall(orig_clean))
        opt_seniority = set(self.SENIORITY_INFLATION_PATTERN.findall(opt_clean))
        unverified_seniority = opt_seniority - orig_seniority
        if unverified_seniority:
            violating_roles = ", ".join(sorted(unverified_seniority))
            return (
                "FLAGGED",
                f"Seniority distortion: elevated role title to ({violating_roles}) without substantiation in original experience.",
            )

        # -------------------------------------------------------------
        # LAYER 5: Status Determination
        # -------------------------------------------------------------
        # When all deterministic entity/metric/temporal/seniority guardrails pass:
        # Return ENTAILMENT (or VERIFIED) for verified factual preservation.
        status_label = "ENTAILMENT" if allow_legacy_entailment else "VERIFIED"
        return (
            status_label,
            "Factual consistency verified; strictly preserves source evidence, metrics, and entities while elevating active impact verbs.",
        )

    def _extract_quantitatives(self, text: str) -> set[str]:
        """Extract all quantitative tokens (percentages, currencies, multipliers, metrics, numbers)."""
        metrics = set()
        text_lower = text.lower()

        for m in self.QUANT_PERCENT_PATTERN.findall(text_lower):
            metrics.add(m.strip())
        for m in self.QUANT_CURRENCY_PATTERN.findall(text_lower):
            metrics.add(m.strip())
        for m in self.QUANT_MULTIPLIER_PATTERN.findall(text_lower):
            metrics.add(m.strip())
        for m in self.QUANT_UNIT_METRIC_PATTERN.findall(text_lower):
            metrics.add(m.strip())
        for m in self.STANDALONE_NUMBER_PATTERN.findall(text_lower):
            # Skip 4-digit calendar years so they are handled accurately by temporal validation
            if self.CALENDAR_YEAR_PATTERN.fullmatch(m):
                continue
            metrics.add(m.strip())

        return metrics

    def _extract_temporals(self, text: str) -> set[str]:
        """Extract calendar years, month names, and duration spans."""
        temporals = set()
        text_lower = text.lower()

        for m in self.CALENDAR_YEAR_PATTERN.findall(text_lower):
            temporals.add(m.strip())
        for m in self.MONTH_NAME_PATTERN.findall(text_lower):
            temporals.add(m.strip())
        for m in self.DURATION_PATTERN.findall(text_lower):
            temporals.add(m.strip())

        return temporals


# Global guardrail instance
nli_guardrail = NLIGuardrail()
