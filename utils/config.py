from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
FAQ_TEXT_PATH = DATA_DIR / "faqs.txt"
CHUNKS_PATH = DATA_DIR / "chunks.json"
FAISS_INDEX_PATH = DATA_DIR / "faiss.index"

FAQ_URL = "https://nust.edu.pk/faqs"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_OLLAMA_MODEL = "phi3:mini"
TOP_K = 3
MIN_SIMILARITY = 0.35
