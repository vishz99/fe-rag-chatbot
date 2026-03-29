import json

chunks = json.load(open("data/processed/chunks.json", "r", encoding="utf-8"))
manual = [c for c in chunks if c["type"] == "manual"]

# Find chunks with real content (keyword mentioned + no excessive dots)
good = [c for c in manual if ("MAT_024" in c["text"] or "ELFORM" in c["text"] or "*SECTION_SHELL" in c["text"]) and c["text"].count("...") < 5]

print(f"Genuine content chunks: {len(good)}")

if good:
    print("\n--- Sample content chunk ---")
    print(good[0]["text"][:600])