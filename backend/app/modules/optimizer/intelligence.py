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
        """Perform comprehensive requirement-to-evidence mapping and content selection."""
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

        # 3. Requirement-to-Evidence Mapping
        requirement_mappings: list[RequirementEvidenceMapping] = []
        missing_requirements: list[dict[str, Any]] = []
        snippet_matched_reqs: dict[str, list[uuid.UUID]] = {}
        snippet_best_sim: dict[str, float] = {}

        for req in jd.requirements:
            canonical = (req.canonical_skill_name or "").lower()
            req_text = req.requirement_text
            best_snippet = None
            best_sim = 0.0
            matching_method = "UNMATCHED"

            # Check direct ontology match in candidate snippets
            if canonical:
                for snip in candidate_snippets:
                    snip_lower = snip["text"].lower()
                    if re.search(rf"\b{re.escape(canonical)}\b", snip_lower):
                        best_snippet = snip
                        best_sim = 0.90
                        matching_method = "ONTOLOGY_EXACT"
                        break

            # If no exact ontology match, try dense semantic matching
            if not best_snippet and candidate_snippets:
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
                        "DENSE_OLLAMA" if is_ollama_available else "DENSE_HASH_FALLBACK"
                    )
                else:
                    # Try lexical BM25 token overlap fallback
                    bm25 = BM25Index()
                    bm25.fit([s["text"] for s in candidate_snippets])
                    q_tokens = tokenize(req_text)
                    if q_tokens and candidate_snippets:
                        lex_scores = [bm25.score_query_against_doc(q_tokens, i) for i in range(len(candidate_snippets))]
                        max_idx, max_score = max(enumerate(lex_scores), key=lambda x: x[1])
                        if max_score > 0.15:
                            best_snippet = candidate_snippets[max_idx]
                            best_sim = min(0.85, round(0.40 + (max_score / (max_score + 1.0)) * 0.45, 2))
                            matching_method = "LEXICAL_BM25_FALLBACK"

            if best_snippet and best_sim >= 0.40:
                # Determine verification status
                cand_skill = verified_skills_map.get(canonical) if canonical else None
                if not cand_skill:
                    # Check if any verified skill token matches
                    extracted = skill_normalizer.extract_skills_from_text(best_snippet["text"])
                    for ext in extracted:
                        c_name = ext["canonical_name"].lower()
                        if c_name in verified_skills_map and verified_skills_map[c_name].is_user_verified:
                            cand_skill = verified_skills_map[c_name]
                            break

                verification_status = (
                    "CANDIDATE_VERIFIED"
                    if (cand_skill and cand_skill.is_user_verified)
                    else "EXTRACTED_UNCONFIRMED"
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
                    confidence_score=best_sim,
                    verification_status=verification_status,
                )
                requirement_mappings.append(mapping)

                snip_key = f"{best_snippet['section_id']}_{best_snippet['item_id']}_{best_snippet['bullet_index']}"
                snippet_matched_reqs.setdefault(snip_key, []).append(req.id)
                snippet_best_sim[snip_key] = max(snippet_best_sim.get(snip_key, 0.0), best_sim)
            else:
                # Unmatched requirement -> flag as missing info (NO FABRICATION)
                missing_requirements.append(
                    {
                        "requirement_id": str(req.id),
                        "requirement_text": req_text,
                        "is_mandatory": req.is_mandatory,
                        "canonical_skill_name": req.canonical_skill_name,
                        "category": req.category,
                        "suggested_action": (
                            f"Add project experience demonstrating {req.canonical_skill_name or 'this requirement'} "
                            "in your Master Profile or resume; do not fabricate unverified claims."
                        ),
                    }
                )

        # 4. Content Selection Categorization
        content_decisions: list[ContentSelectionItem] = []

        for snip in candidate_snippets:
            snip_key = f"{snip['section_id']}_{snip['item_id']}_{snip['bullet_index']}"
            matched_reqs = snippet_matched_reqs.get(snip_key, [])
            sim = snippet_best_sim.get(snip_key, 0.0)
            sec_type = snip["section_type"]

            if ("EXPERIENCE" in sec_type or "PROJECT" in sec_type) and snip["bullet_index"] is not None:
                if matched_reqs and sim >= 0.50:
                    decision = "PROPOSED_REWRITE"
                    reasoning = "Directly demonstrates target requirement(s); selected for active role tailoring."
                elif len(snip["text"]) > 25:
                    decision = "INCLUDED"
                    reasoning = "Foundational background evidence; included in tailored experience record."
                else:
                    decision = "EXCLUDED"
                    reasoning = "Fragment or low contextual density; omitted from primary tailoring focus."
            elif "SKILL" in sec_type:
                decision = "REORDERED"
                reasoning = "Prioritized target role competencies to the front of skills inventory."
            else:
                decision = "INCLUDED"
                reasoning = "Core structural resume element (education, credentials, profile summary)."

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

        return {
            "requirement_mappings": [m.to_dict() for m in requirement_mappings],
            "missing_requirements": missing_requirements,
            "content_decisions": [c.to_dict() for c in content_decisions],
            "summary": {
                "total_requirements": len(jd.requirements),
                "matched_count": len(requirement_mappings),
                "missing_count": len(missing_requirements),
                "proposed_rewrites_count": sum(1 for c in content_decisions if c.decision == "PROPOSED_REWRITE"),
                "included_count": sum(1 for c in content_decisions if c.decision in ["INCLUDED", "REORDERED"]),
            },
        }


# Global content intelligence instance
content_intelligence = ContentIntelligenceEngine()
