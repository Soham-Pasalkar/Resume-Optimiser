import hashlib
import math

from app.core.llm import ollama_client


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    sim = dot / (norm_a * norm_b)
    return max(0.0, min(1.0, float(sim)))


class DenseMatcher:
    """Performs dense semantic vector similarity matching with zero-cost fallback."""

    def __init__(self, fallback_dim: int = 256):
        self.fallback_dim = fallback_dim

    async def get_embedding(self, text: str) -> list[float]:
        """Fetch dense embedding from local Ollama or compute deterministic semantic representation."""
        clean = text.strip()
        if not clean:
            return [0.0] * self.fallback_dim

        # 1. Try local Ollama embedding
        try:
            emb = await ollama_client.get_embedding(clean)
            if emb and len(emb) > 0:
                return emb
        except Exception:
            pass

        # 2. Deterministic hashing fallback (preserves semantic n-gram overlap)
        return self._generate_hashed_embedding(clean)

    def _generate_hashed_embedding(self, text: str) -> list[float]:
        """Generates a normalized n-gram hashed bag-of-words vector."""
        vec = [0.0] * self.fallback_dim
        words = text.lower().split()
        if not words:
            return vec

        # Subword 3-grams and tokens
        tokens = list(words)
        for w in words:
            if len(w) >= 3:
                for i in range(len(w) - 2):
                    tokens.append(w[i : i + 3])

        for token in tokens:
            h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.fallback_dim
            vec[idx] += 1.0

        # L2 Normalize
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]

        return vec

    async def compute_similarity(self, text_a: str, text_b: str) -> float:
        """Compute semantic cosine similarity between two texts."""
        emb_a = await self.get_embedding(text_a)
        emb_b = await self.get_embedding(text_b)
        return cosine_similarity(emb_a, emb_b)

    async def find_best_evidence_match(
        self,
        requirement_text: str,
        candidate_snippets: list[str],
    ) -> tuple[float, str | None]:
        """Find the candidate resume snippet with the highest semantic similarity to a requirement."""
        if not candidate_snippets:
            return 0.0, None

        req_emb = await self.get_embedding(requirement_text)
        best_sim = 0.0
        best_snippet = None

        for snippet in candidate_snippets:
            snippet_emb = await self.get_embedding(snippet)
            sim = cosine_similarity(req_emb, snippet_emb)
            if sim > best_sim:
                best_sim = sim
                best_snippet = snippet

        # Cutoff to prevent attaching unrelated snippets as evidence
        if best_sim < 0.40:
            return round(best_sim, 3), None

        return round(best_sim, 3), best_snippet


# Global dense matcher instance
dense_matcher = DenseMatcher()
