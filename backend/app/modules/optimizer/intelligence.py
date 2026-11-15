import re
import uuid
from typing import Any

from app.core.llm import ollama_client
from app.models.candidate import CandidateSkill
from app.models.jd import JobDescription
from app.models.resume import Resume
from app.modules.matching.bm25 import BM25Index, tokenize
from app.modules.matching.dense import dense_matcher
from app.modules.ontology.normalizer import skill_normalizer

APPLIED_ACTION_VERBS = {
    "architected", "built", "created", "designed", "developed", "deployed",
    "engineered", "established", "implemented", "improved", "launched",
    "led", "managed", "optimized", "orchestrated", "reduced", "scaled",
    "spearheaded", "streamlined", "automated", "delivered", "executed",
    "migrated", "maintained", "configured", "administered", "profiled",
    "monitored", "refactored", "integrated", "tested", "debugged",
}

INCIDENTAL_PATTERNS = [
    r"\bfamiliar with\b",
    r"\bexposure to\b",
    r"\bknowledge of\b",
    r"\bcollaborated with (?:the )?([a-z0-9_-]+ )?team\b",
    r"\bassisted\b",
    r"\binterested in\b",
    r"\bstudied\b",
    r"\bcoursework\b",
]


class RequirementEvidenceMapping:
    def __init__(
        self,
        requirement_id: uuid.UUID,
        requirement_text: str,
        is_mandatory: bool,
        canonical_skill_name: str | None,
        category: str | None,
        matched_section_id: str | None = None,
        matched_section_name: str | None = None,
        matched_item_id: str | None = None,
        matched_bullet_index: int | None = None,
        original_evidence_text: str | None = None,
        matching_method: str = "UNMATCHED",
        confidence_score: float = 0.0,
        verification_status: str = "UNMATCHED",  # CANDIDATE_VERIFIED, EXTRACTED_UNCONFIRMED, UNMATCHED
        match_category: str = "MISSING",  # DEMONSTRATED, TRANSFERABLE, PROFILE_LISTED, MISSING
        explanation: str = "",
        requires_human_verification: bool = False,
        suggested_action: str | None = None,
    ):
        self.requirement_id = requirement_id
        self.requirement_text = requirement_text
        self.is_mandatory = is_mandatory
        self.canonical_skill_name = canonical_skill_name
        self.category = category
        self.matched_section_id = matched_section_id
        self.matched_section_name = matched_section_name
        self.matched_item_id = matched_item_id
        self.matched_bullet_index = matched_bullet_index
        self.original_evidence_text = original_evidence_text
        self.matching_method = matching_method
        self.confidence_score = confidence_score
        self.verification_status = verification_status
        self.match_category = match_category
        self.explanation = explanation
        self.requires_human_verification = requires_human_verification
        self.suggested_action = suggested_action

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": str(self.requirement_id),
            "requirement_text": self.requirement_text,
            "is_mandatory": self.is_mandatory,
            "canonical_skill_name": self.canonical_skill_name,
            "category": self.category,
            "matched_section_id": self.matched_section_id,
            "matched_section_name": self.matched_section_name,
            "matched_item_id": self.matched_item_id,
            "matched_bullet_index": self.matched_bullet_index,
            "original_evidence_text": self.original_evidence_text,
            "matching_method": self.matching_method,
            "confidence_score": round(self.confidence_score, 3),
            "verification_status": self.verification_status,
            "match_category": self.match_category,
            "explanation": self.explanation,
            "requires_human_verification": self.requires_human_verification,
            "suggested_action": self.suggested_action,
        }


class ContentSelectionItem:
    def __init__(
        self,
        section_id: str,
        section_type: str,
        heading: str,
        item_id: str | None,
        bullet_index: int | None,
        content_text: str,
        decision: str,  # INCLUDED, PROPOSED_REWRITE, REORDERED, EXCLUDED, MISSING_INFO
        relevance_score: float,
        matched_requirement_ids: list[str],
        reasoning: str,
    ):
        self.section_id = section_id
        self.section_type = section_type
        self.heading = heading
        self.item_id = item_id
        self.bullet_index = bullet_index
        self.content_text = content_text
        self.decision = decision
        self.relevance_score = relevance_score
        self.matched_requirement_ids = matched_requirement_ids
        self.reasoning = reasoning

    def to_dict(self) -> dict[str, Any]:
        return {
            "section_id": self.section_id,
            "section_type": self.section_type,
            "heading": self.heading,
            "item_id": self.item_id,
            "bullet_index": self.bullet_index,
            "content_text": self.content_text,
            "decision": self.decision,
            "relevance_score": round(self.relevance_score, 3),
            "matched_requirement_ids": self.matched_requirement_ids,
            "reasoning": self.reasoning,
        }


class ContentIntelligenceEngine:
    """Content Intelligence & Selection Engine:
    Maps job requirements to candidate resume evidence, categorizes content decisions,
    prioritizes sections, and identifies missing requirements without fabricating facts.
    """

    async def analyze_and_map(
        self,
        resume: Resume,
        jd: JobDescription,
        candidate_skills: list[CandidateSkill],
    ) -> dict[str, Any]:
        """Perform comprehensive requirement-to-evidence mapping and content selection
        using a 4-tier classification taxonomy:
        - DEMONSTRATED: Directly supported by experience/project/internship bullet evidence (sim >= 0.65 or exact match).
        - TRANSFERABLE: Related experience/project with partial relevance (0.40 <= sim < 0.65).
        - PROFILE_LISTED: Listed in candidate profile or skills/certifications inventory without bullet evidence.
        - MISSING: No supporting evidence found in candidate profile or resume.
        """
        # 1. Inspect Ollama status for honest method labeling
        ollama_status = await ollama_client.get_status()
        is_ollama_available = ollama_status.is_available

        # Candidate verified skill index
        verified_skills_map: dict[str, CandidateSkill] = {}
        for s in candidate_skills:
            norm = (s.normalized_name or s.skill_name or "").lower()
            if norm:
                verified_skills_map[norm] = s

        # 2. Collect all candidate snippets with provenance
        candidate_snippets: list[dict[str, Any]] = []

        for sec in resume.sections:
            sec_type = (sec.section_type or "").upper()
            sec_name = sec.heading or sec_type or "Section"

            for item in sec.items:
                item_title = item.title or ""
                item_org = item.organization or ""

                for b_idx, bullet in enumerate(item.bullets or []):
                    b_str = bullet.strip() if isinstance(bullet, str) else str(bullet).strip()
                    if not b_str:
                        continue
                    candidate_snippets.append(
                        {
                            "section_id": str(sec.id),
                            "section_name": sec_name,
                            "section_type": sec_type,
                            "item_id": str(item.id),
                            "item_title": item_title,
                            "item_org": item_org,
                            "bullet_index": b_idx,
                            "text": b_str,
                        }
                    )

            if not sec.items and sec.raw_content:
                candidate_snippets.append(
                    {
                        "section_id": str(sec.id),
                        "section_name": sec_name,
                        "section_type": sec_type,
                        "item_id": None,
                        "item_title": None,
                        "item_org": None,
                        "bullet_index": None,
                        "text": sec.raw_content.strip(),
                    }
                )

        # 3. Requirement-to-Evidence 4-Tier Mapping
        all_requirement_mappings: list[RequirementEvidenceMapping] = []
        requirement_mappings: list[RequirementEvidenceMapping] = []
        missing_requirements: list[dict[str, Any]] = []
        snippet_matched_reqs: dict[str, list[uuid.UUID]] = {}
        snippet_best_sim: dict[str, float] = {}
        demonstrated_skills: list[str] = []

        for req in jd.requirements:
            canonical = (req.canonical_skill_name or "").lower().strip()
            req_text = req.requirement_text
            best_snippet = None
            best_sim = 0.0
            matching_method = "UNMATCHED"

            # 1. Search for snippets containing exact skill/technology mention
            exact_snippets = []
            if canonical:
                for snip in candidate_snippets:
                    snip_lower = snip["text"].lower()
                    if re.search(rf"\b{re.escape(canonical)}\b", snip_lower):
                        exact_snippets.append(snip)

            if exact_snippets:
                # Prioritize employment/experience over projects, over general skills
                def _snip_rank(s: dict[str, Any]) -> int:
                    stype = (s.get("section_type") or "").upper()
                    if any(t in stype for t in ["EXPERIENCE", "WORK", "EMPLOYMENT", "INTERNSHIP"]):
                        return 3
                    if "PROJECT" in stype:
                        return 2
                    return 1

                exact_snippets.sort(key=_snip_rank, reverse=True)
                best_snippet = exact_snippets[0]
                best_sim = 0.88
                matching_method = "RESUME_DIRECT_EVIDENCE"
            elif candidate_snippets:
                # 2. Vector retrieval as a retrieval signal (NOT proof of demonstration)
                sim, matched_text = await dense_matcher.find_best_evidence_match(
                    req_text, [s["text"] for s in candidate_snippets]
                )
                if matched_text and sim >= 0.40:
                    best_sim = sim
                    for s in candidate_snippets:
                        if s["text"] == matched_text:
                            best_snippet = s
                            break
                    matching_method = (
                        "DENSE_OLLAMA_NEURAL" if is_ollama_available else "LEXICAL_HASH_PROJECTION"
                    )
                else:
                    # BM25 token overlap retrieval fallback
                    bm25 = BM25Index()
                    bm25.fit([s["text"] for s in candidate_snippets])
                    q_tokens = tokenize(req_text)
                    if q_tokens and candidate_snippets:
                        lex_scores = [
                            bm25.score_query_against_doc(q_tokens, i)
                            for i in range(len(candidate_snippets))
                        ]
                        max_idx, max_score = max(enumerate(lex_scores), key=lambda x: x[1])
                        if max_score > 0.15:
                            best_snippet = candidate_snippets[max_idx]
                            best_sim = min(
                                0.65,
                                round(0.40 + (max_score / (max_score + 1.0)) * 0.25, 2),
                            )
                            matching_method = "LEXICAL_BM25"

            # 4-Tier Rigorous Classification
            match_category = "MISSING"
            explanation = ""
            requires_human_verification = False
            suggested_action = None
            verification_status = "UNMATCHED"
            confidence_score = 0.0

            if best_snippet and best_sim >= 0.40:
                snip_lower = best_snippet["text"].lower()
                sec_type = (best_snippet.get("section_type") or "").upper()
                is_employment = any(t in sec_type for t in ["EXPERIENCE", "WORK", "EMPLOYMENT", "INTERNSHIP"])
                is_project = "PROJECT" in sec_type
                is_skills_sec = any(t in sec_type for t in ["SKILL", "COMPETENC", "TECHNOLOG", "PROFILE", "CERTIFIC"])

                # Verify exact skill presence in the candidate snippet
                has_exact_skill = False
                if canonical:
                    has_exact_skill = bool(re.search(rf"\b{re.escape(canonical)}\b", snip_lower))

                has_action_verb = any(v in snip_lower for v in APPLIED_ACTION_VERBS)
                is_incidental = any(re.search(pat, snip_lower) for pat in INCIDENTAL_PATTERNS)

                cand_skill = verified_skills_map.get(canonical) if canonical else None
                verification_status = (
                    "CANDIDATE_VERIFIED"
                    if (cand_skill and cand_skill.is_user_verified)
                    else "EXTRACTED_UNCONFIRMED"
                )

                if has_exact_skill and is_employment and has_action_verb and not is_incidental:
                    # Verified direct employment demonstration
                    match_category = "DEMONSTRATED"
                    confidence_score = min(0.95, max(0.85, best_sim))
                    explanation = (
                        f"Directly demonstrated in employment history ({best_snippet['section_name']} - "
                        f"'{best_snippet.get('item_title') or best_snippet['section_name']}') with active engineering bullet evidence."
                    )
                    requires_human_verification = False
                    if canonical and canonical not in demonstrated_skills:
                        demonstrated_skills.append(canonical)

                elif has_exact_skill and is_employment and (is_incidental or not has_action_verb):
                    # Incidental or passive mention in employment
                    match_category = "TRANSFERABLE"
                    confidence_score = 0.60
                    explanation = (
                        f"Mentioned in {best_snippet['section_name']}, but evidence reflects incidental or passive usage "
                        f"rather than primary production engineering ownership."
                    )
                    requires_human_verification = True
                    suggested_action = f"Add achievement metrics demonstrating direct ownership and production impact with {canonical}."

                elif has_exact_skill and is_project:
                    # Academic or personal project context
                    match_category = "TRANSFERABLE"
                    confidence_score = 0.70
                    explanation = (
                        f"Demonstrated in project context ('{best_snippet.get('item_title') or best_snippet['section_name']}'). "
                        "Demonstrates practical hands-on capability, but lacks documented enterprise employment history."
                    )
                    requires_human_verification = True
                    suggested_action = f"Highlight production deployment, volume scale, and business impact for {canonical}."

                elif has_exact_skill and is_skills_sec:
                    # Listed in skills inventory without bullet achievement text
                    match_category = "PROFILE_LISTED"
                    confidence_score = 0.50
                    explanation = (
                        f"Listed in {best_snippet['section_name']}, but lacks supporting achievement bullet in work experience or projects."
                    )
                    requires_human_verification = True
                    suggested_action = f"Add work experience bullet points demonstrating {canonical} to upgrade to DEMONSTRATED."

                else:
                    # Related technology surfaced via dense/lexical similarity (e.g. Python for PySpark, SQL for Snowflake)
                    match_category = "TRANSFERABLE"
                    confidence_score = round(min(0.58, best_sim), 2)
                    explanation = (
                        f"Transferable foundation found in {best_snippet['section_name']} "
                        f"('{best_snippet.get('item_title') or best_snippet['section_name']}'). "
                        f"Candidate possesses related technical foundation (similarity {best_sim:.2f}), "
                        f"but no direct evidence of applied {canonical or req_text}."
                    )
                    requires_human_verification = True
                    suggested_action = (
                        f"Clarify whether your experience with {best_snippet.get('item_title') or 'related technologies'} "
                        f"included direct hands-on use of {canonical or req_text}."
                    )

                mapping = RequirementEvidenceMapping(
                    requirement_id=req.id,
                    requirement_text=req_text,
                    is_mandatory=req.is_mandatory,
                    canonical_skill_name=req.canonical_skill_name,
                    category=req.category,
                    matched_section_id=best_snippet["section_id"],
                    matched_section_name=best_snippet["section_name"],
                    matched_item_id=best_snippet["item_id"],
                    matched_bullet_index=best_snippet["bullet_index"],
                    original_evidence_text=best_snippet["text"],
                    matching_method=matching_method,
                    confidence_score=confidence_score,
                    verification_status=verification_status,
                    match_category=match_category,
                    explanation=explanation,
                    requires_human_verification=requires_human_verification,
                    suggested_action=suggested_action,
                )
                requirement_mappings.append(mapping)
                all_requirement_mappings.append(mapping)

                snip_key = f"{best_snippet['section_id']}_{best_snippet['item_id']}_{best_snippet['bullet_index']}"
                snippet_matched_reqs.setdefault(snip_key, []).append(req.id)
                snippet_best_sim[snip_key] = max(
                    snippet_best_sim.get(snip_key, 0.0), confidence_score
                )

            else:
                # Check candidate profile skills
                cand_skill = verified_skills_map.get(canonical) if canonical else None
                if not cand_skill:
                    for s_norm, s_obj in verified_skills_map.items():
                        if s_norm in req_text.lower():
                            cand_skill = s_obj
                            canonical = s_norm
                            break

                if cand_skill:
                    match_category = "PROFILE_LISTED"
                    matching_method = "PROFILE_SKILL_INVENTORY"
                    confidence_score = 0.50
                    verification_status = (
                        "CANDIDATE_VERIFIED"
                        if cand_skill.is_user_verified
                        else "EXTRACTED_UNCONFIRMED"
                    )
                    explanation = (
                        f"Found in candidate profile skills ('{cand_skill.skill_name}'), "
                        "but lacks supporting achievement bullet in work experience or projects."
                    )
                    requires_human_verification = True
                    suggested_action = (
                        f"Add work experience or project bullet points demonstrating {cand_skill.skill_name} "
                        "to upgrade to DEMONSTRATED."
                    )

                    mapping = RequirementEvidenceMapping(
                        requirement_id=req.id,
                        requirement_text=req_text,
                        is_mandatory=req.is_mandatory,
                        canonical_skill_name=req.canonical_skill_name or cand_skill.skill_name,
                        category=req.category,
                        matched_section_id=None,
                        matched_section_name="Master Skills Profile",
                        matched_item_id=None,
                        matched_bullet_index=None,
                        original_evidence_text=f"Candidate Profile: {cand_skill.skill_name} ({cand_skill.proficiency_level or 'developing'})",
                        matching_method=matching_method,
                        confidence_score=confidence_score,
                        verification_status=verification_status,
                        match_category=match_category,
                        explanation=explanation,
                        requires_human_verification=requires_human_verification,
                        suggested_action=suggested_action,
                    )
                    requirement_mappings.append(mapping)
                    all_requirement_mappings.append(mapping)
                else:
                    # Truly missing requirement
                    match_category = "MISSING"
                    matching_method = "UNMATCHED"
                    explanation = (
                        f"No direct or transferable evidence found in candidate resume or profile for '{req_text}'."
                    )
                    suggested_action = (
                        f"Add project experience demonstrating {req.canonical_skill_name or 'this requirement'} "
                        "in your Master Profile or resume; do not fabricate unverified claims."
                    )

                    missing_mapping = RequirementEvidenceMapping(
                        requirement_id=req.id,
                        requirement_text=req_text,
                        is_mandatory=req.is_mandatory,
                        canonical_skill_name=req.canonical_skill_name,
                        category=req.category,
                        matched_section_id=None,
                        matched_section_name=None,
                        matched_item_id=None,
                        matched_bullet_index=None,
                        original_evidence_text=None,
                        matching_method=matching_method,
                        confidence_score=0.0,
                        verification_status="UNMATCHED",
                        match_category=match_category,
                        explanation=explanation,
                        requires_human_verification=True,
                        suggested_action=suggested_action,
                    )
                    all_requirement_mappings.append(missing_mapping)

                    missing_requirements.append(
                        {
                            "requirement_id": str(req.id),
                            "requirement_text": req_text,
                            "is_mandatory": req.is_mandatory,
                            "canonical_skill_name": req.canonical_skill_name,
                            "category": req.category,
                            "match_category": "MISSING",
                            "explanation": explanation,
                            "suggested_action": suggested_action,
                        }
                    )

        # 4. Content Selection Categorization
        content_decisions: list[ContentSelectionItem] = []

        for snip in candidate_snippets:
            snip_key = f"{snip['section_id']}_{snip['item_id']}_{snip['bullet_index']}"
            matched_reqs = snippet_matched_reqs.get(snip_key, [])
            sim = snippet_best_sim.get(snip_key, 0.0)
            sec_type = snip["section_type"]

            if (
                any(t in sec_type for t in ["EXPERIENCE", "WORK", "PROJECT", "INTERNSHIP", "LEADERSHIP"])
                and snip["bullet_index"] is not None
            ):
                if matched_reqs and sim >= 0.50:
                    decision = "PROPOSED_REWRITE"
                    reasoning = (
                        "Directly demonstrates target requirement(s); selected for active role tailoring."
                    )
                elif len(snip["text"]) > 25:
                    decision = "INCLUDED"
                    reasoning = (
                        "Foundational background evidence; included in tailored experience record."
                    )
                else:
                    decision = "EXCLUDED"
                    reasoning = (
                        "Fragment or low contextual density; omitted from primary tailoring focus."
                    )
            elif "SKILL" in sec_type:
                decision = "REORDERED"
                reasoning = (
                    "Prioritized target role competencies to the front of skills inventory."
                )
            else:
                decision = "INCLUDED"
                reasoning = (
                    "Core structural resume element (education, credentials, profile summary)."
                )

            content_decisions.append(
                ContentSelectionItem(
                    section_id=snip["section_id"],
                    section_type=snip["section_type"],
                    heading=snip["section_name"],
                    item_id=snip["item_id"],
                    bullet_index=snip["bullet_index"],
                    content_text=snip["text"],
                    decision=decision,
                    relevance_score=sim,
                    matched_requirement_ids=[str(r) for r in matched_reqs],
                    reasoning=reasoning,
                )
            )

        # 5. Generate Role-Specific Professional Summary
        role_summary = self.generate_role_summary(
            resume=resume,
            jd=jd,
            candidate_skills=candidate_skills,
            demonstrated_skills=demonstrated_skills,
        )

        demonstrated_count = sum(
            1 for m in all_requirement_mappings if m.match_category == "DEMONSTRATED"
        )
        transferable_count = sum(
            1 for m in all_requirement_mappings if m.match_category == "TRANSFERABLE"
        )
        profile_listed_count = sum(
            1 for m in all_requirement_mappings if m.match_category == "PROFILE_LISTED"
        )
        missing_count = sum(
            1 for m in all_requirement_mappings if m.match_category == "MISSING"
        )

        return {
            "requirement_mappings": [m.to_dict() for m in requirement_mappings],
            "all_requirement_mappings": [m.to_dict() for m in all_requirement_mappings],
            "missing_requirements": missing_requirements,
            "content_decisions": [c.to_dict() for c in content_decisions],
            "role_summary": role_summary,
            "four_tier_breakdown": {
                "DEMONSTRATED": [
                    m.to_dict()
                    for m in all_requirement_mappings
                    if m.match_category == "DEMONSTRATED"
                ],
                "TRANSFERABLE": [
                    m.to_dict()
                    for m in all_requirement_mappings
                    if m.match_category == "TRANSFERABLE"
                ],
                "PROFILE_LISTED": [
                    m.to_dict()
                    for m in all_requirement_mappings
                    if m.match_category == "PROFILE_LISTED"
                ],
                "MISSING": [
                    m.to_dict()
                    for m in all_requirement_mappings
                    if m.match_category == "MISSING"
                ],
            },
            "summary": {
                "total_requirements": len(jd.requirements),
                "demonstrated_count": demonstrated_count,
                "transferable_count": transferable_count,
                "profile_listed_count": profile_listed_count,
                "missing_count": missing_count,
                "matched_count": len(requirement_mappings),
                "proposed_rewrites_count": sum(
                    1 for c in content_decisions if c.decision == "PROPOSED_REWRITE"
                ),
                "included_count": sum(
                    1
                    for c in content_decisions
                    if c.decision in ["INCLUDED", "REORDERED"]
                ),
            },
        }

    def generate_role_summary(
        self,
        resume: Resume,
        jd: JobDescription,
        candidate_skills: list[CandidateSkill],
        demonstrated_skills: list[str],
    ) -> str:
        """Generate a factual, role-aligned professional summary grounded strictly in candidate evidence."""
        target_role = jd.job_title or "Software Professional"
        company = jd.company_name or ""

        # Pick top demonstrated skills
        top_skills = [s.title() for s in demonstrated_skills[:4] if s]
        if not top_skills:
            # Fall back to verified candidate skills
            top_skills = [
                s.skill_name.title() for s in candidate_skills if s.is_user_verified
            ][:4]

        skills_phrase = (
            ", ".join(top_skills[:-1]) + f", and {top_skills[-1]}"
            if len(top_skills) > 1
            else (top_skills[0] if top_skills else "modern software engineering practices")
        )

        # Check total experience items
        exp_count = sum(
            len(sec.items)
            for sec in resume.sections
            if any(
                t in (sec.section_type or "").lower()
                for t in ["experience", "work", "project", "internship", "leadership"]
            )
        )
        exp_descriptor = "Experienced" if exp_count >= 3 else "Results-oriented"

        target_phrase = f" for {company}" if company else ""
        return (
            f"{exp_descriptor} {target_role} with demonstrated technical expertise across {skills_phrase}. "
            f"Proven track record of designing reliable architectures, driving engineering velocity, and delivering measurable impact. "
            f"Aligned with core technical competencies and production standards required{target_phrase}."
        )


# Global content intelligence instance
content_intelligence = ContentIntelligenceEngine()
