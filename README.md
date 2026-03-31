# RAG-Based Chatbot for FE-Simulation Documentation

A Retrieval-Augmented Generation chatbot for querying LS-DYNA manuals and FE simulation project databases. Engineers can ask natural language questions about keyword cards, simulation parameters, and project configurations.

## Status
- Phase 0 - Environment Setup (done)
- Phase 1 - Document Ingestion & Chunking (done)
- Phase 2 - Embedding & Vector Store (next)

## Project Structure
```
fe-rag-chatbot/
├── data/
│   ├── raw/              ← Source PDFs and CSVs
│   └── processed/        ← Chunked data (chunks.json)
├── src/
│   ├── ingest.py         ← PDF extraction, chunking, noise filtering
│   ├── check_chunks.py   ← Chunk inspection utility
│   └── generate_synthetic_db.py ← Synthetic database generator
├── notebooks/            ← Jupyter notebooks for experimentation
├── .env                  ← API keys (excluded from Git)
├── .gitignore
├── requirements.txt
└── test_setup.py         ← Environment verification script
```

## Tech Stack
- Python 3.11 (Conda environment)
- PyMuPDF - PDF text extraction
- ChromaDB - Vector database
- sentence-transformers - Local embedding model
- Google Gemini API - LLM generation
- Streamlit - Chat UI (planned)