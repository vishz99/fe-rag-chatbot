"""
Phase 5: Streamlit UI for FE Software Doc RAG Chatbot
A simple web interface for engineers to query the LS-DYNA manual
and project database using natural language.
"""

import streamlit as st
from rag import load_components, ask


# ============================================================
# PAGE CONFIGURATION
# ============================================================
# Sets the browser tab title, icon, and layout.
# "wide" layout uses the full browser width for better readability.
st.set_page_config(
    page_title="FE Software Doc Assistant",
    page_icon="🔧",
    layout="wide"
)


# ============================================================
# COMPONENT LOADING (cached)
# ============================================================
# @st.cache_resource tells Streamlit to load the components once
# and keep them in memory across user interactions. Without this,
# every question would reload the embedding model and vector store,
# which takes several seconds each time.
@st.cache_resource
def get_components():
    """Load LLM client, embedding model, and vector store once."""
    return load_components()


# ============================================================
# UI LAYOUT
# ============================================================

# Header section
st.title("🔧 FE Software Doc Assistant")
st.caption("RAG-powered chatbot for LS-DYNA manuals and crash simulation project databases")

# Load components (happens once, cached for entire session)
with st.spinner("Loading system components..."):
    client, embed_model, collection = get_components()

# Sidebar with information about the system
# The sidebar is a collapsible panel on the left side of the UI
with st.sidebar:
    st.header("About")
    st.markdown("""
    This assistant uses **Retrieval-Augmented Generation** to answer
    engineering questions by searching:
    
    - **LS-DYNA R13 Manual** (9,051 chunks)
    - **Project Database** (32 simulations)
    
    **Tech Stack:**
    - Embedding: all-MiniLM-L6-v2 (local)
    - Vector DB: ChromaDB
    - LLM: Qwen 3.6 Plus (OpenRouter)
    """)
    
    st.header("Example Questions")
    # These are clickable example questions that populate the input box.
    # st.session_state is Streamlit's way of storing values between interactions.
    examples = [
        "What is *MAT_024 piecewise linear plasticity?",
        "What material was used for the B-pillar in the Atlas-X SOF simulation?",
        "What element formulation is recommended for shell elements in crash?",
        "Which simulations used Cowper-Symonds strain rate model?",
        "What is hourglass control and why is it needed?",
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex[:20]}", use_container_width=True):
            st.session_state["user_query"] = ex

# Retrieval settings in an expandable section
# st.expander creates a collapsible UI element
with st.expander("⚙️ Retrieval Settings"):
    # Slider lets the user control how many chunks are retrieved.
    # More chunks give the LLM more context but slower responses.
    n_results = st.slider(
        "Number of chunks to retrieve",
        min_value=3,
        max_value=15,
        value=10,
        help="How many document chunks to retrieve for each query"
    )


# ============================================================
# CHAT HISTORY (session state)
# ============================================================
# Streamlit reruns the entire script on every interaction, so we need
# session_state to persist data between reruns. Without this, the chat
# history would disappear on every new question.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing chat history
# Iterates through all previous messages and renders them
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # If the message has sources (assistant message), show them in an expander
        if "sources" in msg and msg["sources"]:
            with st.expander(f"📚 Sources ({len(msg['sources'])} chunks)"):
                for i, src in enumerate(msg["sources"]):
                    meta = src["metadata"]
                    source_type = meta.get("type", "unknown")
                    distance = src["distance"]
                    
                    if source_type == "manual":
                        page = meta.get("page", "?")
                        st.markdown(f"**{i+1}. LS-DYNA Manual, Page {page}** _(distance: {distance:.3f})_")
                    elif source_type == "simulation":
                        project = meta.get("project", "?")
                        load_case = meta.get("load_case", "?")
                        st.markdown(f"**{i+1}. Project: {project} / {load_case}** _(distance: {distance:.3f})_")
                    
                    # Show a preview of the chunk text (first 300 chars)
                    st.text(src["text"][:300] + ("..." if len(src["text"]) > 300 else ""))
                    st.divider()


# ============================================================
# USER INPUT
# ============================================================
# st.chat_input creates a text input at the bottom of the page.
# It returns the user's text when they press Enter.
user_input = st.chat_input("Ask a question about LS-DYNA or your simulations...")

# If the user clicked an example button, use that instead
if "user_query" in st.session_state:
    user_input = st.session_state.pop("user_query")


# ============================================================
# PROCESS USER QUERY
# ============================================================
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })
    
    # Display the user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        # Show a loading indicator while the LLM generates the answer
        with st.spinner("Searching documents and generating answer..."):
            try:
                # Call the RAG pipeline from rag.py
                # verbose=False to avoid printing debug info to the terminal
                answer, retrieved = ask(
                    user_input,
                    client,
                    embed_model,
                    collection,
                    n_results=n_results,
                    verbose=False
                )
                
                # Display the answer
                st.markdown(answer)
                
                # Show sources in an expandable section
                with st.expander(f"📚 Sources ({len(retrieved)} chunks)"):
                    for i, src in enumerate(retrieved):
                        meta = src["metadata"]
                        source_type = meta.get("type", "unknown")
                        distance = src["distance"]
                        
                        if source_type == "manual":
                            page = meta.get("page", "?")
                            st.markdown(f"**{i+1}. LS-DYNA Manual, Page {page}** _(distance: {distance:.3f})_")
                        elif source_type == "simulation":
                            project = meta.get("project", "?")
                            load_case = meta.get("load_case", "?")
                            st.markdown(f"**{i+1}. Project: {project} / {load_case}** _(distance: {distance:.3f})_")
                        
                        st.text(src["text"][:300] + ("..." if len(src["text"]) > 300 else ""))
                        st.divider()
                
                # Save to session history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": retrieved
                })
                
            except Exception as e:
                # If something goes wrong (API error, connection issue),
                # show a friendly error message instead of crashing.
                error_msg = f"Error generating answer: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "sources": []
                })


# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Built with Streamlit, ChromaDB, and Qwen 3.6 Plus via OpenRouter")

######################################################################
# To run this app:
# streamlit run src/app.py
######################################################################
