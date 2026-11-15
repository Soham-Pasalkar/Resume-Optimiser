import re

from app.modules.ontology.seed_data import CANONICAL_SKILLS


class SkillNormalizer:
    """Normalizes skill aliases to canonical ontology concepts and scans text for competencies."""

    def __init__(self):
        self.alias_to_canonical: dict[str, tuple[str, str]] = {}
        self._compiled_patterns: list[tuple[re.Pattern, str, str]] = []
        self._init_lookup()

    def _init_lookup(self):
        for entry in CANONICAL_SKILLS:
            canonical = entry["canonical_name"]
            category = entry["category"]
            self.alias_to_canonical[canonical.lower()] = (canonical, category)

            # Register all aliases
            for alias in entry.get("aliases", []):
                alias_lower = alias.lower()
                self.alias_to_canonical[alias_lower] = (canonical, category)

                # Build regex with strict word boundary
                escaped = re.escape(alias_lower)
                # Ensure special characters like C++ / C# / .NET are correctly bounded
                pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
                self._compiled_patterns.append((pattern, canonical, category))

        # Sort patterns by length descending so longer phrases match first (e.g. "Google Cloud Platform" before "Go")
        self._compiled_patterns.sort(key=lambda x: len(x[1]), reverse=True)

    def normalize(self, skill_name: str) -> tuple[str, str]:
        """Map raw skill string to (canonical_name, category).
        If not found, returns (cleaned_skill_name, 'Other').
        """
        cleaned = skill_name.strip()
        cleaned_lower = cleaned.lower()

        if cleaned_lower in self.alias_to_canonical:
            return self.alias_to_canonical[cleaned_lower]

        # Try prefix/suffix matching
        for pattern, canonical, category in self._compiled_patterns:
            if pattern.search(cleaned_lower):
                return canonical, category

        return cleaned, "Other"

    def extract_skills_from_text(self, text: str) -> list[dict[str, str]]:
        """Extract all known canonical skills present in the text with exact match spans."""
        found: dict[str, dict[str, str]] = {}

        for pattern, canonical, category in self._compiled_patterns:
            match = pattern.search(text)
            if match and canonical not in found:
                found[canonical] = {
                    "skill_name": match.group(0),
                    "canonical_name": canonical,
                    "category": category,
                }

        return list(found.values())


# Global singleton instance
skill_normalizer = SkillNormalizer()
