# NUST Admissions Assistant (Offline Chatbot)

Production-ready, fully local chatbot for NUST admissions queries.

## Key Features

- 100% local inference after setup (no cloud APIs)
- Lightweight local LLM via Ollama (`phi3:mini` by default, can switch to `mistral`)
- FAQ scraping from official page: https://nust.edu.pk/faqs
- Retrieval-Augmented Generation (RAG) using FAISS + all-MiniLM-L6-v2 embeddings
- Hallucination control: answers only from retrieved context
- Modern dark Streamlit chat UI with confidence score and source display

## Project Structure

- `app.py` - Streamlit web UI
- `ingest.py` - FAQ scraping, cleaning, chunking, embedding, FAISS indexing
- `rag.py` - Retrieval and grounded response generation pipeline
- `utils/config.py` - paths and runtime settings
- `utils/text_processing.py` - cleaning/chunking utilities
- `utils/model_client.py` - local Ollama client with API + CLI fallback
- `data/` - local corpus text and vector index files
- `requirements.txt` - Python dependencies
- `setup.sh` - one-command environment setup + indexing
- `run.sh` - one-command app launch

## One-Command Setup

From this folder:

bash setup.sh

Windows PowerShell (no Bash required):

.\setup.ps1

Or double-click / terminal shortcut:

setup.cmd

This does all of the following automatically:

1. Creates Python virtual environment
2. Installs dependencies
3. Installs Ollama (if missing)
4. Starts Ollama service (if needed)
5. Pulls local model (`phi3:mini` by default)
6. Downloads and indexes NUST FAQ content into FAISS

## Run

bash run.sh

Windows PowerShell:

.\run.ps1

Or:

run.cmd

Then open: http://localhost:8501

## Optional Model Switch

Use Mistral instead of Phi-3 mini:

OLLAMA_MODEL=mistral bash setup.sh

## How It Works

1. Ingestion:
   - Scrape official FAQ page
   - Clean text and remove boilerplate noise
   - Chunk content for retrieval
   - Create embeddings using `all-MiniLM-L6-v2`
   - Store vectors in FAISS and chunk metadata in `data/chunks.json`

2. Query-time RAG:
   - Encode user question
   - Retrieve top 3 relevant chunks from FAISS
   - If retrieval confidence is low, return fallback:
      - `I don’t have reliable information on that.`
   - Otherwise, send only retrieved context to local Ollama model
   - Display concise answer with source and confidence

## Architecture Diagram (Text)

User Question
  -> Streamlit UI (`app.py`)
  -> RAG Engine (`rag.py`)
  -> Query Embedding (MiniLM)
  -> FAISS Top-3 Retrieval (`data/faiss.index` + `data/chunks.json`)
  -> Grounding Check (similarity threshold)
      -> Low confidence: safe fallback response
      -> High confidence: local LLM prompt with retrieved context only
  -> Ollama Local Model (`phi3:mini` or `mistral`)
  -> Final Answer + Source + Confidence in UI

## Notes for Low-End Machines (8GB RAM, CPU)

- Default model is `phi3:mini` for lower memory usage
- Keep browser tabs minimal while running local model
- You can reduce answer generation length in `rag.py` (`num_predict`) for faster responses

## Troubleshooting

- If setup fails while scraping FAQs, verify internet is available during setup and rerun `bash setup.sh`
- If app cannot generate responses, ensure Ollama is running and model is present:
  - `ollama list`
  - `ollama serve`
