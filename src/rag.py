"""
Phase 3: Basic RAG Pipeline
Connect retrieval (ChromaDB) with generation (Gemini API)
to answer engineering questions grounded in source documents.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from google import genai


# ============================================================
# STEP 1: LOAD COMPONENTS
# ============================================================

def load_components():
    """
    Load all components needed for RAG:
    - Environment variables (API key)
    - Embedding model (for query embedding)
    - Vector store (for retrieval)
    - LLM client (for answer generation)
    """
    # Load API key
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file")
    
    # Configure Gemini client
    client = genai.Client(api_key=api_key)
    print("Gemini API configured.")
    
    # Load embedding model
    print("Loading embedding model...")
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    print("Embedding model loaded.")
    
    # Load vector store
    db_client = chromadb.PersistentClient(path="data/vector_store")
    collection = db_client.get_collection("fe_rag_chunks")
    print(f"Vector store loaded: {collection.count()} chunks available.")
    
    return client, embed_model, collection


# ============================================================
# STEP 2: RETRIEVE RELEVANT CHUNKS
# ============================================================

def retrieve(query, embed_model, collection, n_results=5):
    """
    Find the most relevant chunks for a given query.
    
    How it works:
    1. Embed the query using the same model that embedded the chunks
    2. ChromaDB compares the query vector to all stored vectors
    3. Returns the n closest matches with their text and metadata
    
    n_results=5: 5 chunks are retrived to give the LLM enough
    context without overwhelming it. Too few and the answer might
    miss important details. Too many and irrelevant content dilutes
    the good context. 5 is a starting point — tuned later.
    """
    query_embedding = embed_model.encode([query]).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results
    )
    
    # Package results into a cleaner format
    retrieved = []
    for i in range(len(results["ids"][0])):
        retrieved.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i]
        })
    
    return retrieved


# ============================================================
# STEP 3: BUILD PROMPT
# ============================================================

def build_prompt(query, retrieved_chunks):
    """
    Construct the prompt that will be sent to the LLM.
    
    Why this structure matters: The LLM has no knowledge of LS-DYNA
    or our project database. Everything it needs to answer must be
    in the prompt. We give it:
    1. A system instruction defining its role and rules
    2. The retrieved context chunks with source info
    3. The user's question
    
    The instruction tells the LLM to only answer from the provided
    context — this prevents hallucination (making up information
    that isn't in the documents).
    """
    # Build context string from retrieved chunks
    context_parts = []
    for i, chunk in enumerate(retrieved_chunks):
        meta = chunk["metadata"]
        source_info = ""
        if meta.get("type") == "manual":
            source_info = f"[Source: LS-DYNA Manual, Page {meta.get('page', '?')}]"
        elif meta.get("type") == "simulation":
            source_info = f"[Source: Project Database - {meta.get('project', '?')}, {meta.get('load_case', '?')}]"
        
        context_parts.append(f"--- Context {i+1} {source_info} ---\n{chunk['text']}")
    
    context = "\n\n".join(context_parts)
    
    prompt = f"""You are an expert LS-DYNA crash simulation engineer assistant. 
            Answer the user's question based ONLY on the context provided below. 
            If the context does not contain enough information to answer the question, 
            say so clearly — do not make up information.

            When referencing information, mention the source (manual page number or 
            project name) so the engineer can verify.

            Keep answers technical, precise, and practical.

            CONTEXT:
            {context}

            QUESTION: {query}

            ANSWER:"""
    
    return prompt


# ============================================================
# STEP 4: GENERATE ANSWER
# ============================================================

def generate_answer(prompt, client):
    """
    Send the prompt to Gemini and get the answer.
    What happens here: The prompt (containing the system instruction,
    retrieved context, and question) is sent to Google's Gemini API.
    The LLM reads the context and generates an answer. Because we
    instructed it to only use the provided context, it should ground
    its answer in the actual LS-DYNA manual or project database content.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text


# ============================================================
# STEP 5: FULL RAG PIPELINE
# ============================================================

def ask(query, client, embed_model, collection, n_results=5, verbose=True):
    """
    The complete RAG pipeline in one function:
    Query -> Retrieve -> Build Prompt -> Generate Answer
    
    This is what gets called every time the user asks a question.
    """
    # Step 1: Retrieve relevant chunks
    retrieved = retrieve(query, embed_model, collection, n_results)
    
    if verbose:
        print(f"\nRetrieved {len(retrieved)} chunks:")
        for i, chunk in enumerate(retrieved):
            meta = chunk["metadata"]
            source = meta.get("type", "?")
            detail = ""
            if source == "manual":
                detail = f"Page {meta.get('page', '?')}"
            elif source == "simulation":
                detail = f"{meta.get('project', '?')} / {meta.get('load_case', '?')}"
            print(f"  {i+1}. [{source}] {detail} (distance: {chunk['distance']:.4f})")
    
    # Step 2: Build prompt with context
    prompt = build_prompt(query, retrieved)
    
    if verbose:
        print(f"\nPrompt length: {len(prompt)} characters")
    
    # Step 3: Generate answer
    if verbose:
        print("Generating answer...\n")
    
    answer = generate_answer(prompt, client)
    
    return answer, retrieved


# ============================================================
# MAIN — Interactive mode
# ============================================================

def main():
    print("=" * 60)
    print("FE Software Doc RAG Chatbot")
    print("Loading components...")
    print("=" * 60)
    
    client, embed_model, collection = load_components()
    
    print("\nReady! Type your question (or 'quit' to exit).\n")
    
    while True:
        query = input("You: ").strip()
        
        if not query:
            continue
        if query.lower() in ["quit", "exit", "q"]: ###############!!
            print("Goodbye!")
            break
        
        try:
            answer, sources = ask(query, client, embed_model, collection, n_results=10)
            print(f"\nAssistant: {answer}\n")
            print("-" * 40)
        except Exception as e:
            print(f"\nError: {e}\n")
            print("-" * 40)


if __name__ == "__main__":
    main()