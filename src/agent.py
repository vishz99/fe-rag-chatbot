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

import json
from typing import TypedDict

from langgraph.graph import StateGraph, END

from rag import load_components

AGENT_MODEL = "nex-agi/nex-n2.5-pro:free"
MAX_ITERATIONS = 3

SYSTEM_PROMPT = """You are an expert LS-DYNA crash simulation engineer assistant with access to two search tools:
- search_manual: searches the LS-DYNA manual for keyword definitions, element formulations, material models, and theory.
- search_simulations: searches the project simulation database for project-specific data (materials, engineers, results).

Decide which tool(s) to call based on the question. You may call a tool more than once with a refined query if the
first results are insufficient, or call both tools for questions that need information from both sources. Once you
have enough context, answer the question directly (make no more tool calls) based ONLY on the retrieved context.
If the context does not contain enough information to answer, say so clearly — do not make up information. When
referencing information, mention the source (manual page number or project name) so the engineer can verify."""


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


# ============================================================
# STEP 2: GRAPH STATE + NODES
# ============================================================

class AgentState(TypedDict):
    """
    State threaded through the graph. `messages` is the OpenAI-style chat
    history (system/user/assistant/tool turns) sent back to the LLM on every
    reasoning call — this is how the LLM "observes" tool results.
    """
    query: str
    messages: list
    retrieved_chunks: list
    tool_call_log: list
    iterations: int
    final_answer: str


def _message_to_dict(msg):
    """
    Convert an OpenAI SDK ChatCompletionMessage object into a plain dict so it
    can be appended to `messages` and round-tripped through the next API call.
    """
    d = {"role": msg.role, "content": msg.content}
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": tc.type,
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return d


def _format_chunks_for_llm(chunks):
    """Render retrieved chunks as a tool-result string the LLM reads to decide its next move."""
    if not chunks:
        return "No results found."
    parts = []
    for i, c in enumerate(chunks):
        meta = c["metadata"]
        if meta.get("type") == "manual":
            src = f"[Manual, Page {meta.get('page', '?')}]"
        else:
            src = f"[Project DB - {meta.get('project', '?')}, {meta.get('load_case', '?')}]"
        parts.append(f"{i + 1}. {src} {c['text']}")
    return "\n\n".join(parts)


def make_reasoning_node(llm_client):
    """
    Factory returning the reasoning node bound to a specific LLM client.
    A closure (rather than stuffing llm_client into AgentState) so the graph
    state stays plain, inspectable data and the client is wired once per
    ask_agentic() call.
    """
    def reasoning_node(state: AgentState) -> AgentState:
        """LLM decides whether to call a retrieval tool or answer directly, given the conversation so far."""
        state["iterations"] += 1
        response = llm_client.chat.completions.create(
            model=AGENT_MODEL,
            messages=state["messages"],
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        msg = response.choices[0].message
        state["messages"].append(_message_to_dict(msg))
        return state

    return reasoning_node


def make_tool_node(embed_model, collection):
    """Factory returning the tool-execution node bound to the embedding model + ChromaDB collection."""
    def tool_node(state: AgentState) -> AgentState:
        """Execute every tool call requested by the last reasoning step and append results as tool messages."""
        last_msg = state["messages"][-1]
        for tc in last_msg.get("tool_calls", []):
            name = tc["function"]["name"]
            try:
                args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                args = {}
            query = args.get("query", state["query"])

            tool_fn = TOOL_FUNCTIONS.get(name)
            chunks = tool_fn(query, embed_model, collection) if tool_fn else []

            state["retrieved_chunks"].extend(chunks)
            state["tool_call_log"].append({"tool": name, "args": args, "n_results": len(chunks)})
            state["messages"].append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": _format_chunks_for_llm(chunks),
            })
        return state

    return tool_node


def answer_node(state: AgentState) -> AgentState:
    """Extract the final answer text from the last assistant message (already produced, no further tool call)."""
    state["final_answer"] = state["messages"][-1].get("content") or ""
    return state


def make_force_answer_node(llm_client):
    """
    Factory returning the node used once MAX_ITERATIONS is hit. The LLM still
    asked for a tool call, but the loop is over — so this makes one last call
    with no `tools` param (it physically cannot call a tool) and an explicit
    instruction to answer now from whatever context has already been gathered.
    """
    def force_answer_node(state: AgentState) -> AgentState:
        """Hard cap reached — ask the LLM to answer now using only context already retrieved, no more tool calls."""
        state["messages"].append({
            "role": "user",
            "content": (
                "You have reached the maximum number of search iterations. "
                "Answer the question now using only the context already retrieved above. "
                "If it is insufficient, say so clearly."
            ),
        })
        response = llm_client.chat.completions.create(
            model=AGENT_MODEL,
            messages=state["messages"],
        )
        msg = response.choices[0].message
        state["messages"].append(_message_to_dict(msg))
        state["final_answer"] = msg.content or ""
        return state

    return force_answer_node


def route_after_reasoning(state: AgentState) -> str:
    """
    Conditional edge: if the LLM asked for tool(s) and the iteration cap
    hasn't been hit, loop back through the tool node. If it asked for
    tool(s) but the cap is hit, force a final answer instead. Otherwise its
    last message (no tool_calls) is already the answer.
    """
    last_msg = state["messages"][-1]
    if last_msg.get("tool_calls"):
        if state["iterations"] < MAX_ITERATIONS:
            return "tool_node"
        return "force_answer_node"
    return "answer_node"


def build_agent_graph(llm_client, embed_model, collection):
    """Wire the reasoning node, tool node, forced-answer node, and conditional edges into a compiled LangGraph graph."""
    graph = StateGraph(AgentState)
    graph.add_node("reasoning_node", make_reasoning_node(llm_client))
    graph.add_node("tool_node", make_tool_node(embed_model, collection))
    graph.add_node("force_answer_node", make_force_answer_node(llm_client))
    graph.add_node("answer_node", answer_node)

    graph.set_entry_point("reasoning_node")
    graph.add_conditional_edges(
        "reasoning_node",
        route_after_reasoning,
        {
            "tool_node": "tool_node",
            "force_answer_node": "force_answer_node",
            "answer_node": "answer_node",
        },
    )
    graph.add_edge("tool_node", "reasoning_node")
    graph.add_edge("force_answer_node", END)
    graph.add_edge("answer_node", END)

    return graph.compile()
