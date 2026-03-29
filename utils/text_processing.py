import re
from typing import Iterable, List


_WHITESPACE_RE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Normalize whitespace and trim noisy separators."""
    if not text:
        return ""
    cleaned = text.replace("\xa0", " ").replace("\u200b", " ")
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def unique_preserve_order(items: Iterable[str]) -> List[str]:
    """Deduplicate text chunks while preserving original ordering."""
    seen = set()
    result: List[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def chunk_text(text: str, chunk_size_words: int = 120, overlap_words: int = 25) -> List[str]:
    """Split long text into overlapping word chunks for retrieval."""
    tokens = text.split()
    if not tokens:
        return []

    chunks: List[str] = []
    start = 0
    n_tokens = len(tokens)

    while start < n_tokens:
        end = min(start + chunk_size_words, n_tokens)
        chunk = " ".join(tokens[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= n_tokens:
            break
        start = max(0, end - overlap_words)

    return chunks
