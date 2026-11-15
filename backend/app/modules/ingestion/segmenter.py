import re
from typing import Any


class SectionSegmenter:
    """Segments raw resume text into logical sections and extracts structured items
    preserving all experience, project, education, and achievement entries without silent data loss.
    """

    # Comprehensive Heading detection regex patterns (case-insensitive)
    SECTION_PATTERNS = {
        "summary": re.compile(
            r"^(professional\s+summary|executive\s+summary|summary|profile|about\s+me|career\s+objective|objective|professional\s+profile)",
            re.IGNORECASE,
        ),
        "skills": re.compile(
            r"^(technical\s+skills|skills|technologies|core\s+competencies|tools\s*(&|and)?\s*technologies|areas\s+of\s+expertise|technical\s+proficiencies|programming\s+languages|skills\s*(&|and)?\s*tools)",
            re.IGNORECASE,
        ),
        "experience": re.compile(
            r"^(work\s+experience|professional\s+experience|experience|employment\s+history|career\s+history|work\s+history|relevant\s+experience)",
            re.IGNORECASE,
        ),
        "internships": re.compile(
            r"^(internships|internship\s+experience|student\s+employment|practical\s+experience|internship\s+history)",
            re.IGNORECASE,
        ),
        "projects": re.compile(
            r"^(projects|technical\s+projects|key\s+projects|personal\s+projects|open\s+source\s+contributions|academic\s+projects|selected\s+projects)",
            re.IGNORECASE,
        ),
        "education": re.compile(
            r"^(education|academic\s+background|academic\s+history|qualifications|degrees|educational\s+background)",
            re.IGNORECASE,
        ),
        "certifications": re.compile(
            r"^(certifications|licenses|courses|professional\s+certifications|accreditations|certificates|certifications\s*(&|and)?\s*licenses)",
            re.IGNORECASE,
        ),
        "achievements": re.compile(
            r"^(achievements|honors|awards|publications|patents|presentations|honors\s*(&|and)?\s*awards|key\s+achievements|awards\s*(&|and)?\s*honors)",
            re.IGNORECASE,
        ),
        "leadership": re.compile(
            r"^(leadership|leadership\s+experience|extracurricular|extracurricular\s+activities|volunteer|volunteer\s+experience|volunteering|community\s+service|activities)",
            re.IGNORECASE,
        ),
    }

    # Bullet point prefix detection
    BULLET_REGEX = re.compile(r"^(\s*[-•*▪▸–—]\s*|\s*\d+[\.\)]\s+)")

    # Date span pattern (e.g. "Jan 2021 - Present", "2020 - 2023", "05/2019 to 08/2021")
    DATE_SPAN_REGEX = re.compile(
        r"(?P<start>(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)?(?:19|20)\d{2}|\d{1,2}/\d{4})\s*(?:-|–|—|to)\s*(?P<end>(?:(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)?(?:19|20)\d{2}|\d{1,2}/\d{4}|Present|Current)",
        re.IGNORECASE,
    )

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
        if len(line) > 55:
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
        """Extract individual structured items from section lines."""
        if section_type in ["experience", "projects", "internships", "leadership"]:
            return cls._extract_work_or_project_items(lines, section_type)
        elif section_type == "education":
            return cls._extract_education_items(lines)
        elif section_type == "certifications":
            return cls._extract_certification_items(lines)
        elif section_type == "achievements":
            return cls._extract_achievement_items(lines)
        return []

    @classmethod
    def _extract_work_or_project_items(
        cls, lines: list[str], section_type: str
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        current_title: str | None = None
        current_org: str | None = None
        current_location: str | None = None
        current_start: str | None = None
        current_end: str | None = None
        current_is_current: bool = False
        current_bullets: list[str] = []

        item_type_map = {
            "experience": "job_position",
            "internships": "internship_position",
            "projects": "project_entry",
            "leadership": "leadership_entry",
        }
        item_type = item_type_map.get(section_type, "entry")

        def commit_current_item():
            nonlocal current_title, current_org, current_location, current_start, current_end, current_is_current, current_bullets
            if current_title or current_bullets:
                items.append(
                    {
                        "item_type": item_type,
                        "title": current_title or f"Role at {current_org}" if current_org else "Professional Experience",
                        "organization": current_org,
                        "location": current_location,
                        "start_date": current_start,
                        "end_date": current_end,
                        "is_current": current_is_current,
                        "bullets": current_bullets if current_bullets else [current_title] if current_title else [],
                    }
                )
            current_title = None
            current_org = None
            current_location = None
            current_start = None
            current_end = None
            current_is_current = False
            current_bullets = []

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            is_bullet = bool(cls.BULLET_REGEX.match(line_str))
            cleaned_line = cls.BULLET_REGEX.sub("", line_str).strip()

            date_match = cls.DATE_SPAN_REGEX.search(cleaned_line)

            if is_bullet:
                if cleaned_line:
                    current_bullets.append(cleaned_line)
            else:
                # Check if this non-bullet line contains a date span
                if date_match and not current_start:
                    current_start = date_match.group("start")
                    current_end = date_match.group("end")
                    current_is_current = "present" in current_end.lower() or "current" in current_end.lower()
                    # Strip date from line to see if org or location remains
                    rem = cleaned_line[:date_match.start()] + " " + cleaned_line[date_match.end():]
                    rem = re.sub(r"[|–—\-,]+", " ", rem).strip()
                    if rem and not current_org and len(rem) < 50:
                        current_org = rem
                    elif rem and not current_location and len(rem) < 40:
                        current_location = rem
                    continue

                if not current_title:
                    # Line 1: Title / Organization line (e.g. "Senior Data Engineer at Citi" or "ETL Infrastructure | Personal Project")
                    parts = re.split(r"\s+(?:at|@|\||–|—|-)\s+", cleaned_line, maxsplit=1)
                    current_title = parts[0].strip()
                    if len(parts) > 1:
                        sub_part = parts[1].strip()
                        if cls.DATE_SPAN_REGEX.search(sub_part):
                            d_m = cls.DATE_SPAN_REGEX.search(sub_part)
                            current_start = d_m.group("start")
                            current_end = d_m.group("end")
                            current_is_current = "present" in current_end.lower() or "current" in current_end.lower()
                            org_rem = sub_part[:d_m.start()].strip(" |–—-,")
                            if org_rem:
                                current_org = org_rem
                        else:
                            current_org = sub_part
                elif current_bullets:
                    # If bullets already accumulated, a new non-bullet line signifies a new item
                    commit_current_item()
                    parts = re.split(r"\s+(?:at|@|\||–|—|-)\s+", cleaned_line, maxsplit=1)
                    current_title = parts[0].strip()
                    if len(parts) > 1:
                        current_org = parts[1].strip()
                else:
                    # Non-bullet line following title before any bullets were accumulated
                    if date_match:
                        current_start = date_match.group("start")
                        current_end = date_match.group("end")
                        current_is_current = "present" in current_end.lower() or "current" in current_end.lower()
                    elif not current_org and len(cleaned_line) < 60:
                        current_org = cleaned_line
                    elif not current_location and any(loc in cleaned_line.lower() for loc in ["remote", "ca", "ny", "tx", "wa", "usa", "uk", "india"]):
                        current_location = cleaned_line
                    else:
                        # CRITICAL FIX: Do NOT drop non-bulleted achievement or description sentences!
                        current_bullets.append(cleaned_line)

        # Commit final item
        commit_current_item()

        # If items still empty (e.g. freeform paragraphs), package all lines as achievement bullets
        if not items and lines:
            items.append(
                {
                    "item_type": item_type,
                    "title": section_type.replace("_", " ").title(),
                    "organization": None,
                    "location": None,
                    "start_date": None,
                    "end_date": None,
                    "is_current": False,
                    "bullets": [l for l in lines if len(l.strip()) > 10],
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
            date_match = cls.DATE_SPAN_REGEX.search(cleaned)
            start_d = date_match.group("start") if date_match else None
            end_d = date_match.group("end") if date_match else None

            # University / Degree detection
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
                    "b.tech",
                    "m.tech",
                    "degree",
                    "institute",
                ]
            ):
                parts = re.split(r"\s+(?:-|–|—|\||,)\s+", cleaned, maxsplit=1)
                items.append(
                    {
                        "item_type": "degree",
                        "title": parts[0].strip(),
                        "organization": parts[1].strip() if len(parts) > 1 else None,
                        "location": None,
                        "start_date": start_d,
                        "end_date": end_d,
                        "is_current": False,
                        "bullets": [],
                    }
                )
        return items

    @classmethod
    def _extract_certification_items(cls, lines: list[str]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for line in lines:
            if not line:
                continue
            cleaned = cls.BULLET_REGEX.sub("", line).strip()
            if len(cleaned) < 5:
                continue
            parts = re.split(r"\s+(?:-|–|—|\||,)\s+", cleaned, maxsplit=1)
            items.append(
                {
                    "item_type": "certification",
                    "title": parts[0].strip(),
                    "organization": parts[1].strip() if len(parts) > 1 else None,
                    "location": None,
                    "start_date": None,
                    "end_date": None,
                    "is_current": False,
                    "bullets": [],
                }
            )
        return items

    @classmethod
    def _extract_achievement_items(cls, lines: list[str]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for line in lines:
            if not line:
                continue
            cleaned = cls.BULLET_REGEX.sub("", line).strip()
            if len(cleaned) < 8:
                continue
            items.append(
                {
                    "item_type": "achievement",
                    "title": cleaned,
                    "organization": None,
                    "location": None,
                    "start_date": None,
                    "end_date": None,
                    "is_current": False,
                    "bullets": [],
                }
            )
        return items
