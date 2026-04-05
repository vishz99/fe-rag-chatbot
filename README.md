# RAG-Based Chatbot for FE-Simulation Documentation

A Retrieval-Augmented Generation chatbot for querying LS-DYNA manuals and FE simulation project databases. Engineers can ask natural language questions about keyword cards, simulation parameters, and project configurations.

## Status
- Phase 0 - Environment Setup (done)
- Phase 1 - Document Ingestion & Chunking (done)
- Phase 2 - Embedding & Vector Store (done)
- Phase 3 - Initial working RAG Pipeline (done)
- Phase 4 - Evaluating and iterating (in progress)

## Project Structure
```
fe-rag-chatbot/
├── data/
│   ├── raw/                          ← Source PDFs and CSVs
│   │   ├── .gitkeep                  ← (0) Preserves empty folder in Git
│   │   ├── ls-dyna_manual_vol1.pdf   ← (1.0) LS-DYNA R13 Keyword Manual
│   │   ├── simulations.csv           ← (1.1) Synthetic project database
│   │   ├── components.csv            ← (1.2) Component details per simulation
│   │   └── contacts.csv              ← (1.3) Contact definitions per simulation
│   ├── processed/
│   │   └── chunks.json               ← (2.0) Output of ingestion pipeline
│   └── vector_store/                 ← (3.0) ChromaDB embeddings (gitignored)
├── src/
│   ├── generate_synthetic_db.py      ← (1.0) Generates the 3 CSV files (Synthetic data)
│   ├── ingest.py                     ← (2.0) PDF extraction, chunking, noise filtering
│   ├── check_chunks.py               ← (2.1) Chunk inspection utility
│   ├── embed.py                      ← (3.0) Embedding pipeline + ChromaDB storage
│   ├── list_models.py                ← (3.1) Utility to list available Gemini models
│   ├── rag.py                        ← (4.0) Full RAG pipeline: retrieve + prompt + generate
│   ├── test_set.py                   ← (5.0) Evaluation test set (30 questions)
│   └── inspect_data.py               ← (5.1) Database inspection utility
├── docs/                             ← Phase documentation (gitignored for now)
├── notebooks/                        ← Jupyter notebooks for experimentation
├── .env                              ← API keys (gitignored)
├── .gitignore
├── requirements.txt                  ← pip freeze output for reproducibility
└── test_setup.py                     ← (0) Environment verification script
```

## Tech Stack
- Python 3.11 (Conda environment: fesoftwaredoc-rag)
- PyMuPDF — PDF text extraction
- sentence-transformers (all-MiniLM-L6-v2) — Local embedding model
- ChromaDB — Vector database
- Google Gemini 2.5 Flash — LLM generation (free tier)
- Streamlit — Chat UI (planned)

## Setup
1. Clone the repo
2. Create conda environment: `conda create -n fesoftwaredoc-rag python=3.11`
3. Activate: `conda activate fesoftwaredoc-rag`
4. Install dependencies: `pip install -r requirements.txt`
5. Add your API key to `.env`: `GOOGLE_API_KEY=your_key_here`
6. Place LS-DYNA manual PDF in `data/raw/`
7. Run pipeline: `python src/ingest.py` → `python src/embed.py` → `python src/rag.py`

[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/vishz99/fe-rag-chatbot)