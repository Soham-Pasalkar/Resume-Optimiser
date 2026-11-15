import re
from typing import Any

from app.models.candidate import CandidateSkill
from app.models.jd import JDRequirement, JobDescription
from app.models.resume import Resume
from app.modules.matching.bm25 import BM25Index
from app.modules.matching.dense import dense_matcher
from app.modules.ontology.normalizer import skill_normalizer


class ScoringResult:
    def __init__(
        self,
        overall_score: float,
        rating_label: str,
        skill_match_score: float,
        semantic_score: float,
        lexical_score: float,
        experience_score: float,
        domain_score: float,
        scoring_breakdown: dict[str, Any],
        summary_analysis: str,
        gap_evaluations: list[dict[str, Any]],
    ):
        self.overall_score = overall_score
        self.rating_label = rating_label
        self.skill_match_score = skill_match_score
        self.semantic_score = semantic_score
        self.lexical_score = lexical_score
        self.experience_score = experience_score
        self.domain_score = domain_score
        self.scoring_breakdown = scoring_breakdown
        self.summary_analysis = summary_analysis
        self.gap_evaluations = gap_evaluations


class HybridMatchingEngine:
    """Combines BM25 lexical search, dense embeddings, ontology overlap, and multi-factor scoring."""

    def __init__(
        self,
        w_skill: float = 0.35,
        w_sem: float = 0.25,
        w_lex: float = 0.15,
        w_exp: float = 0.15,
        w_dom: float = 0.10,
    ):
        self.w_skill = w_skill
        self.w_sem = w_sem
        self.w_lex = w_lex
        self.w_exp = w_exp
        self.w_dom = w_dom

    async def evaluate(
        self,
        resume: Resume,
        jd: JobDescription,
        candidate_skills: list[CandidateSkill],
    ) -> ScoringResult:
        # 1. Gather granular atomic resume textual chunks (bullets and distinct lines only; never entire sections)
        resume_chunks: list[str] = []
        for section in resume.sections:
            heading = section.heading or "Experience"
            for item in section.items:
                prefix = f"[{item.title} at {item.organization or 'Company'}] " if item.title else ""
                for bullet in item.bullets or []:
                    bullet_text = bullet if isinstance(bullet, str) else str(bullet)
                    clean_b = bullet_text.strip()
                    if clean_b:
                        resume_chunks.append(f"{prefix}{clean_b}")
            # For sections without items or skills lists, split by lines/bullets, never the entire multi-line section
            if section.raw_content and not section.items:
                lines = [ln.strip().lstrip("•-* ").strip() for ln in section.raw_content.splitlines() if ln.strip()]
                for ln in lines:
                    if len(ln) >= 5:
                        resume_chunks.append(f"[{heading}] {ln}")

        if not resume_chunks:
            resume_chunks = [s.strip() for s in re.split(r"[\n.]+", resume.raw_text or "") if len(s.strip()) > 10]

        # 2. Fit BM25 Index
        bm25_index = BM25Index()
        bm25_index.fit(resume_chunks)

        # 3. Index Candidate Skills
        candidate_canonical_map: dict[str, CandidateSkill] = {
            s.normalized_name.lower(): s for s in candidate_skills
        }
        candidate_categories = {s.category for s in candidate_skills}

        # 4. Evaluate each JD Requirement
        gap_evaluations: list[dict[str, Any]] = []
        req_texts = [r.requirement_text for r in jd.requirements]
        lexical_score = bm25_index.compute_overall_lexical_alignment(req_texts)

        skill_points = 0.0
        total_skill_weight = 0.0
        mandatory_matched = 0
        mandatory_total = 0
        preferred_matched = 0
        preferred_total = 0

        semantic_similarities: list[float] = []

        for req in jd.requirements:
            w_i = 1.0 if req.is_mandatory else 0.6
            total_skill_weight += w_i

            if req.is_mandatory:
                mandatory_total += 1
            else:
                preferred_total += 1

            # Check direct skill match via ontology
            canonical_target = (req.canonical_skill_name or "").lower()
            if not canonical_target:
                extracted = skill_normalizer.extract_skills_from_text(req.requirement_text)
                if extracted:
                    canonical_target = extracted[0]["canonical_name"].lower()

            direct_skill = (
                candidate_canonical_map.get(canonical_target) if canonical_target else None
            )

            # Semantic similarity search against candidate resume snippets
            best_sim, best_snippet = await dense_matcher.find_best_evidence_match(
                req.requirement_text,
                resume_chunks,
            )

            # If direct skill is matched with evidence, anchor semantic relevance
            if direct_skill:
                best_sim = max(best_sim, 0.85 if direct_skill.evidence_text else 0.75)

            semantic_similarities.append(best_sim)

            # Determine Match Status & Gap Classification
            status, severity, match_ratio, suggested_action = self._classify_gap(
                req=req,
                direct_skill=direct_skill,
                best_sim=best_sim,
                candidate_categories=candidate_categories,
            )

            skill_points += w_i * match_ratio

            if req.is_mandatory and match_ratio >= 0.7:
                mandatory_matched += 1
            elif not req.is_mandatory and match_ratio >= 0.7:
                preferred_matched += 1

            evidence_text = None
            if direct_skill and direct_skill.evidence_text:
                evidence_text = direct_skill.evidence_text
            elif best_sim >= 0.48 and best_snippet:
                evidence_text = best_snippet[:220].strip()
                if len(best_snippet) > 220:
                    evidence_text += "..."

            if status == "NOT_DEMONSTRATED":
                evidence_text = None

            gap_evaluations.append(
                {
                    "requirement_id": req.id,
                    "requirement_text": req.requirement_text,
                    "category": req.category,
                    "is_mandatory": req.is_mandatory,
                    "status": status,
                    "gap_severity": severity,
                    "evidence_snippet": evidence_text,
                    "similarity_score": best_sim,
                    "suggested_action": suggested_action,
                    "is_resolved": bool(direct_skill and direct_skill.is_user_verified),
                }
            )

        # Calculate Sub-scores
        skill_match_score = round(
            (skill_points / total_skill_weight * 100.0) if total_skill_weight > 0 else 75.0,
            2,
        )
        semantic_score = round(
            (sum(semantic_similarities) / len(semantic_similarities) * 100.0)
            if semantic_similarities
            else 70.0,
            2,
        )

        # Experience Score
        experience_score = self._compute_experience_score(resume, jd)

        # Domain Relevance Score
        domain_score = self._compute_domain_score(candidate_skills, jd)

        # Overall Weighted Score
        overall = (
            self.w_skill * skill_match_score
            + self.w_sem * semantic_score
            + self.w_lex * lexical_score
            + self.w_exp * experience_score
            + self.w_dom * domain_score
        )
        overall_score = round(min(100.0, max(0.0, overall)), 2)

        # Rating Label
        rating_label = self._get_rating_label(overall_score)

        # Breakdown Dict
        mandatory_ratio = (
            round(mandatory_matched / mandatory_total, 2) if mandatory_total > 0 else 1.0
        )
        preferred_ratio = (
            round(preferred_matched / preferred_total, 2) if preferred_total > 0 else 1.0
        )

        scoring_breakdown = {
            "weights": {
                "skill_match": self.w_skill,
                "semantic": self.w_sem,
                "lexical": self.w_lex,
                "experience": self.w_exp,
                "domain": self.w_dom,
            },
            "mandatory_coverage_ratio": mandatory_ratio,
            "preferred_coverage_ratio": preferred_ratio,
            "mandatory_matched": mandatory_matched,
            "mandatory_total": mandatory_total,
            "preferred_matched": preferred_matched,
            "preferred_total": preferred_total,
        }

        # Explainable Summary Analysis
        summary_analysis = self._generate_summary(
            overall_score=overall_score,
            rating_label=rating_label,
            mandatory_ratio=mandatory_ratio,
            gap_evaluations=gap_evaluations,
            job_title=jd.job_title,
        )

        return ScoringResult(
            overall_score=overall_score,
            rating_label=rating_label,
            skill_match_score=skill_match_score,
            semantic_score=semantic_score,
            lexical_score=lexical_score,
            experience_score=experience_score,
            domain_score=domain_score,
            scoring_breakdown=scoring_breakdown,
            summary_analysis=summary_analysis,
            gap_evaluations=gap_evaluations,
        )

    def _classify_gap(
        self,
        req: JDRequirement,
        direct_skill: CandidateSkill | None,
        best_sim: float,
        candidate_categories: set[str],
    ) -> tuple[str, str, float, str]:
        """Classifies requirement gap into 4 tiers and assigns severity and action."""
        if direct_skill:
            if direct_skill.is_user_verified:
                status = "DEMONSTRATED"
                severity = "LOW"
                ratio = 1.0
                action = (
                    f"Candidate-verified alignment with competency '{direct_skill.skill_name}'."
                )
            elif direct_skill.evidence_text or best_sim >= 0.55:
                status = "DEMONSTRATED"
                severity = "LOW"
                ratio = 0.90
                action = f"Extracted from resume evidence for '{direct_skill.skill_name}' (candidate verification recommended)."
            else:
                status = "REQUIRES_VERIFICATION"
                severity = "MODERATE" if req.is_mandatory else "LOW"
                ratio = 0.75
                action = f"Skill '{direct_skill.skill_name}' found in profile, but lacks direct evidence in work history. Verify your experience."
        elif best_sim >= 0.60:
            status = "DEMONSTRATED"
            severity = "LOW"
            ratio = 0.90
            action = "Strong textual and technical evidence found in work history."
        elif best_sim >= 0.45:
            status = "PARTIAL"
            severity = "MODERATE" if req.is_mandatory else "LOW"
            ratio = 0.60
            action = f"Add explicit achievements or bullet points detailing your experience with '{req.requirement_text[:40]}...'."
        elif req.category in candidate_categories:
            status = "PARTIAL"
            severity = "MODERATE" if req.is_mandatory else "LOW"
            ratio = 0.50
            action = f"Demonstrated background in {req.category}; specify hands-on tools mentioned in this requirement."
        else:
            status = "NOT_DEMONSTRATED"
            severity = "CRITICAL" if req.is_mandatory else "MODERATE"
            ratio = 0.0
            action = "Requirement not evidenced in resume. Consider completing practical project work or coursework in this competency."

        return status, severity, ratio, action

    def _compute_experience_score(self, resume: Resume, jd: JobDescription) -> float:
        """Evaluates candidate years of experience against JD seniority and requirements."""
        exp_count = sum(
            len(s.items)
            for s in resume.sections
            if "experience" in s.section_type.lower() or "work" in s.section_type.lower()
        )
        if exp_count >= 3:
            base = 92.0
        elif exp_count >= 2:
            base = 85.0
        elif exp_count >= 1:
            base = 75.0
        else:
            base = 65.0

        if jd.seniority_level in ["Senior", "Lead", "Principal", "Staff"] and exp_count < 2:
            base -= 10.0

        return round(min(100.0, max(40.0, base)), 2)

    def _compute_domain_score(
        self, candidate_skills: list[CandidateSkill], jd: JobDescription
    ) -> float:
        """Measures technical domain overlap between candidate profile and JD requirements."""
        if not candidate_skills or not jd.requirements:
            return 75.0

        cand_cats = {s.category for s in candidate_skills}
        jd_cats = {r.category for r in jd.requirements}
        overlap = cand_cats.intersection(jd_cats)

        ratio = len(overlap) / len(jd_cats) if jd_cats else 1.0
        score = 65.0 + (ratio * 35.0)
        return round(min(100.0, max(50.0, score)), 2)

    def _get_rating_label(self, score: float) -> str:
        if score >= 85.0:
            return "Exceptional Alignment"
        elif score >= 75.0:
            return "Strong Alignment"
        elif score >= 60.0:
            return "Moderate Alignment"
        elif score >= 45.0:
            return "Developing Match"
        else:
            return "Significant Gaps"

    def _generate_summary(
        self,
        overall_score: float,
        rating_label: str,
        mandatory_ratio: float,
        gap_evaluations: list[dict[str, Any]],
        job_title: str,
    ) -> str:
        critical_gaps = [
            g["requirement_text"]
            for g in gap_evaluations
            if g["status"] == "NOT_DEMONSTRATED" and g["is_mandatory"]
        ]
        demonstrated_count = sum(1 for g in gap_evaluations if g["status"] == "DEMONSTRATED")

        summary = (
            f"Overall evaluation indicates {rating_label.lower()} ({overall_score}/100) for the {job_title} position. "
            f"Candidate satisfies {int(mandatory_ratio * 100)}% of core mandatory qualifications with "
            f"{demonstrated_count} competencies directly substantiated by resume evidence. "
        )

        if critical_gaps:
            short_gaps = [g[:50] + "..." if len(g) > 50 else g for g in critical_gaps[:2]]
            summary += f"Primary priority gaps to address: {'; '.join(short_gaps)}."
        else:
            summary += "No critical mandatory qualifications were left unaddressed."

        return summary


# Global matching engine instance
hybrid_matching_engine = HybridMatchingEngine()
