import math
import re
from collections import Counter

# Standard English stop words
STOP_WORDS: set[str] = {
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "am",
    "an",
    "and",
    "any",
    "are",
    "aren't",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can't",
    "cannot",
    "could",
    "couldn't",
    "did",
    "didn't",
    "do",
    "does",
    "doesn't",
    "doing",
    "don't",
    "down",
    "during",
    "each",
    "few",
    "for",
    "from",
    "further",
    "had",
    "hadn't",
    "has",
    "hasn't",
    "have",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "her",
    "here",
    "here's",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "how's",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "if",
    "in",
    "into",
    "is",
    "isn't",
    "it",
    "it's",
    "its",
    "itself",
    "let's",
    "me",
    "more",
    "most",
    "mustn't",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "same",
    "shan't",
    "she",
    "she'd",
    "she'll",
    "she's",
    "should",
    "shouldn't",
    "so",
    "some",
    "such",
    "than",
    "that",
    "that's",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "there's",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "wasn't",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "were",
    "weren't",
    "what",
    "what's",
    "when",
    "when's",
    "where",
    "where's",
    "which",
    "while",
    "who",
    "who's",
    "whom",
    "why",
    "why's",
    "with",
    "won't",
    "would",
    "wouldn't",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


def tokenize(text: str) -> list[str]:
    """Tokenize text into lowercase alphanumeric tokens without stop words."""
    clean = re.sub(r"[^\w\s+#.-]", " ", text.lower())
    tokens = clean.split()
    return [t for t in tokens if len(t) > 1 and t not in STOP_WORDS]


class BM25Index:
    """Okapi BM25 indexer with parameters k1=1.5 and b=0.75."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = 0
        self.avgdl = 0.0
        self.doc_lengths: list[int] = []
        self.doc_freqs: list[Counter] = []
        self.df: Counter = Counter()

    def fit(self, documents: list[str]):
        """Build BM25 index over candidate document chunks."""
        self.corpus_size = len(documents)
        if self.corpus_size == 0:
            return

        total_length = 0
        self.doc_lengths = []
        self.doc_freqs = []
        self.df = Counter()

        for doc in documents:
            tokens = tokenize(doc)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_length += length

            freqs = Counter(tokens)
            self.doc_freqs.append(freqs)

            for token in freqs.keys():
                self.df[token] += 1

        self.avgdl = total_length / self.corpus_size if self.corpus_size > 0 else 0.0

    def score_query_against_doc(self, query_tokens: list[str], doc_idx: int) -> float:
        """Compute BM25 score of a query against a specific document index."""
        if self.corpus_size == 0 or doc_idx >= len(self.doc_freqs):
            return 0.0

        score = 0.0
        doc_len = self.doc_lengths[doc_idx]
        freqs = self.doc_freqs[doc_idx]
        effective_n = max(self.corpus_size, 5)

        for token in query_tokens:
            if token not in freqs:
                continue

            # Inverse Document Frequency (probabilistic BM25 IDF with smoothing for resume chunks)
            n_q = self.df.get(token, 0)
            idf = math.log(((effective_n - n_q + 0.5) / (n_q + 0.5)) + 1.0)
            if idf < 0:
                idf = 0.0

            tf = freqs[token]
            num = tf * (self.k1 + 1.0)
            den = tf + self.k1 * (
                1.0 - self.b + self.b * (doc_len / self.avgdl if self.avgdl > 0 else 1.0)
            )
            score += idf * (num / den)

        return score

    def score_query_across_corpus(self, query: str) -> float:
        """Return the maximum BM25 match score across the document collection."""
        tokens = tokenize(query)
        if not tokens or self.corpus_size == 0:
            return 0.0

        scores = [self.score_query_against_doc(tokens, i) for i in range(self.corpus_size)]
        return max(scores) if scores else 0.0

    def compute_overall_lexical_alignment(self, requirements: list[str]) -> float:
        """Compute overall normalized lexical score (0.0 to 100.0) across all requirements."""
        if not requirements or self.corpus_size == 0:
            return 0.0

        scores = []
        for req in requirements:
            raw_score = self.score_query_across_corpus(req)
            # Map raw BM25 score to 0.0 - 1.0 using saturation curve
            normalized = raw_score / (raw_score + 1.0) if raw_score > 0 else 0.0
            scores.append(normalized)

        avg_score = sum(scores) / len(scores) if scores else 0.0
        return round(avg_score * 100.0, 2)
