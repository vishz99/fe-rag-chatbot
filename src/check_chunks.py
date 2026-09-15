import json

chunks = json.load(open("data/processed/chunks.json", "r", encoding="utf-8"))
manual = [c for c in chunks if c["type"] == "manual"]

# Find chunks with real content (keyword mentioned + no excessive dots)
good = [c for c in manual if ("MAT_024" in c["text"] or "ELFORM" in c["text"] or "*SECTION_SHELL" in c["text"]) and c["text"].count("...") < 5]

print(f"Genuine content chunks: {len(good)}")

if good:
    print("\n--- Sample content chunk ---")
    print(good[0]["text"][:600])

"""
--- Sample content chunk ---
 capability is not yet im-
plemented for MPP applications. 
• A binary option for the ASCII ﬁles is now available.  This option applies to all 
ASCII ﬁles and results in one binary ﬁle that contains all the information normal-
ly spread between a large number of separate ASCII ﬁles. 
• Material models can now be deﬁned by numbers rather than long names in the 
keyword input.  For example the keyword *MAT_PIECEWISE_LINEAR_PLAS-
TICITY can be replaced by the keyword: *MAT_024. 
• An embedded NASTRAN reader for direct reading of NASTRAN input ﬁles is 
available.  This option allows a typical inpu
"""