"""
Phase 2: Embedding & Vector Store
Loads chunks from Phase 1, embeds them using a local model,
and stores them in ChromaDB for semantic search.
"""

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer


# ============================================================
# STEP 1: LOAD CHUNKS
# ============================================================

def load_chunks(chunks_path):
    """
    Load the processed chunks from Phase 1.
    
    Why: ingest.py saved all chunks (manual + simulation) into a single
    JSON file in data/processed. It is now loaded here to embed and store in the vector database.
    """
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"Loaded {len(chunks)} chunks from {chunks_path}")
    return chunks


# ============================================================
# STEP 2: INITIALIZE EMBEDDING MODEL
# ============================================================

def load_embedding_model(model_name="all-MiniLM-L6-v2"):
    """
    Loading a pre-trained sentence embedding model.
    
    Why this model: all-MiniLM-L6-v2 is small (~80MB), fast, and produces
    384-dimensional vectors. It runs comfortably on CPU. For a first pass,
    it's the standard starting point. If retrieval quality isn't good enough
    in later can swap to a larger or domain-specific model.
    
    What it does: converts any text string into a vector of 384 numbers.
    Texts with similar meaning produce vectors that are close together
    in that 384-dimensional space.
    """
    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    print(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")
    return model


# ============================================================
# STEP 3: CREATE VECTOR STORE
# ============================================================

def create_vector_store(chunks, model, db_path="data/vector_store"):
    """
    Embed all chunks and store them in ChromaDB.
    
    Why ChromaDB: It's a lightweight vector database that runs locally
    (no server needed), stores embeddings on disk, and supports
    metadata filtering. Perfect for development and small-to-medium
    projects.
    
    How it works:
    1. Creates a ChromaDB "collection" (like a table in a database)
    2. For each chunk, we embed the text using our model
    3. We store the embedding, the original text, and metadata
       (source, page, type) together
    4. Later, question is embedded, and ChromaDB finds the chunks
       whose embeddings are most similar
    """
    # Create persistent ChromaDB client (saves to disk)
    client = chromadb.PersistentClient(path=db_path)
    
    # Delete existing collection if it exists (fresh start)
    try:
        client.delete_collection("fe_rag_chunks")
        print("Deleted existing collection.")
    except Exception:
        pass
    
    # Create new collection
    collection = client.create_collection(
        name="fe_rag_chunks",
        metadata={"description": "FE software manual and project database chunks"}
    )
    
    # Prepare data for ChromaDB
    # ChromaDB expects: ids, documents, embeddings, metadatas ######
    print(f"\nEmbedding {len(chunks)} chunks...")
    
    # Process in batches to show progress and manage memory
    batch_size = 100
    total_batches = (len(chunks) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(chunks))
        batch = chunks[start_idx:end_idx]
        
        # Prepare batch data
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(batch):
            chunk_id = f"chunk-{start_idx + i:05d}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            
            # Build metadata (ChromaDB only accepts str, int, float, bool)
            metadata = {
                "source": chunk.get("source", "unknown"),
                "type": chunk.get("type", "unknown"),
            }
            
            # Add type-specific metadata
            if chunk["type"] == "manual":
                metadata["page"] = chunk.get("page", 0)
            elif chunk["type"] == "simulation":
                metadata["sim_id"] = chunk.get("sim_id", "")
                metadata["project"] = chunk.get("project", "")
                metadata["load_case"] = chunk.get("load_case", "")
            
            metadatas.append(metadata)
        
        # Embed the batch
        texts = [chunk["text"] for chunk in batch]
        embeddings = model.encode(texts, show_progress_bar=False).tolist()
        
        # Add to ChromaDB - Only the chunks are embedded, and added to the collection 
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        # Progress update
        progress = min(end_idx, len(chunks))
        print(f"  Batch {batch_num + 1}/{total_batches}: embedded and stored {progress}/{len(chunks)} chunks")
    
    print(f"\nVector store created at: {db_path}")
    print(f"Collection '{collection.name}' contains {collection.count()} entries")
    return collection


# ============================================================
# STEP 4: TEST RETRIEVAL
# ============================================================

def test_retrieval(collection, model, query, n_results=5):
    """
    Test the vector store by running a sample query.
    
    How retrieval works:
    1. Embed the query text using the same model
    2. ChromaDB compares the query embedding to all stored embeddings
    3. Returns the n closest matches (most semantically similar chunks)
    
    Core principal of RAG — finding relevant context for a question.
    """
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    # Embed the query
    query_embedding = model.encode([query]).tolist()
    
    # Search ChromaDB
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    # Display results
    for i in range(len(results["ids"][0])):
        doc_id = results["ids"][0][i]
        distance = results["distances"][0][i]
        metadata = results["metadatas"][0][i]
        text = results["documents"][0][i]
        
        print(f"\n--- Result {i+1} (distance: {distance:.4f}) ---")
        print(f"Type: {metadata.get('type', 'unknown')}", end="")
        if metadata.get("type") == "manual":
            print(f" | Page: {metadata.get('page', '?')}")
        elif metadata.get("type") == "simulation":
            print(f" | Project: {metadata.get('project', '?')} | Load Case: {metadata.get('load_case', '?')}")
        else:
            print()
        print(f"Text: {text[:200]}...")
    
    return results


# ============================================================
# MAIN
# ============================================================

def main():
    # Paths
    chunks_path = "data/processed/chunks.json"
    db_path = "data/vector_store"
    
    # Step 1: Load chunks
    chunks = load_chunks(chunks_path)
    
    # Step 2: Load embedding model
    model = load_embedding_model()
    
    # Step 3: Create vector store
    collection = create_vector_store(chunks, model, db_path)
    
    # Step 4: Test with sample queries
    test_queries = [
        "What is MAT_024 piecewise linear plasticity?",
        "What element formulation should I use for shell elements in crash?",
        "Which projects used hot stamped steel for the B-pillar?",
    ]
    
    for query in test_queries:
        test_retrieval(collection, model, query)



if __name__ == "__main__":
    main()
