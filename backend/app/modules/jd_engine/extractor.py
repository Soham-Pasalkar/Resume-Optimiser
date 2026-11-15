import json
import logging
import re

from app.core.llm import ollama_client
from app.modules.jd_engine.schemas import DecomposedJD, ExtractedRequirement
from app.modules.ontology.normalizer import skill_normalizer

logger = logging.getLogger(__name__)


class JDExtractor:
    """Extracts structured requirements, metadata, and skills from raw job descriptions."""

    JD_EXTRACTION_PROMPT = """You are an expert technical recruiter and talent intelligence specialist.
Analyze the following Job Description (JD) and extract structured information in JSON format.

JSON Schema to strictly follow:
{
  "job_title": "string (e.g. Senior Backend Engineer)",
  "company_name": "string or null",
  "department": "string or null",
  "seniority_level": "string or null (Entry, Mid-Level, Senior, Lead, Staff, Principal)",
  "work_mode": "string or null (Remote, Hybrid, On-site)",
  "location": "string or null",
  "salary_range": "string or null",
  "requirements": [
    {
      "requirement_text": "verbatim requirement string",
      "category": "technical_skill | soft_skill | qualification | responsibility | tool",
      "is_mandatory": true or false,
      "importance_weight": 1.0 for mandatory, 0.6 for preferred,
      "min_years_experience": number or null,
      "canonical_skill_name": "canonical skill if identifiable or null"
    }
  ]
}

Classify requirements accurately:
- 'is_mandatory' must be true for required, minimum, or must-have items.
- 'is_mandatory' must be false for preferred, nice-to-have, bonus, or plus items.
Return ONLY valid raw JSON without markdown code fences or conversational text.

Job Description text:
"""

    async def extract(self, raw_text: str) -> DecomposedJD:
        """Attempt local LLM extraction; gracefully fallback to deterministic rules."""
        cleaned_text = raw_text.strip()
        if not cleaned_text:
            return DecomposedJD(raw_text="")

        try:
            status = await ollama_client.get_status()
            if status.is_available:
                logger.info(
                    "Ollama is available. Extracting JD via local model: %s", status.active_model
                )
                prompt = self.JD_EXTRACTION_PROMPT + "\n" + cleaned_text[:6000]
                resp = await ollama_client.generate(
                    prompt=prompt,
                    system_prompt="You extract job descriptions into structured JSON. Always output valid JSON only.",
                    format_json=True,
                    temperature=0.1,
                )
                raw_json = resp.get("response", "").strip()
                # Clean possible markdown wrap
                if raw_json.startswith("```"):
                    raw_json = re.sub(r"^```(?:json)?", "", raw_json).strip()
                    raw_json = re.sub(r"```$", "", raw_json).strip()

                parsed = json.loads(raw_json)
                return self._post_process_llm_result(parsed, cleaned_text)
            else:
                logger.warning(
                    "Ollama unavailable (%s). Using deterministic JD extractor.", status.error
                )
        except Exception as exc:
            logger.warning(
                "Local LLM extraction failed (%s). Falling back to rule-based parser.", exc
            )

        return self._rule_based_extract(cleaned_text)

    def _post_process_llm_result(self, data: dict, raw_text: str) -> DecomposedJD:
        """Validate LLM JSON output and enrich with ontology normalizer."""
        requirements: list[ExtractedRequirement] = []

        for req in data.get("requirements", []):
            text = str(req.get("requirement_text", "")).strip()
            if not text:
                continue

            category = req.get("category", "technical_skill")
            is_mandatory = bool(req.get("is_mandatory", True))
            importance = float(req.get("importance_weight", 1.0 if is_mandatory else 0.6))

            # Experience years
            years = req.get("min_years_experience")
            if years is not None:
                try:
                    years = float(years)
                except (ValueError, TypeError):
                    years = None

            canonical_name = req.get("canonical_skill_name")
            if not canonical_name:
                # Run ontology extraction on text
                matched = skill_normalizer.extract_skills_from_text(text)
                if matched:
                    canonical_name = matched[0]["canonical_name"]

            requirements.append(
                ExtractedRequirement(
                    requirement_text=text,
                    category=category,
                    is_mandatory=is_mandatory,
                    importance_weight=importance,
                    min_years_experience=years,
                    canonical_skill_name=canonical_name,
                )
            )

        return DecomposedJD(
            job_title=data.get("job_title") or self._extract_title_fallback(raw_text),
            company_name=data.get("company_name"),
            department=data.get("department"),
            seniority_level=data.get("seniority_level") or self._extract_seniority(raw_text),
            work_mode=data.get("work_mode") or self._extract_work_mode(raw_text),
            location=data.get("location"),
            salary_range=data.get("salary_range") or self._extract_salary(raw_text),
            requirements=requirements,
            raw_text=raw_text,
        )

    def _rule_based_extract(self, raw_text: str) -> DecomposedJD:
        """Deterministic heuristic and ontology extraction for 100% offline accuracy."""
        title = self._extract_title_fallback(raw_text)
        seniority = self._extract_seniority(raw_text)
        work_mode = self._extract_work_mode(raw_text)
        salary = self._extract_salary(raw_text)

        requirements: list[ExtractedRequirement] = []
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        current_mandatory = True
        current_category = "qualification"

        # Regex headers
        mandatory_pattern = re.compile(
            r"^(?:(?:minimum|basic|required|mandatory|must\s+have)\s+(?:qualifications|requirements|skills|experience)|requirements:|qualifications:)",
            re.IGNORECASE,
        )
        preferred_pattern = re.compile(
            r"^(?:(?:preferred|desired|bonus|nice\s+to\s+have|plus)\s+(?:qualifications|requirements|skills|experience)|preferred:|bonus:)",
            re.IGNORECASE,
        )
        responsibilities_pattern = re.compile(
            r"^(?:(?:key\s+)?responsibilities|what\s+you(?:'ll|\swill)\s+do|duties|the\s+role):?",
            re.IGNORECASE,
        )

        for line in lines:
            # Check if this line is a section header
            if mandatory_pattern.search(line):
                current_mandatory = True
                current_category = "qualification"
                continue
            elif preferred_pattern.search(line):
                current_mandatory = False
                current_category = "qualification"
                continue
            elif responsibilities_pattern.search(line):
                current_mandatory = True
                current_category = "responsibility"
                continue

            # Process bullet or requirement line
            is_bullet = bool(re.match(r"^[-*•–—\d+\.]\s+", line))
            clean_item = re.sub(r"^[-*•–—\d+\.]\s+", "", line).strip()

            if is_bullet or len(clean_item) > 20:
                # Extract years of experience if mentioned
                years_match = re.search(
                    r"(\d+(?:\.\d+)?)\+?\s*(?:-\s*(\d+(?:\.\d+)?))?\s*years?",
                    clean_item,
                    re.IGNORECASE,
                )
                min_years = float(years_match.group(1)) if years_match else None

                # Extract ontology skills
                skills = skill_normalizer.extract_skills_from_text(clean_item)
                canonical_name = skills[0]["canonical_name"] if skills else None

                cat = current_category
                if skills:
                    cat = "technical_skill"
                elif any(
                    soft in clean_item.lower()
                    for soft in [
                        "communication",
                        "leadership",
                        "collaborat",
                        "team player",
                        "mentor",
                    ]
                ):
                    cat = "soft_skill"

                # Check for inline preferred indicators (e.g. "is a plus", "bonus", "preferred")
                inline_preferred = bool(
                    re.search(
                        r"\b(preferred|plus|bonus|nice\s+to\s+have|ideally|desired)\b",
                        clean_item,
                        re.IGNORECASE,
                    )
                )
                line_mandatory = False if inline_preferred else current_mandatory
                importance = 1.0 if line_mandatory else 0.6

                requirements.append(
                    ExtractedRequirement(
                        requirement_text=clean_item,
                        category=cat,
                        is_mandatory=line_mandatory,
                        importance_weight=importance,
                        min_years_experience=min_years,
                        canonical_skill_name=canonical_name,
                    )
                )

        # If no requirements were extracted from bullets, perform sentence-level requirement extraction
        if not requirements:
            # Split raw text into natural sentences
            raw_sentences = [
                s.strip()
                for s in re.split(r"(?<=[.!?])\s+|\n+", raw_text)
                if len(s.strip()) > 15
            ]

            requirement_signals = re.compile(
                r"\b(look(?:ing)?\s+for|require[ds]?|must\s+have|responsible\s+for|experience\s+with|proficien(?:t|cy)|background\s+in|degree\s+in|knowledge\s+of|ability\s+to|familiarity\s+with|demonstrated|hands-on|build|design|manage|lead|develop)\b",
                re.IGNORECASE,
            )

            preferred_signals = re.compile(
                r"\b(preferred|plus|bonus|nice\s+to\s+have|ideally|desired)\b",
                re.IGNORECASE,
            )

            seen_texts: set[str] = set()

            for sent in raw_sentences:
                clean_sent = sent.strip().lstrip("•-* ").strip()
                if clean_sent.lower() in seen_texts or len(clean_sent) < 20:
                    continue

                # Check if sentence signals a requirement or mentions known technical skills
                matched_skills = skill_normalizer.extract_skills_from_text(clean_sent)
                has_signal = bool(requirement_signals.search(clean_sent))

                if has_signal or matched_skills:
                    seen_texts.add(clean_sent.lower())

                    is_mand = not bool(preferred_signals.search(clean_sent))
                    years_m = re.search(
                        r"(\d+(?:\.\d+)?)\+?\s*(?:-\s*(\d+(?:\.\d+)?))?\s*years?",
                        clean_sent,
                        re.IGNORECASE,
                    )
                    min_yrs = float(years_m.group(1)) if years_m else None
                    canonical = matched_skills[0]["canonical_name"] if matched_skills else None

                    # Category classification
                    if matched_skills:
                        c_type = "technical_skill"
                    elif any(w in clean_sent.lower() for w in ["degree", "bachelor", "master", "phd", "education"]):
                        c_type = "qualification"
                    elif any(w in clean_sent.lower() for w in ["certif", "aws certified", "pmp", "license"]):
                        c_type = "qualification"
                    elif any(w in clean_sent.lower() for w in ["lead", "manage", "collaborat", "communicate", "mentor"]):
                        c_type = "soft_skill"
                    elif any(w in clean_sent.lower() for w in ["architect", "design", "build", "deliver", "scale"]):
                        c_type = "responsibility"
                    else:
                        c_type = "qualification"

                    requirements.append(
                        ExtractedRequirement(
                            requirement_text=clean_sent,
                            category=c_type,
                            is_mandatory=is_mand,
                            importance_weight=1.0 if is_mand else 0.6,
                            min_years_experience=min_yrs,
                            canonical_skill_name=canonical,
                        )
                    )

            if len(requirements) > 25:
                requirements = requirements[:25]

        # If still no requirements, fallback to extracted skill phrases
        if not requirements:
            all_skills = skill_normalizer.extract_skills_from_text(raw_text)
            for skill in all_skills:
                requirements.append(
                    ExtractedRequirement(
                        requirement_text=f"Hands-on experience with {skill['canonical_name']}",
                        category="technical_skill",
                        is_mandatory=True,
                        importance_weight=1.0,
                        canonical_skill_name=skill["canonical_name"],
                    )
                )

        return DecomposedJD(
            job_title=title,
            seniority_level=seniority,
            work_mode=work_mode,
            salary_range=salary,
            requirements=requirements,
            raw_text=raw_text,
        )

    def _extract_title_fallback(self, text: str) -> str:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines[:5]:
            match = re.match(r"^(?:job\s+title|role|position):\s*(.+)$", line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        # Fallback to first line if short enough
        if lines and len(lines[0]) < 80:
            return lines[0]
        return "Untitled Position"

    def _extract_seniority(self, text: str) -> str | None:
        match = re.search(
            r"\b(intern|junior|entry[\s-]level|mid[\s-]level|senior|lead|principal|staff|director|head\s+of|vp)\b",
            text,
            re.IGNORECASE,
        )
        if match:
            val = match.group(1).title()
            return "Entry-Level" if "Entry" in val else val
        return None

    def _extract_work_mode(self, text: str) -> str | None:
        if re.search(r"\b(remote|work\s+from\s+home|telecommute)\b", text, re.IGNORECASE):
            return "Remote"
        if re.search(r"\b(hybrid)\b", text, re.IGNORECASE):
            return "Hybrid"
        if re.search(r"\b(on-site|onsite|in-office)\b", text, re.IGNORECASE):
            return "On-site"
        return None

    def _extract_salary(self, text: str) -> str | None:
        match = re.search(
            r"(\$\s*[0-9]{2,3}(?:,[0-9]{3})*(?:\s*-\s*\$?\s*[0-9]{2,3}(?:,[0-9]{3})*)?(?:\s*(?:k|usd|\/yr|\/year|per\s+year))?)",
            text,
            re.IGNORECASE,
        )
        return match.group(1).strip() if match else None


# Global extractor instance
jd_extractor = JDExtractor()
