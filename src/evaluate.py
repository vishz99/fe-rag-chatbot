"""
Phase 4: Evaluation Runner
Runs all 30 test questions through the RAG pipeline,
scores retrieval and answer quality, and saves results.
"""

import json
import time
from test_set import test_questions
from rag import load_components, retrieve, build_prompt, generate_answer


# ============================================================
# SCORING
# ============================================================

def score_retrieval(retrieved_chunks, question):
    """
    Score retrieval quality based on:
    1. Did we get chunks of the right type? (manual/simulation/both)
    2. Are the distances reasonable? (< 1.0 is decent)
    3. Do the retrieved chunks contain any of the key terms?
    """
    scores = {}

    # Check if correct source type was retrieved
    types_retrieved = set(c["metadata"].get("type", "") for c in retrieved_chunks)
    expected_type = question["category"]

    if expected_type == "manual":
        scores["correct_source"] = "manual" in types_retrieved
    elif expected_type == "project":
        scores["correct_source"] = "simulation" in types_retrieved
    elif expected_type == "cross":
        scores["correct_source"] = "manual" in types_retrieved and "simulation" in types_retrieved

    # Best distance (lower is better)
    scores["best_distance"] = min(c["distance"] for c in retrieved_chunks)

    # How many chunks have distance < 1.0 (decent match)
    scores["good_chunks"] = sum(1 for c in retrieved_chunks if c["distance"] < 1.0)

    # Key term hits: check if any key terms appear in retrieved text
    all_retrieved_text = " ".join(c["text"] for c in retrieved_chunks).lower()
    key_terms = question.get("key_terms", [])
    hits = sum(1 for term in key_terms if term.lower() in all_retrieved_text)
    scores["key_term_hits"] = f"{hits}/{len(key_terms)}"
    scores["key_term_ratio"] = hits / len(key_terms) if key_terms else 0

    return scores


def score_answer(answer, question):
    """
    Score answer quality based on:
    1. Does the answer contain key terms from the expected answer?
    2. Did the LLM refuse to answer (indicating retrieval failure)?
    3. Basic length check (too short = likely unhelpful)
    """
    scores = {}
    answer_lower = answer.lower()

    # Check for refusal
    refusal_phrases = [
        "does not contain enough information",
        "cannot answer",
        "not mentioned",
        "no information",
        "not found in",
        "not contain",
        "i cannot"
    ]
    scores["refused"] = any(phrase in answer_lower for phrase in refusal_phrases)

    # Key term hits in the answer
    key_terms = question.get("key_terms", [])
    hits = sum(1 for term in key_terms if term.lower() in answer_lower)
    scores["key_term_hits"] = f"{hits}/{len(key_terms)}"
    scores["key_term_ratio"] = hits / len(key_terms) if key_terms else 0

    # Length
    scores["answer_length"] = len(answer)

    # Overall quality estimate
    if scores["refused"]:
        scores["quality"] = "FAIL - Refused"
    elif scores["key_term_ratio"] >= 0.5:
        scores["quality"] = "PASS"
    elif scores["key_term_ratio"] > 0:
        scores["quality"] = "PARTIAL"
    else:
        scores["quality"] = "FAIL - Wrong"

    return scores


# ============================================================
# MAIN EVALUATION
# ============================================================

def run_evaluation():
    print("=" * 60)
    print("Phase 4: RAG System Evaluation")
    print("=" * 60)

    client, embed_model, collection = load_components()

    results = []
    category_scores = {"manual": [], "project": [], "cross": []}

    for q in test_questions:
        print(f"\n--- Q{q['id']}: {q['question'][:60]}... ---")

        # Retrieve
        retrieved = retrieve(q["question"], embed_model, collection, n_results=10)
        retrieval_scores = score_retrieval(retrieved, q)

        # Generate
        prompt = build_prompt(q["question"], retrieved)
        try:
            answer = generate_answer(prompt, client)
            time.sleep(2)  # Rate limit: 10 RPM for free tier
        except Exception as e:
            answer = f"ERROR: {e}"
            time.sleep(5)

        # Score answer
        answer_scores = score_answer(answer, q)

        # Store result
        result = {
            "id": q["id"],
            "category": q["category"],
            "question": q["question"],
            "expected": q["expected"],
            "answer": answer,
            "retrieval": retrieval_scores,
            "answer_score": answer_scores,
            "sources": [
                {
                    "type": c["metadata"].get("type"),
                    "distance": round(c["distance"], 4),
                    "page": c["metadata"].get("page", ""),
                    "project": c["metadata"].get("project", "")
                }
                for c in retrieved[:3]
            ]
        }
        results.append(result)
        category_scores[q["category"]].append(answer_scores["quality"])

        # Print summary
        quality = answer_scores["quality"]
        best_dist = retrieval_scores["best_distance"]
        correct_src = retrieval_scores["correct_source"]
        print(f"  Quality: {quality} | Best dist: {best_dist:.4f} | Correct source: {correct_src}")
        print(f"  Retrieval key terms: {retrieval_scores['key_term_hits']} | Answer key terms: {answer_scores['key_term_hits']}")

    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    for cat in ["manual", "project", "cross"]:
        scores = category_scores[cat]
        total = len(scores)
        passed = scores.count("PASS")
        partial = scores.count("PARTIAL")
        failed = total - passed - partial
        print(f"\n{cat.upper()} ({total} questions):")
        print(f"  PASS: {passed}/{total} ({100*passed//total}%)")
        print(f"  PARTIAL: {partial}/{total}")
        print(f"  FAIL: {failed}/{total}")

    all_scores = [r["answer_score"]["quality"] for r in results]
    total = len(all_scores)
    passed = all_scores.count("PASS")
    partial = all_scores.count("PARTIAL")
    failed = total - passed - partial
    print(f"\nOVERALL ({total} questions):")
    print(f"  PASS: {passed}/{total} ({100*passed//total}%)")
    print(f"  PARTIAL: {partial}/{total}")
    print(f"  FAIL: {failed}/{total}")

    # Save detailed results
    output_path = "data/processed/evaluation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to {output_path}")

    return results


if __name__ == "__main__":
    run_evaluation()