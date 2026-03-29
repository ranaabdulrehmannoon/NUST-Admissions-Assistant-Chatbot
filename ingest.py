import json
import logging
import re
from typing import List

import faiss
import numpy as np
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from utils.config import (
    CHUNKS_PATH,
    DATA_DIR,
    EMBEDDING_MODEL_NAME,
    FAQ_TEXT_PATH,
    FAQ_URL,
    FAISS_INDEX_PATH,
)
from utils.text_processing import chunk_text, clean_text, unique_preserve_order

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def fetch_faq_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def parse_faq_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text_parts: List[str] = []

    candidate_selectors = [
        "[class*='faq']",
        "[id*='faq']",
        "[class*='accordion']",
        "main",
        "article",
    ]

    candidate_nodes = []
    for selector in candidate_selectors:
        candidate_nodes.extend(soup.select(selector))

    if not candidate_nodes:
        candidate_nodes = [soup]

    for node in candidate_nodes:
        for element in node.find_all(["h1", "h2", "h3", "h4", "p", "li", "dt", "dd", "span", "div"]):
            text = clean_text(element.get_text(" ", strip=True))
            if not text:
                continue
            if len(text) < 20:
                continue
            if text.lower() in {"home", "menu", "search", "faq", "faqs"}:
                continue
            text_parts.append(text)

    text_parts = unique_preserve_order(text_parts)
    full_text = "\n".join(text_parts)

    # Remove excessive repeated punctuation and lines.
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    return full_text.strip()


def build_chunks(text: str) -> List[str]:
    paragraphs = [clean_text(p) for p in text.split("\n") if clean_text(p)]
    chunks: List[str] = []

    for para in paragraphs:
        if len(para.split()) <= 120:
            chunks.append(para)
        else:
            chunks.extend(chunk_text(para, chunk_size_words=120, overlap_words=25))

    chunks = [c for c in unique_preserve_order(chunks) if len(c.split()) >= 8]
    return chunks


def create_embeddings(chunks: List[str]) -> np.ndarray:
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    embeddings = model.encode(
        chunks,
        convert_to_numpy=True,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    return embeddings.astype("float32")


def save_faiss_index(embeddings: np.ndarray) -> faiss.Index:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    faiss.write_index(index, str(FAISS_INDEX_PATH))
    return index


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    logging.info("Fetching FAQ page: %s", FAQ_URL)
    html = fetch_faq_html(FAQ_URL)

    logging.info("Parsing FAQ content")
    text = parse_faq_text(html)
    if not text:
        raise RuntimeError("Failed to parse FAQ text from NUST website.")

    FAQ_TEXT_PATH.write_text(text, encoding="utf-8")
    logging.info("Saved cleaned FAQ text to %s", FAQ_TEXT_PATH)

    chunks = build_chunks(text)
    if not chunks:
        raise RuntimeError("No valid chunks produced from FAQ text.")

    logging.info("Created %d chunks", len(chunks))
    embeddings = create_embeddings(chunks)

    save_faiss_index(embeddings)
    logging.info("Saved FAISS index to %s", FAISS_INDEX_PATH)

    chunk_records = [
        {
            "id": idx,
            "text": chunk,
            "source": "FAQ",
        }
        for idx, chunk in enumerate(chunks)
    ]
    CHUNKS_PATH.write_text(json.dumps(chunk_records, indent=2, ensure_ascii=False), encoding="utf-8")
    logging.info("Saved chunk metadata to %s", CHUNKS_PATH)
    logging.info("Ingestion complete")


if __name__ == "__main__":
    main()
