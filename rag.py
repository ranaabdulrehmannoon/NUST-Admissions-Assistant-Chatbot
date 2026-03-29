import json
import os
from dataclasses import dataclass
from typing import Dict, List

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from utils.config import (
    CHUNKS_PATH,
    DEFAULT_OLLAMA_MODEL,
    EMBEDDING_MODEL_NAME,
    FAISS_INDEX_PATH,
    MIN_SIMILARITY,
    TOP_K,
)
from utils.model_client import OllamaClient


@dataclass
class RetrievalResult:
    text: str
    similarity: float
    source: str


class NUSTAdmissionsRAG:
    """FAISS-backed retrieval + Ollama generation pipeline."""

    def __init__(self, ollama_model: str | None = None) -> None:
        if not FAISS_INDEX_PATH.exists() or not CHUNKS_PATH.exists():
            raise FileNotFoundError(
                "Missing FAISS index or chunk metadata. Run setup.sh (or python ingest.py) first."
            )

        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        self.chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
        self.encoder = SentenceTransformer(EMBEDDING_MODEL_NAME)

        model_name = ollama_model or os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self.llm = OllamaClient(model=model_name)

    @staticmethod
    def _normalize_similarity(raw_score: float) -> float:
        # Index uses cosine similarity with normalized vectors and inner product.
        norm = (raw_score + 1.0) / 2.0
        return float(max(0.0, min(1.0, norm)))

    def retrieve(self, query: str, top_k: int = TOP_K) -> List[RetrievalResult]:
        query_embedding = self.encoder.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).astype("float32")

        similarities, indices = self.index.search(query_embedding, top_k)

        results: List[RetrievalResult] = []
        for score, idx in zip(similarities[0], indices[0]):
            if idx < 0:
                continue
            chunk = self.chunks[idx]
            results.append(
                RetrievalResult(
                    text=chunk["text"],
                    similarity=float(score),
                    source=chunk.get("source", "FAQ"),
                )
            )
        return results

    def _build_prompt(self, query: str, contexts: List[RetrievalResult]) -> str:
        context_block = "\n\n".join(
            [f"Context {i + 1}: {item.text}" for i, item in enumerate(contexts)]
        )

        return (
            "You are NUST Admissions Assistant.\n"
            "Rules:\n"
            "1) Answer using ONLY the provided context.\n"
            "2) Keep the answer short and factual.\n"
            "3) If the answer is not explicitly in context, respond exactly with: "
            "I don’t have reliable information on that.\n\n"
            f"User Question: {query}\n\n"
            f"Retrieved Context:\n{context_block}\n\n"
            "Answer:"
        )

    def answer(self, query: str) -> Dict[str, object]:
        retrieved = self.retrieve(query, top_k=TOP_K)
        if not retrieved:
            return {
                "answer": "I don’t have reliable information on that.",
                "confidence": 0.0,
                "source": "FAQ",
                "contexts": [],
            }

        max_similarity = max(item.similarity for item in retrieved)
        avg_similarity = float(np.mean([item.similarity for item in retrieved]))

        # Strict grounding guardrail.
        if max_similarity < MIN_SIMILARITY:
            return {
                "answer": "I don’t have reliable information on that.",
                "confidence": self._normalize_similarity(avg_similarity),
                "source": "FAQ",
                "contexts": [item.text for item in retrieved],
            }

        prompt = self._build_prompt(query=query, contexts=retrieved)
        response = self.llm.generate(prompt, temperature=0.1, num_predict=220).strip()

        if not response:
            response = "I don’t have reliable information on that."

        confidence = self._normalize_similarity((max_similarity + avg_similarity) / 2.0)

        return {
            "answer": response,
            "confidence": confidence,
            "source": "FAQ",
            "contexts": [item.text for item in retrieved],
        }
