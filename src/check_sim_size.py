import json

chunks = json.load(open("data/processed/chunks.json", "r", encoding="utf-8"))

# Find simulation chunks and group by sim_id
sim_chunks = [c for c in chunks if c["type"] == "simulation"]
sim_ids = set(c.get("sim_id", "") for c in sim_chunks)

print(f"Total simulation chunks: {len(sim_chunks)}")
print(f"Unique simulations: {len(sim_ids)}")
print(f"Average chunks per simulation: {len(sim_chunks)/len(sim_ids):.1f}")

# Check size of original simulation documents
from ingest import build_simulation_documents
docs = build_simulation_documents(
    "data/raw/simulations.csv",
    "data/raw/components.csv",
    "data/raw/contacts.csv"
)
for d in docs[:3]:
    print(f"\n{d.get('sim_id', '?')}: {len(d['text'])} characters")
    print(d["text"][:200] + "...")