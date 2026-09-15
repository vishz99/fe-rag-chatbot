"""
Phase 6: Agentic Retrieval (7.0)
Replaces keyword-based routing (rag.py's retrieve()) with genuine agentic
decision-making: the LLM itself decides which source(s) to search via
OpenAI-style tool calling, observes what comes back, and decides whether to
search again or answer — instead of an if/else router on keyword lists.

This is a new, separate module. It does NOT modify retrieve() in rag.py —
the existing keyword-routed pipeline (rag.py, evaluate.py, app.py) is
untouched and keeps working exactly as before.

Model note: rag.py's model id "qwen/qwen3.6-plus:free" is deprecated on
OpenRouter (confirmed via a direct API call — returns HTTP 404, "transition
to qwen/qwen3.6-plus for continued paid access"). This affects the existing
pipeline too, not just this module, but that's out of scope here. For this
module, swapped to "nex-agi/nex-n2.5-pro:free", the first free OpenRouter
model tested (checked against supported_parameters containing "tools") that
returned a well-formed tool_calls response on a raw API call.
"""

from rag import load_components

AGENT_MODEL = "nex-agi/nex-n2.5-pro:free"
MAX_ITERATIONS = 3


# ============================================================
# STEP 1: TOOLS — thin wrappers around the existing ChromaDB collection
# ============================================================
# Reuse the same embedding model + ChromaDB where-filtering already present
# in rag.py's retrieve() (do not duplicate its keyword-routing logic — these
# wrappers just expose the two source types as directly callable tools).

def search_manual(query, embed_model, collection, n_results=5):
    """
    Search LS-DYNA manual chunks only (type == "manual").
    Called by the agent when it decides the question needs manual/theory
    documentation rather than project-specific simulation data.
    """
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where={"type": "manual"},
    )
    return _package(results)


def search_simulations(query, embed_model, collection, n_results=5):
    """
    Search project/simulation database chunks only (type == "simulation").
    Called by the agent when it decides the question needs project-specific
    data (materials used, engineers, simulation results).
    """
    query_embedding = embed_model.encode([query]).tolist()
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        where={"type": "simulation"},
    )
    return _package(results)


def _package(results):
    """Convert a raw ChromaDB query result into the {text, metadata, distance} shape used elsewhere in the project."""
    packaged = []
    if not results["ids"] or not results["ids"][0]:
        return packaged
    for i in range(len(results["ids"][0])):
        packaged.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return packaged


# OpenAI-style tool schemas describing the two tools above to the LLM.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_manual",
            "description": (
                "Search the LS-DYNA manual for keyword definitions, element "
                "formulations, material models, contact types, and general "
                "theory/usage documentation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. a keyword or concept name.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_simulations",
            "description": (
                "Search the project simulation database for project-specific "
                "data: materials used per component, engineers who ran a "
                "simulation, simulation results (peak force, intrusion, "
                "failures), and element formulations per project."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query, e.g. a project name or simulation attribute.",
                    },
                },
                "required": ["query"],
            },
        },
    },
]

# Maps a tool name from a tool_call back to the actual Python function.
TOOL_FUNCTIONS = {
    "search_manual": search_manual,
    "search_simulations": search_simulations,
}
