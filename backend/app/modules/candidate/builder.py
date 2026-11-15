from app.models.resume import Resume
from app.modules.ontology.normalizer import skill_normalizer


class CandidateProfileBuilder:
    """Extracts factual competencies anchored to verbatim resume evidence."""

    def extract_competencies(self, resume: Resume) -> list[dict]:
        """Extract all skills from a resume with evidence anchoring."""
        extracted: dict[str, dict] = {}

        for section in resume.sections:
            section_type = (section.section_type or "").lower()
            heading = section.heading or "Section"

            # 1. Process items (work experience, projects, education)
            for item in section.items:
                item_id_str = str(item.id)
                prefix = f"[{item.title}] " if item.title else ""

                # Check bullets
                for bullet in item.bullets or []:
                    bullet_text = bullet if isinstance(bullet, str) else str(bullet)
                    clean_text = bullet_text.strip()
                    if not clean_text:
                        continue

                    skills = skill_normalizer.extract_skills_from_text(clean_text)
                    for s in skills:
                        canonical = s["canonical_name"]
                        evidence = f"{prefix}{clean_text}"

                        # Work experience and projects provide stronger evidence than simple skill listings
                        is_experience = (
                            "experience" in section_type
                            or "work" in section_type
                            or "project" in section_type
                        )

                        if canonical not in extracted or (
                            is_experience and not extracted[canonical]["is_experience"]
                        ):
                            extracted[canonical] = {
                                "skill_name": s["skill_name"],
                                "normalized_name": canonical,
                                "category": s["category"],
                                "proficiency_level": "advanced" if is_experience else "proficient",
                                "evidence_text": evidence,
                                "evidence_item_id": item_id_str,
                                "is_experience": is_experience,
                            }

            # 2. Also process raw_content (especially for Skills sections or non-itemized sections)
            if section.raw_content:
                lines = [line.strip() for line in section.raw_content.splitlines() if line.strip()]
                for line in lines:
                    skills = skill_normalizer.extract_skills_from_text(line)
                    for s in skills:
                        canonical = s["canonical_name"]
                        if canonical not in extracted:
                            extracted[canonical] = {
                                "skill_name": s["skill_name"],
                                "normalized_name": canonical,
                                "category": s["category"],
                                "proficiency_level": "proficient",
                                "evidence_text": f"[{heading}] {line}",
                                "evidence_item_id": str(section.id),
                                "is_experience": False,
                            }

        # Remove temporary helper flags
        results = []
        for item in extracted.values():
            item_copy = dict(item)
            item_copy.pop("is_experience", None)
            results.append(item_copy)

        return results


candidate_profile_builder = CandidateProfileBuilder()
