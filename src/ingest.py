"""
Phase 1: Document Ingestion & Chunking Pipeline
Reads LS-DYNA manual (PDF) and synthetic project database (CSVs),
processes them into text chunks ready for embedding.
"""

import os
import csv
import json
import fitz  # PyMuPDF
from pathlib import Path


# ============================================================
# STEP 1: PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(pdf_path):
    """
    Extract text from each page of a PDF.
    Returns a list of dicts: [{"page": 1, "text": "..."}, ...]
    
    Page-by-page to preserve page numbers so one can later
    tell the engineer using the system the location where in the manual the answer came from.
    """
    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():  # skip blank pages
            pages.append({
                "page": page_num + 1,
                "text": text,
                "source": os.path.basename(pdf_path)
            })
    doc.close()
    print(f"Extracted {len(pages)} pages from {os.path.basename(pdf_path)}")
    return pages


# ============================================================
# STEP 2: CHUNKING
# ============================================================

def chunk_text(text, chunk_size=800, overlap=200):
    """
    Split text into overlapping chunks of roughly chunk_size characters.
    
    Overlap since, if a keyword explanation starts at the end of one chunk,
    the overlap ensures the beginning of that explanation also appears
    in the next chunk. Without overlap, the context is lost at the boundaries.
    
    Why characters not tokens? Simpler to implement, and for a first pass,
    character-based chunking works well enough. We'll tune later.
    """
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():  # don't add empty chunks
            chunks.append(chunk)
        start += chunk_size - overlap  # step forward by (chunk_size - overlap)
    return chunks


def chunk_pdf_pages(pages, chunk_size=800, overlap=200):
    """
    Chunk all pages from a PDF, preserving source metadata.
    Returns list of dicts: [{"text": "...", "source": "...", "page": N}, ...]
    """
    all_chunks = []
    for page in pages:
        chunks = chunk_text(page["text"], chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": page["source"],
                "page": page["page"],
                "chunk_index": i,
                "type": "manual"
            })
    print(f"Created {len(all_chunks)} chunks from PDF")
    return all_chunks

# ============================================================
# STEP 2b: FILTER OUT NOISY CHUNKS
# ============================================================

def filter_noisy_chunks(chunks, dot_threshold=15, min_meaningful_words=30):
    """
    Remove chunks that are mostly table of contents, index pages,
    or other formatting noise.
    
    How noise is detected:
    - TOC pages : "..." dotted lines (dot_threshold)
    - Page numbers or headers (min_meaningful_words)
    
    If noisy chunks stay in, the retrieval step will
    match them to queries (e.g., a TOC line mentioning *MAT_024 matches
    the query "what is MAT_024") aka they contain no useful information.
    The LLM then gets useless context and gives a bad answer.
    """
    clean = []
    removed = 0
    for chunk in chunks:
        text = chunk["text"]
        
        # Count dotted line sequences (TOC indicator)
        dot_count = text.count("...")
        
        # Count actual words (not dots or formatting)
        words = [w for w in text.split() if len(w) > 2 and "." * 3 not in w]
        
        if dot_count > dot_threshold or len(words) < min_meaningful_words:
            removed += 1
            continue
        
        clean.append(chunk)
    
    print(f"Filtered out {removed} noisy chunks, kept {len(clean)}")
    return clean

# ============================================================
# STEP 3: CSV TO NATURAL LANGUAGE DOCUMENTS
# ============================================================

def load_csv(filepath):
    """Load a CSV file into a list of dicts."""
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_simulation_documents(sim_csv, comp_csv, contact_csv):
    """
    Convert structured CSV data into natural language documents.
    
    Why? RAG works by semantic similarity search over text. A CSV row
    like "mat_keyword,*MAT_024" means nothing as a vector. But a sentence
    like "The B-pillar used *MAT_024 (piecewise linear plasticity) with 
    DP780 steel" embeds meaningfully and can be found when an engineer
    asks about B-pillar materials.
    
    Each simulation becomes one document combining info from all three tables.
    """
    simulations = load_csv(sim_csv)
    components = load_csv(comp_csv)
    contacts = load_csv(contact_csv)
    
    # Group components and contacts by sim_id
    comp_by_sim = {}
    for c in components:
        sid = c["sim_id"]
        if sid not in comp_by_sim:
            comp_by_sim[sid] = []
        comp_by_sim[sid].append(c)
    
    contact_by_sim = {}
    for c in contacts:
        sid = c["sim_id"]
        if sid not in contact_by_sim:
            contact_by_sim[sid] = []
        contact_by_sim[sid].append(c)
    
    documents = []
    
    for sim in simulations:
        sid = sim["sim_id"]
        
        # Build the natural language document
        lines = []
        lines.append(f"Crash Simulation Report: {sid}")
        lines.append(f"Project: {sim['project_name']} ({sim['vehicle_segment']})")
        lines.append(f"Project Phase: {sim['project_phase']}")
        lines.append(f"Load Case: {sim['load_case']} ({sim['load_case_code']})")
        lines.append(f"Barrier: {sim['barrier_type']}, Impact Velocity: {sim['impact_velocity_kmh']} km/h")
        lines.append(f"Solver: {sim['solver_version']}, Termination Time: {sim['termination_time_ms']} ms")
        lines.append(f"Engineer: {sim['engineer']}, Date: {sim['date']}")
        lines.append(f"Minimum Timestep: {sim['min_timestep_ms']} ms, Mass Scaling: {sim['mass_scaling']}")
        lines.append(f"")
        lines.append(f"Results:")
        lines.append(f"  Peak Intrusion: {sim['peak_intrusion_mm']} mm")
        lines.append(f"  Peak Force: {sim['peak_force_kn']} kN")
        lines.append(f"  Energy Absorbed: {sim['energy_absorbed_kj']} kJ")
        lines.append(f"  Status: {sim['status']}")
        lines.append(f"  Engineer Notes: {sim['notes']}")
        lines.append(f"")
        
        # Add component details
        sim_comps = comp_by_sim.get(sid, [])
        if sim_comps:
            lines.append(f"Components ({len(sim_comps)} parts):")
            for comp in sim_comps:
                lines.append(
                    f"  - {comp['component_name']} (Part ID: {comp['part_id']}): "
                    f"{comp['material_grade']} using {comp['mat_keyword']}, "
                    f"{comp['element_formulation']}, thickness {comp['thickness_mm']}mm, "
                    f"mesh size {comp['mesh_size_mm']}mm, {comp['num_integration_points']} integration points. "
                    f"Hourglass: {comp['hourglass_type']} ({comp['hourglass_description']}). "
                    f"Strain rate: {comp['strain_rate_model']}"
                    f"{' (' + comp['strain_rate_params'] + ')' if comp['strain_rate_params'] != 'N/A' else ''}."
                )
            lines.append(f"")
        
        # Add contact definitions
        sim_contacts = contact_by_sim.get(sid, [])
        if sim_contacts:
            lines.append(f"Contact Definitions ({len(sim_contacts)}):")
            for ct in sim_contacts:
                lines.append(
                    f"  - {ct['contact_keyword']}: {ct['contact_description']}. "
                    f"Friction: static={ct['static_friction']}, dynamic={ct['dynamic_friction']}. "
                    f"Soft constraint option: {ct['soft_constraint']}. "
                    f"Ignore initial penetration: {ct['ignore_initial_penetration']}."
                )
        
        doc_text = "\n".join(lines)
        documents.append({
            "text": doc_text,
            "source": "project_database",
            "sim_id": sid,
            "project": sim["project_name"],
            "load_case": sim["load_case_code"],
            "type": "simulation"
        })
    
    print(f"Created {len(documents)} simulation documents from CSVs")
    return documents

##### Updated: #################################################################
def split_simulation_documents(documents):
    """
    ##### Added as part of Attempt 3
    Split each simulation document into 2 chunks:
    1. Header + Results + first half of components
    2. Header + Results + second half of components + contacts
    
    The header (project name, load case, engineer, results) is repeated
    in BOTH chunks so that every chunk contains the project identity.
    This solves the problem of Attempt #1 where project name and component
    details ended up in different chunks.
    """
    all_chunks = []
    
    for doc in documents:
        text = doc["text"]
        
        # Find where components section starts
        comp_marker = "Components ("
        contact_marker = "Contact Definitions ("
        
        comp_idx = text.find(comp_marker)
        contact_idx = text.find(contact_marker)
        
        if comp_idx == -1:
            # No components found, keep as single chunk
            all_chunks.append(doc)
            continue
        
        # Header = everything before components
        header = text[:comp_idx].strip()
        
        # Components section
        if contact_idx > comp_idx:
            components_text = text[comp_idx:contact_idx].strip()
            contacts_text = text[contact_idx:].strip()
        else:
            components_text = text[comp_idx:].strip()
            contacts_text = ""
        
        # Split components roughly in half by lines
        comp_lines = components_text.split("\n")
        mid = len(comp_lines) // 2
        comp_first_half = "\n".join(comp_lines[:mid])
        comp_second_half = "\n".join(comp_lines[mid:])
        
        # Build metadata
        meta = {
            "source": doc.get("source", "project_database"),
            "sim_id": doc.get("sim_id", ""),
            "project": doc.get("project", ""),
            "load_case": doc.get("load_case", ""),
            "type": "simulation"
        }
        
        # Chunk 1: Header + first half of components
        chunk1_text = f"{header}\n\n{comp_first_half}"
        chunk1 = {**meta, "text": chunk1_text, "chunk_index": 0}
        all_chunks.append(chunk1)
        
        # Chunk 2: Header + second half of components + contacts
        chunk2_parts = [header, comp_second_half]
        if contacts_text:
            chunk2_parts.append(contacts_text)
        chunk2_text = "\n\n".join(chunk2_parts)
        chunk2 = {**meta, "text": chunk2_text, "chunk_index": 1}
        all_chunks.append(chunk2)
    
    return all_chunks

def chunk_simulation_documents(documents, chunk_size=1200, overlap=200):
    """
    Chunk simulation documents. We use a larger chunk size here
    because each simulation document is a coherent unit and we
    want to keep related info together (e.g., component + its parameters).
    """
    all_chunks = []
    for doc in documents:
        chunks = chunk_text(doc["text"], chunk_size, overlap)
        for i, chunk in enumerate(chunks):
            all_chunks.append({
                "text": chunk,
                "source": doc["source"],
                "sim_id": doc["sim_id"],
                "project": doc["project"],
                "load_case": doc["load_case"],
                "chunk_index": i,
                "type": "simulation"
            })
    print(f"Created {len(all_chunks)} chunks from simulation documents")
    return all_chunks


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_pipeline():
    """Run the full ingestion and chunking pipeline."""
    
    # Paths
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Process PDF ---
    pdf_path = raw_dir / "ls-dyna_manual_volume_i_r13.pdf"
    print(f"\n{'='*60}")
    print(f"Processing PDF: {pdf_path}")
    print(f"{'='*60}")

    # Chunking the (Ls-Dyna) Manual in to chunks of size 800 words with 200 word overlap
    pages = extract_pdf_text(str(pdf_path))
    manual_chunks = chunk_pdf_pages(pages, chunk_size=800, overlap=200)
    manual_chunks = filter_noisy_chunks(manual_chunks)
    
    # --- Process CSVs ---
    print(f"\n{'='*60}")
    print(f"Processing Simulation Database")
    print(f"{'='*60}")
    
    sim_docs = build_simulation_documents(
        str(raw_dir / "simulations.csv"),
        str(raw_dir / "components.csv"),
        str(raw_dir / "contacts.csv")
    )
    
    ##### Attempt #1: 1200-char chunks — splits simulations into ~6 pieces, 
    ##### separating project name from component details. 33% project pass rate.
    # sim_chunks = chunk_simulation_documents(sim_docs, chunk_size=1200, overlap=200)
    
    ##### Attempt #2: Whole documents (~6000-7000 chars) — embedding becomes too 
    ##### vague, retrieval drops to 0% for project queries.
    # sim_chunks = sim_docs
    
    ##### Attempt #3: Split each simulation into 2 focused chunks — header (project 
    ##### info + results) repeated in both, so every chunk contains the project name.
    sim_chunks = split_simulation_documents(sim_docs)
    print(f"Created {len(sim_chunks)} simulation chunks (2 per simulation)")
    
    # --- Combine all chunks ---
    all_chunks = manual_chunks + sim_chunks
    print(f"\n{'='*60}")
    print(f"TOTAL: {len(all_chunks)} chunks")
    print(f"  - Manual chunks: {len(manual_chunks)}")
    print(f"  - Simulation chunks: {len(sim_chunks)}")
    print(f"{'='*60}")
    
    # --- Save processed chunks ---
    output_path = processed_dir / "chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    print(f"\nChunks saved to {output_path}")
    
    # --- Print some sample chunks for inspection ---
    print(f"\n{'='*60}")
    print("SAMPLE MANUAL CHUNK:")
    print(f"{'='*60}")
    for chunk in manual_chunks:
        if "*MAT" in chunk["text"] or "*SECTION" in chunk["text"]:
            print(f"[Page {chunk['page']}]")
            print(chunk["text"][:500])
            print("...")
            break
    
    print(f"\n{'='*60}")
    print("SAMPLE SIMULATION CHUNK:")
    print(f"{'='*60}")
    print(sim_chunks[0]["text"][:500])
    print("...")
    
    return all_chunks


if __name__ == "__main__":
    run_pipeline()
