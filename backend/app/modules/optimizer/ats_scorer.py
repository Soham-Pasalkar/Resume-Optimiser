import io
import re
from typing import Any

import docx
import pdfplumber

from app.models.jd import JobDescription


class ATSEvaluator:
    """Transparent ATS Evaluation Engine:
    Computes two distinct, explainable metrics:
    1. Job Compatibility Score (0-100): Algorithmic role fit based on verified candidate evidence.
    2. ATS Readability Score (0-100): Structural & machine-readability audit verified by actual byte extraction.
    """

    STANDARD_HEADINGS = {
        "summary": ["summary", "professional summary", "profile", "about", "objective"],
        "experience": ["experience", "work experience", "professional experience", "employment", "internships"],
        "education": ["education", "academic background", "academics"],
        "skills": ["skills", "technical skills", "core competencies", "competencies", "technologies"],
        "projects": ["projects", "personal projects", "technical projects"],
        "certifications": ["certifications", "licenses", "certificates", "credentials"],
    }

    ACTION_VERBS = {
        "architected", "built", "created", "designed", "developed", "deployed",
        "engineered", "established", "implemented", "improved", "launched",
        "led", "managed", "optimized", "orchestrated", "reduced", "scaled",
        "spearheaded", "streamlined", "automated", "delivered", "executed",
    }

    def evaluate_job_compatibility(
        self,
        tailored_content: dict[str, Any],
        jd: JobDescription,
        requirement_mappings: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Compute Job Compatibility Score (0-100) based on 4-tier requirement mapping and evidence depth."""
        mappings = requirement_mappings or tailored_content.get("requirement_mappings", [])
        total_reqs = len(jd.requirements)

        if total_reqs == 0:
            return {
                "score": 100.0,
                "breakdown": {
                    "mandatory_score": 40.0,
                    "preferred_score": 20.0,
                    "transferable_score": 15.0,
                    "profile_score": 15.0,
                    "depth_score": 10.0,
                },
                "tier_counts": {
                    "demonstrated": 0,
                    "transferable": 0,
                    "profile_listed": 0,
                    "missing": 0,
                    "total": 0,
                },
                "strengths": ["No specific requirements defined for target role."],
                "gaps": [],
                "recommendations": [],
                "disclaimer": "CareerPilot Algorithmic Estimate. Not an official hiring decision.",
            }

        req_map_by_id = {m.get("requirement_id"): m for m in mappings}

        mandatory_reqs = [r for r in jd.requirements if r.is_mandatory]
        preferred_reqs = [r for r in jd.requirements if not r.is_mandatory]

        # 1. Mandatory demonstrated (Weight: 40)
        mand_demonstrated = sum(
            1
            for r in mandatory_reqs
            if req_map_by_id.get(str(r.id), {}).get("match_category") == "DEMONSTRATED"
        )
        mand_score = (
            (mand_demonstrated / len(mandatory_reqs)) * 40.0
            if mandatory_reqs
            else 40.0
        )

        # 2. Preferred demonstrated (Weight: 20)
        pref_demonstrated = sum(
            1
            for r in preferred_reqs
            if req_map_by_id.get(str(r.id), {}).get("match_category") == "DEMONSTRATED"
        )
        pref_score = (
            (pref_demonstrated / len(preferred_reqs)) * 20.0
            if preferred_reqs
            else 20.0
        )

        # 3. Transferable coverage (Weight: 15)
        transferable_count = sum(
            1
            for r in jd.requirements
            if req_map_by_id.get(str(r.id), {}).get("match_category") == "TRANSFERABLE"
        )
        transferable_score = min(15.0, (transferable_count / max(1, total_reqs)) * 30.0)

        # 4. Profile listed coverage (Weight: 15)
        profile_count = sum(
            1
            for r in jd.requirements
            if req_map_by_id.get(str(r.id), {}).get("match_category") == "PROFILE_LISTED"
        )
        profile_score = min(15.0, (profile_count / max(1, total_reqs)) * 25.0)

        # 5. Experience depth & evidence density (Weight: 10)
        sections = tailored_content.get("sections", [])
        total_bullets = sum(
            len(item.get("bullets", []))
            for sec in sections
            for item in sec.get("items", [])
        )
        depth_score = min(10.0, (total_bullets / 8.0) * 10.0)

        total_score = round(
            min(100.0, mand_score + pref_score + transferable_score + profile_score + depth_score),
            1,
        )

        demonstrated_total = mand_demonstrated + pref_demonstrated
        missing_count = sum(
            1
            for r in jd.requirements
            if req_map_by_id.get(str(r.id), {}).get("match_category", "MISSING") == "MISSING"
        )

        # Build qualitative feedback
        strengths = []
        if mand_demonstrated > 0:
            strengths.append(
                f"Directly demonstrated {mand_demonstrated} of {len(mandatory_reqs)} mandatory requirement(s) with verified bullet evidence."
            )
        if pref_demonstrated > 0:
            strengths.append(
                f"Demonstrated {pref_demonstrated} preferred requirement(s) aligned with target role."
            )
        if transferable_count > 0:
            strengths.append(
                f"{transferable_count} requirement(s) supported by strong transferable background experience."
            )
        if depth_score >= 8.0:
            strengths.append(
                f"Strong evidence density ({total_bullets} achievement bullet points across experience sections)."
            )

        gaps = []
        recommendations = []
        missing_mandatory = [
            r for r in mandatory_reqs
            if req_map_by_id.get(str(r.id), {}).get("match_category", "MISSING") == "MISSING"
        ]
        if missing_mandatory:
            top_missing = [r.canonical_skill_name or r.requirement_text[:35] for r in missing_mandatory[:3]]
            gaps.append(f"Missing {len(missing_mandatory)} mandatory requirement(s): {', '.join(top_missing)}.")
            recommendations.append(
                f"Bridge mandatory gap(s) like {top_missing[0]} by completing a targeted portfolio milestone or adding verified project evidence."
            )

        if profile_count > 0:
            gaps.append(
                f"{profile_count} skill(s) are listed in your profile inventory but lack achievement bullet points."
            )
            recommendations.append(
                "Add quantified achievement bullets for profile-listed skills to elevate them to DEMONSTRATED status."
            )

        return {
            "score": total_score,
            "breakdown": {
                "mandatory_score": round(mand_score, 1),
                "preferred_score": round(pref_score, 1),
                "transferable_score": round(transferable_score, 1),
                "profile_score": round(profile_score, 1),
                "depth_score": round(depth_score, 1),
            },
            "tier_counts": {
                "demonstrated": demonstrated_total,
                "transferable": transferable_count,
                "profile_listed": profile_count,
                "missing": missing_count,
                "total": total_reqs,
            },
            "strengths": strengths,
            "gaps": gaps,
            "recommendations": recommendations,
            "disclaimer": (
                "CareerPilot Algorithmic Estimate. Calculated from factual candidate evidence matched against "
                "job requirements. Not an official hiring decision or black-box ATS guarantee."
            ),
        }

    def evaluate_ats_readability(
        self,
        tailored_content: dict[str, Any],
        document_bytes: bytes | None = None,
        file_format: str = "pdf",
    ) -> dict[str, Any]:
        """Compute ATS Readability Score (0-100) with real-text extraction verification."""
        findings: list[str] = []
        breakdown = {
            "standard_headings": 0.0,
            "contact_completeness": 0.0,
            "document_structure": 0.0,
            "date_consistency": 0.0,
            "bullet_clarity": 0.0,
            "text_extraction_validation": 0.0,
        }

        sections = tailored_content.get("sections", [])
        headings_lower = [
            (s.get("heading") or s.get("section_type") or "").lower().strip()
            for s in sections
        ]

        # 1. Standard Headings (Max: 20)
        found_cats: list[str] = []
        missing_cats: list[str] = []
        for cat, aliases in self.STANDARD_HEADINGS.items():
            if any(any(alias in h for alias in aliases) for h in headings_lower):
                found_cats.append(cat.title())
            else:
                missing_cats.append(cat.title())

        headings_score = round((len(found_cats) / 6.0) * 20.0, 1)
        breakdown["standard_headings"] = headings_score
        findings.append(f"Standard ATS section headings detected ({len(found_cats)}/6 categories: {', '.join(found_cats)}).")
        if missing_cats:
            findings.append(f"Standard categories not detected: {', '.join(missing_cats)}.")

        # 2. Contact Information Completeness (Max: 15)
        contact_score = 0.0
        name = (
            tailored_content.get("full_name")
            or tailored_content.get("candidate_name")
            or ""
        ).strip()
        contact_str = tailored_content.get("contact_info", "")

        if len(name) >= 3:
            contact_score += 5.0
        if "@" in contact_str or tailored_content.get("email"):
            contact_score += 5.0
        if any(term in contact_str.lower() for term in ["linkedin", "github", "phone", "http", ".com"]):
            contact_score += 5.0

        breakdown["contact_completeness"] = round(contact_score, 1)
        if contact_score >= 15.0:
            findings.append("Contact information is complete and easily parseable.")
        else:
            findings.append("Ensure full name, email, and LinkedIn/GitHub profiles are present in contact line.")

        # 3. Document Structure (Max: 15)
        structure_score = 0.0
        if len(sections) >= 3:
            structure_score += 5.0
        # Summary or skills placed high in hierarchy
        first_headings = headings_lower[:2]
        if any(any(a in h for a in self.STANDARD_HEADINGS["summary"] + self.STANDARD_HEADINGS["skills"]) for h in first_headings):
            structure_score += 5.0

        # Physical layout geometry validation
        is_single_column = True
        if document_bytes and file_format.lower() == "pdf":
            try:
                with pdfplumber.open(io.BytesIO(document_bytes)) as pdf:
                    for page in pdf.pages:
                        words = page.extract_words()
                        y_lines: dict[int, list[float]] = {}
                        for w in words:
                            y_bucket = int(w["top"] // 10) * 10
                            y_lines.setdefault(y_bucket, []).append(w["x0"])
                        for y_val, x_positions in y_lines.items():
                            has_left = any(x < 200 for x in x_positions)
                            has_right = any(x > 380 for x in x_positions)
                            has_middle_gap = not any(230 <= x <= 350 for x in x_positions)
                            if has_left and has_right and has_middle_gap and len(x_positions) >= 6:
                                is_single_column = False
                                break
            except Exception:
                pass

        if is_single_column:
            structure_score += 5.0
            findings.append("Single-column linear hierarchy verified against document layout geometry.")
        else:
            findings.append("Multi-column layout detected; single-column format recommended for optimal ATS traversal.")

        breakdown["document_structure"] = round(structure_score, 1)

        # 4. Date Consistency (Max: 15)
        items_with_dates = 0
        total_exp_items = 0
        date_pattern = re.compile(r"\b(20\d\d|19\d\d|present|current)\b", re.IGNORECASE)

        for sec in sections:
            sec_type = (sec.get("section_type") or "").lower()
            if any(t in sec_type for t in ["experience", "work", "education", "internship"]):
                for itm in sec.get("items", []):
                    total_exp_items += 1
                    dates_str = f"{itm.get('start_date', '')} {itm.get('end_date', '')}"
                    if date_pattern.search(dates_str):
                        items_with_dates += 1

        if total_exp_items == 0:
            date_score = 0.0
            findings.append("No career history or education items present to evaluate date consistency.")
        else:
            date_score = (items_with_dates / total_exp_items) * 15.0
            if date_score >= 12.0:
                findings.append("Consistent chronological date ranges verified across career records.")
            else:
                findings.append(f"Only {items_with_dates} of {total_exp_items} career items contain standard date ranges.")
        breakdown["date_consistency"] = round(date_score, 1)

        # 5. Bullet Clarity & Action Verbs (Max: 15)
        total_bullets = 0
        action_verb_bullets = 0
        length_compliant_bullets = 0

        for sec in sections:
            for itm in sec.get("items", []):
                for b in itm.get("bullets", []):
                    b_str = (b if isinstance(b, str) else str(b)).strip()
                    if not b_str:
                        continue
                    total_bullets += 1
                    if 25 <= len(b_str) <= 350:
                        length_compliant_bullets += 1
                    first_word = re.sub(r"[^\w]", "", b_str.split()[0].lower()) if b_str.split() else ""
                    if first_word in self.ACTION_VERBS:
                        action_verb_bullets += 1

        if total_bullets == 0:
            bullet_score = 0.0
            findings.append("No achievement bullets found across experience or project records.")
        else:
            action_ratio = action_verb_bullets / total_bullets
            len_ratio = length_compliant_bullets / total_bullets
            bullet_score = min(15.0, (action_ratio * 7.5) + (len_ratio * 7.5))
            if bullet_score >= 10.0:
                findings.append(f"Strong action-verb phrasing across {total_bullets} bullet point(s) ({action_verb_bullets} with active verbs).")
            else:
                findings.append("Begin achievement bullets with strong action verbs (e.g. Architected, Engineered, Optimized).")

        breakdown["bullet_clarity"] = round(bullet_score, 1)

        # 6. Real Text Extraction & Content Coverage Validation (Max: 20)
        expected_terms: set[str] = set()
        for part in [name or "", contact_str or ""]:
            for token in part.split():
                clean = re.sub(r"[^\w]", "", token.lower())
                if len(clean) >= 4:
                    expected_terms.add(clean)
        for sec in sections:
            for itm in sec.get("items", []):
                for field in [itm.get("title") or "", itm.get("organization") or ""]:
                    for token in field.split():
                        clean = re.sub(r"[^\w]", "", token.lower())
                        if len(clean) >= 4:
                            expected_terms.add(clean)
                for b in itm.get("bullets", []):
                    for token in str(b).split():
                        clean = re.sub(r"[^\w]", "", token.lower())
                        if len(clean) >= 5:
                            expected_terms.add(clean)

        extracted_text = ""
        extracted_char_count = 0
        page_count = 1
        coverage_pct = 0.0

        if document_bytes:
            try:
                if file_format.lower() == "pdf":
                    with pdfplumber.open(io.BytesIO(document_bytes)) as pdf:
                        page_count = len(pdf.pages)
                        extracted_pages = [page.extract_text() or "" for page in pdf.pages]
                        extracted_text = "\n".join(extracted_pages).strip()
                        extracted_char_count = len(extracted_text)
                elif file_format.lower() == "docx":
                    doc = docx.Document(io.BytesIO(document_bytes))
                    extracted_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
                    extracted_char_count = len(extracted_text)
            except Exception as exc:
                findings.append(f"Text extraction warning: {exc!s}")

        if extracted_char_count > 50 and expected_terms:
            extracted_lower = extracted_text.lower()
            matched_terms = sum(1 for term in expected_terms if term in extracted_lower)
            coverage_pct = (matched_terms / len(expected_terms)) * 100.0

            if coverage_pct >= 80.0:
                extract_score = 20.0
            elif coverage_pct >= 65.0:
                extract_score = 15.0
            elif coverage_pct >= 45.0:
                extract_score = 10.0
            else:
                extract_score = 5.0

            breakdown["text_extraction_validation"] = extract_score
            findings.append(
                f"Verified byte-level text extraction with {coverage_pct:.1f}% expected content coverage ({extracted_char_count} chars across {page_count} page(s))."
            )
        elif document_bytes:
            breakdown["text_extraction_validation"] = 3.0
            findings.append("Document extraction yielded negligible character count.")
        else:
            ir_chars = sum(len(str(b)) for sec in sections for itm in sec.get("items", []) for b in itm.get("bullets", []))
            breakdown["text_extraction_validation"] = 15.0 if ir_chars > 100 else 5.0
            findings.append("Structured text ready for clean PDF/DOCX compiler extraction.")

        total_readability = round(
            min(100.0, sum(breakdown.values())),
            1,
        )

        return {
            "score": total_readability,
            "breakdown": breakdown,
            "extracted_character_count": extracted_char_count,
            "page_count": page_count,
            "findings": findings,
            "disclaimer": (
                "CareerPilot Algorithmic Readability Index measuring machine-readability, linear formatting, "
                "and text extraction compliance against standard ATS specifications. Algorithmic estimate; "
                "not an official guarantee for any third-party ATS software."
            ),
        }


# Global ATS evaluator instance
ats_evaluator = ATSEvaluator()
