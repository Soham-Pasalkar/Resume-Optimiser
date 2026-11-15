import datetime
from typing import Any

from app.models.optimizer import TailoredBulletDiff, TailoredResume


class ResumeComposer:
    """Resume Composition Engine:
    Assembles a job-tailored resume into a structured Intermediate Representation (IR),
    integrating candidate review decisions (accepted rewrites, rejected defaults, custom edits,
    and restored originals), maintaining end-to-end source provenance and section ordering.
    """

    def build_composition_ir(
        self,
        tailored: TailoredResume,
        diffs: list[TailoredBulletDiff],
    ) -> dict[str, Any]:
        """Construct the complete Intermediate Representation (IR) from current state."""
        content = tailored.tailored_content or {}
        candidate_identity = {
            "full_name": content.get("full_name") or content.get("candidate_name") or "Candidate Profile",
            "candidate_name": content.get("candidate_name") or content.get("full_name") or "Candidate Profile",
            "contact_info": content.get("contact_info") or "Verified Candidate Profile • CareerPilot Intelligence",
            "email": content.get("email"),
            "headline": content.get("headline"),
            "location": content.get("location"),
            "linkedin_url": content.get("linkedin_url"),
            "github_url": content.get("github_url"),
            "portfolio_url": content.get("portfolio_url"),
        }

        # Index diffs by (section_id, item_id, bullet_index) and by diff.id
        diff_by_coord: dict[tuple[str, str, int], TailoredBulletDiff] = {}
        diff_by_id: dict[str, TailoredBulletDiff] = {}
        for d in diffs:
            diff_by_id[str(d.id)] = d
            sec_id = d.section_id or ""
            itm_id = d.item_id or ""
            diff_by_coord[(sec_id, itm_id, d.bullet_index)] = d

        sections_input = list(content.get("sections", []))
        role_summary = (content.get("role_summary") or "").strip()

        # Insert or update role-aligned professional summary section
        if role_summary:
            existing_summary = next(
                (
                    s
                    for s in sections_input
                    if (s.get("section_type") or "").upper() == "SUMMARY"
                    or "summary" in (s.get("heading") or "").lower()
                ),
                None,
            )
            if existing_summary:
                existing_summary["raw_content"] = role_summary
                existing_summary["selection_reason"] = "Role-aligned professional summary synthesized from verified competencies."
            else:
                sections_input.insert(
                    0,
                    {
                        "id": "sec_role_summary",
                        "section_type": "SUMMARY",
                        "heading": "Professional Summary",
                        "is_included": True,
                        "display_order": 1,
                        "raw_content": role_summary,
                        "items": [],
                        "selection_reason": "Role-aligned professional summary synthesized from verified candidate competencies.",
                    },
                )

        SECTION_PRIORITY = {
            "SUMMARY": 1,
            "SKILLS": 2,
            "EXPERIENCE": 3,
            "WORK": 3,
            "PROJECTS": 4,
            "PROJECT": 4,
            "EDUCATION": 5,
            "CERTIFICATIONS": 6,
            "CERTIFICATION": 6,
            "ACHIEVEMENTS": 7,
            "PUBLICATIONS": 8,
            "LEADERSHIP": 9,
            "GENERAL": 10,
        }

        composed_sections: list[dict[str, Any]] = []
        provenance_records: list[dict[str, Any]] = []

        total_diffs = len(diffs)
        applied_diffs = 0
        edited_diffs = 0
        rejected_diffs = 0

        for sec_idx, sec in enumerate(sections_input):
            sec_id = str(sec.get("id") or f"sec_{sec_idx}")
            is_included = sec.get("is_included", True)
            sec_type = (sec.get("section_type") or "GENERAL").upper()
            heading = sec.get("heading") or sec_type.title()

            # Assign natural ATS priority order if display_order is default sequential
            default_prio = SECTION_PRIORITY.get(sec_type, 10)
            display_order = sec.get("display_order", default_prio)

            section_reason = sec.get("selection_reason") or (
                f"Curated {heading} section aligned with target opportunity requirements."
            )

            composed_items: list[dict[str, Any]] = []

            for item_idx, item in enumerate(sec.get("items", [])):
                item_id = str(item.get("id") or f"item_{sec_idx}_{item_idx}")
                title = item.get("title", "")
                org = item.get("organization", "")
                loc = item.get("location", "")
                start_date = item.get("start_date", "")
                end_date = item.get("end_date", "")
                is_current = item.get("is_current", False)

                composed_bullets: list[dict[str, Any]] = []

                for b_idx, bullet in enumerate(item.get("bullets", [])):
                    orig_text = bullet if isinstance(bullet, str) else str(bullet)
                    diff = diff_by_coord.get((sec_id, item_id, b_idx))

                    final_text = orig_text
                    source_status = "ORIGINAL"
                    diff_id = None
                    req_id = None
                    nli_status = "VERIFIED"

                    if diff:
                        diff_id = str(diff.id)
                        req_id = str(diff.targeted_requirement_id) if diff.targeted_requirement_id else None
                        nli_status = diff.nli_verification_status

                        if diff.status == "ACCEPTED":
                            final_text = diff.optimized_text
                            source_status = "ACCEPTED_REWRITE"
                            applied_diffs += 1
                        elif diff.status == "EDITED" and diff.edited_text:
                            final_text = diff.edited_text
                            source_status = "CANDIDATE_EDIT"
                            edited_diffs += 1
                        elif diff.status == "REJECTED":
                            final_text = diff.original_text
                            source_status = "REJECTED_ORIGINAL"
                            rejected_diffs += 1
                        else:  # PENDING
                            final_text = diff.original_text
                            source_status = "PENDING_ORIGINAL"

                    composed_bullets.append(
                        {
                            "bullet_index": b_idx,
                            "text": final_text,
                            "original_text": diff.original_text if diff else orig_text,
                            "source_status": source_status,
                            "diff_id": diff_id,
                            "requirement_id": req_id,
                            "validation_status": nli_status,
                            "provenance": (
                                f"Action-aligned tailored bullet targeting requirement {req_id}"
                                if diff and diff.status == "ACCEPTED"
                                else "Verified authentic candidate resume bullet"
                            ),
                        }
                    )

                    provenance_records.append(
                        {
                            "section_id": sec_id,
                            "section_name": heading,
                            "item_id": item_id,
                            "item_title": title,
                            "bullet_index": b_idx,
                            "original_text": diff.original_text if diff else orig_text,
                            "composed_text": final_text,
                            "source_status": source_status,
                            "diff_id": diff_id,
                            "requirement_id": req_id,
                            "validation_status": nli_status,
                        }
                    )

                desc = item.get("description") or item.get("text") or ""
                item_reason = (
                    f"Verified {title or 'career experience'} demonstrating applied competencies."
                    if composed_bullets
                    else "Original candidate career record preserved without data loss."
                )

                composed_items.append(
                    {
                        "id": item_id,
                        "title": title,
                        "organization": org,
                        "location": loc,
                        "start_date": start_date,
                        "end_date": end_date,
                        "is_current": is_current,
                        "description": desc,
                        "bullets": composed_bullets,
                        "rendered_bullets": [b["text"] for b in composed_bullets],
                        "selection_reason": item_reason,
                    }
                )

            composed_sections.append(
                {
                    "id": sec_id,
                    "section_type": sec_type,
                    "heading": heading,
                    "is_included": is_included,
                    "display_order": display_order,
                    "selection_reason": section_reason,
                    "items": composed_items,
                    "raw_content": sec.get("raw_content"),
                }
            )

        # Sort sections by display_order
        composed_sections.sort(key=lambda s: s.get("display_order", 0))

        composition_metadata = {
            "target_role": tailored.target_jd.job_title if tailored.target_jd else "Target Role",
            "company_name": tailored.target_jd.company_name if tailored.target_jd else None,
            "version_title": tailored.version_title,
            "total_sections": len(composed_sections),
            "included_sections_count": sum(1 for s in composed_sections if s["is_included"]),
            "total_diffs": total_diffs,
            "applied_diffs": applied_diffs,
            "edited_diffs": edited_diffs,
            "rejected_diffs": rejected_diffs,
            "generated_at": datetime.datetime.utcnow().isoformat(),
        }

        # Build clean snapshot formatted for PDF/DOCX exporters and backward compatibility
        export_sections = []
        for sec in composed_sections:
            if not sec.get("is_included", True):
                continue
            export_sec = {
                "id": sec["id"],
                "section_type": sec["section_type"],
                "heading": sec["heading"],
                "display_order": sec["display_order"],
                "raw_content": sec["raw_content"],
                "selection_reason": sec.get("selection_reason", ""),
                "items": [
                    {
                        "id": itm["id"],
                        "title": itm["title"],
                        "organization": itm["organization"],
                        "location": itm["location"],
                        "start_date": itm["start_date"],
                        "end_date": itm["end_date"],
                        "is_current": itm["is_current"],
                        "description": itm.get("description", ""),
                        "bullets": itm["rendered_bullets"],
                        "selection_reason": itm.get("selection_reason", ""),
                    }
                    for itm in sec["items"]
                ],
            }
            export_sections.append(export_sec)

        return {
            "candidate_identity": candidate_identity,
            "sections": composed_sections,
            "export_sections": export_sections,
            "provenance": provenance_records,
            "metadata": composition_metadata,
        }

    def sync_tailored_content_snapshot(
        self,
        tailored: TailoredResume,
        diffs: list[TailoredBulletDiff],
    ) -> dict[str, Any]:
        """Produce an updated tailored_content dict synced with latest diff choices and section statuses."""
        ir = self.build_composition_ir(tailored, diffs)
        identity = ir["candidate_identity"]
        return {
            "full_name": identity["full_name"],
            "candidate_name": identity["candidate_name"],
            "contact_info": identity["contact_info"],
            "sections": ir["export_sections"],
            "raw_sections": ir["sections"],
            "metadata": ir["metadata"],
        }


# Global resume composer instance
resume_composer = ResumeComposer()
