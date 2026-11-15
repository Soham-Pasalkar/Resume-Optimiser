import re
from typing import Any


class SectionSegmenter:
    """Segments raw resume text into logical sections and extracts structured items."""

    # Heading detection regex patterns (case-insensitive)
    SECTION_PATTERNS = {
        "summary": re.compile(
            r"^(professional\s+summary|executive\s+summary|summary|profile|about\s+me|career\s+objective|objective)",
            re.IGNORECASE,
        ),
        "experience": re.compile(
            r"^(work\s+experience|professional\s+experience|experience|employment\s+history|career\s+history|work\s+history)",
            re.IGNORECASE,
        ),
        "education": re.compile(
            r"^(education|academic\s+background|academic\s+history|qualifications|degrees)",
            re.IGNORECASE,
        ),
        "skills": re.compile(
            r"^(technical\s+skills|skills|technologies|core\s+competencies|tools\s*(&|and)?\s*technologies|areas\s+of\s+expertise)",
            re.IGNORECASE,
        ),
        "projects": re.compile(
            r"^(projects|technical\s+projects|key\s+projects|personal\s+projects|open\s+source\s+contributions)",
            re.IGNORECASE,
        ),
        "certifications": re.compile(
            r"^(certifications|licenses|courses|professional\s+certifications|accreditations)",
            re.IGNORECASE,
        ),
    }

    # Bullet point prefix detection
    BULLET_REGEX = re.compile(r"^(\s*[-•*▪▸–—]\s*|\s*\d+\.\s+)")

    @classmethod
    def segment_text(cls, raw_text: str) -> list[dict[str, Any]]:
        """Segments raw text into structured section blocks."""
        lines = [line.strip() for line in raw_text.split("\n")]
        sections: list[dict[str, Any]] = []

        current_heading = "Personal Information"
        current_type = "personal_info"
        current_content_lines: list[str] = []

        for line in lines:
            if not line:
                continue

            matched_type, matched_heading = cls._match_heading(line)
            if matched_type:
                # Save previous section if it has content
                if current_content_lines:
                    sections.append(
                        cls._build_section_dict(
                            current_type,
                            current_heading,
                            current_content_lines,
                            len(sections),
                        )
                    )
                current_heading = matched_heading
                current_type = matched_type
                current_content_lines = []
            else:
                current_content_lines.append(line)

        # Append final section
        if current_content_lines:
            sections.append(
                cls._build_section_dict(
                    current_type,
                    current_heading,
                    current_content_lines,
                    len(sections),
                )
            )

        return sections

    @classmethod
    def _match_heading(cls, line: str) -> tuple[str | None, str]:
        """Check if a line represents a known section header."""
        # Headings are generally short (< 50 chars), often uppercase or title-cased
        if len(line) > 50:
            return None, line

        # Strip common decorative characters (e.g. "--- EXPERIENCE ---", "## Skills")
        cleaned = re.sub(r"^[#=\-_\s*]+|[#=\-_\s*:]+$", "", line).strip()

        for sec_type, pattern in cls.SECTION_PATTERNS.items():
            if pattern.match(cleaned):
                return sec_type, cleaned

        return None, line

    @classmethod
    def _build_section_dict(
        cls,
        section_type: str,
        heading: str,
        lines: list[str],
        display_order: int,
    ) -> dict[str, Any]:
        raw_content = "\n".join(lines).strip()
        items = cls._extract_items_for_section(section_type, lines)

        return {
            "section_type": section_type,
            "heading": heading,
            "raw_content": raw_content,
            "display_order": display_order,
            "items": items,
        }

    @classmethod
    def _extract_items_for_section(
        cls, section_type: str, lines: list[str]
    ) -> list[dict[str, Any]]:
        """Extract individual structured items (e.g. jobs, projects, degrees) from section lines."""
        if section_type in ["experience", "projects"]:
            return cls._extract_work_or_project_items(lines, section_type)
        elif section_type == "education":
            return cls._extract_education_items(lines)
        return []

    @classmethod
    def _extract_work_or_project_items(
        cls, lines: list[str], section_type: str
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        current_title: str | None = None
        current_org: str | None = None
        current_bullets: list[str] = []

        for line in lines:
            is_bullet = bool(cls.BULLET_REGEX.match(line))
            cleaned_line = cls.BULLET_REGEX.sub("", line).strip()

            if is_bullet:
                if cleaned_line:
                    current_bullets.append(cleaned_line)
            else:
                # Likely a title/company line or date line
                if not current_title:
                    # Parse title / company line (e.g. "Senior Software Engineer at Stripe")
                    parts = re.split(r"\s+(?:at|@|\||-)\s+", cleaned_line, maxsplit=1)
                    current_title = parts[0].strip()
                    current_org = parts[1].strip() if len(parts) > 1 else None
                elif current_bullets:
                    # New position entry detected
                    items.append(
                        {
                            "item_type": "job_position"
                            if section_type == "experience"
                            else "project_entry",
                            "title": current_title,
                            "organization": current_org,
                            "bullets": current_bullets,
                        }
                    )
                    parts = re.split(r"\s+(?:at|@|\||-)\s+", cleaned_line, maxsplit=1)
                    current_title = parts[0].strip()
                    current_org = parts[1].strip() if len(parts) > 1 else None
                    current_bullets = []
                else:
                    # Secondary line before bullets (e.g. company or date)
                    if not current_org and len(cleaned_line) < 60:
                        current_org = cleaned_line

        # Commit final item
        if current_title:
            items.append(
                {
                    "item_type": "job_position"
                    if section_type == "experience"
                    else "project_entry",
                    "title": current_title,
                    "organization": current_org,
                    "bullets": current_bullets,
                }
            )

        return items

    @classmethod
    def _extract_education_items(cls, lines: list[str]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for line in lines:
            if not line:
                continue
            cleaned = cls.BULLET_REGEX.sub("", line).strip()
            # Simple university/degree heuristic
            if any(
                term in cleaned.lower()
                for term in [
                    "university",
                    "college",
                    "bachelor",
                    "master",
                    "phd",
                    "b.s.",
                    "m.s.",
                    "degree",
                ]
            ):
                parts = re.split(r"\s+(?:-|\||,)\s+", cleaned, maxsplit=1)
                items.append(
                    {
                        "item_type": "degree",
                        "title": parts[0].strip(),
                        "organization": parts[1].strip() if len(parts) > 1 else None,
                        "bullets": [],
                    }
                )
        return items
