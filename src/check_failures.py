import json

results = json.load(open("data/processed/evaluation_results.json", "r", encoding="utf-8"))

print("=== FAILED PROJECT QUERIES ===")
# for r in results:
#     if r["category"] == "project" and r["answer_score"]["quality"] != "PASS":
#         print(f"\nQ{r['id']}: {r['question'][:70]}")
#         print(f"  Retrieval correct source: {r['retrieval']['correct_source']}")
#         print(f"  Best distance: {r['retrieval']['best_distance']:.4f}")
#         print(f"  Top 3 sources: {[s['type'] for s in r['sources']]}")
#         print(f"  Retrieval key terms: {r['retrieval']['key_term_hits']}")

for r in results[:10]:
    print(f"\nQ{r['id']}: {r['question'][:60]}")
    print(f"  Quality: {r['answer_score']['quality']}")
    print(f"  Refused: {r['answer_score']['refused']}")
    print(f"  Answer key terms: {r['answer_score']['key_term_hits']}")
    print(f"  Answer: {r['answer'][:300]}")
    print("---")