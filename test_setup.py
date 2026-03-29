import os
from dotenv import load_dotenv

load_dotenv()

# Test 1: API key loaded
api_key = os.getenv("GOOGLE_API_KEY")
print(f"API key loaded: {'Yes' if api_key and api_key != 'your_key_here' else 'No - check your .env file'}")

# Test 2: Embedding model
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
embedding = model.encode("FE simulation parameters")
print(f"Embedding model works: vector of {len(embedding)} dimensions")

# Test 3: ChromaDB
import chromadb
client = chromadb.Client()
print(f"ChromaDB works: {client.heartbeat()}")

# Test 4: PDF reader
import fitz
print(f"PyMuPDF works: version {fitz.version}")

print("\nAll systems go! Phase 0 complete.")
