"""
Day215 — Week4 Day3: Capstone Streamlit UI
===========================================
Wraps the Day213/214 LangGraph agent (classifier + MCP tool) in a
client-facing UI: paste a ticket, see priority / confidence / routing
decision / MCP signal. Also supports batch scoring via CSV upload
(same "always ship a test CSV alongside a Streamlit+batch-prediction day"
convention used on prior Streamlit days).

Run locally:   streamlit run app.py
Deploy:        same flow as ResumeGapAI -> Streamlit Community Cloud
"""

import time
import pandas as pd
import streamlit as st

from graph_logic import MCPClientManager, run_ticket_through_graph

st.set_page_config(page_title="TeleServe Support Agent", layout="centered")

st.title("TeleServe India — Support Ticket Agent")
st.caption("LangGraph agent + fine-tuned classifier (Day209-211) + MCP tool (Day204) — Capstone Day215")

MOCK_MODE = st.sidebar.checkbox(
    "Mock mode (no GPU / real MCP server needed)",
    value=True,
    help="Uncheck only when running where the Day211 adapter and Day204 MCP server are available (Colab/deployed env with GPU + server file).",
)

# Persistent MCP client — created ONCE per Streamlit process (st.cache_resource),
# reused across every button click and every row of a batch upload. This is the
# Day215 fix for Day214's per-call subprocess-spawn latency finding.
@st.cache_resource
def get_mcp_manager(mock_mode: bool):
    return MCPClientManager(mock_mode=mock_mode)

mcp_manager = get_mcp_manager(MOCK_MODE)

tab_single, tab_batch = st.tabs(["Single ticket", "Batch (CSV)"])

with tab_single:
    ticket_text = st.text_area(
        "Paste ticket text",
        height=120,
        placeholder="e.g. My internet has been down for 3 days and no one has responded.",
    )

    if st.button("Route Ticket", type="primary"):
        if not ticket_text.strip():
            st.warning("Enter ticket text first.")
        else:
            with st.spinner("Running agent..."):
                result = run_ticket_through_graph(ticket_text, mock_mode=MOCK_MODE, mcp_manager=mcp_manager)

            col1, col2, col3 = st.columns(3)
            col1.metric("Priority", result["priority"])
            col2.metric("Confidence", f"{result['confidence']:.0%}")
            col3.metric("Routing", result["routing_decision"])

            if result["routing_decision"] == "auto_route":
                st.success(f"MCP tool signal: {result['mcp_signal']}")
            else:
                st.info("Flagged for human review — confidence below the 0.60 threshold (Day210/211).")

            st.caption(f"Trace: {' -> '.join(result['trace'])} | Latency: {result['latency_ms']:.0f} ms")

with tab_batch:
    st.write("Upload a CSV with a `ticket_text` column to route a batch of tickets.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])

    if uploaded is not None:
        df = pd.read_csv(uploaded)
        if "ticket_text" not in df.columns:
            st.error("CSV must contain a `ticket_text` column.")
        else:
            with st.spinner(f"Routing {len(df)} tickets..."):
                rows = []
                t0 = time.time()
                for text in df["ticket_text"].astype(str):
                    r = run_ticket_through_graph(text, mock_mode=MOCK_MODE, mcp_manager=mcp_manager)
                    rows.append({
                        "ticket_text": text,
                        "priority": r["priority"],
                        "confidence": round(r["confidence"], 4),
                        "routing_decision": r["routing_decision"],
                        "latency_ms": round(r["latency_ms"], 1),
                    })
                total_s = time.time() - t0

            out_df = pd.DataFrame(rows)
            st.dataframe(out_df, use_container_width=True)
            st.caption(
                f"{len(df)} tickets routed in {total_s:.2f}s "
                f"({out_df['routing_decision'].eq('auto_route').sum()} auto_route, "
                f"{out_df['routing_decision'].eq('human_review').sum()} human_review)."
            )
            st.download_button(
                "Download results CSV",
                out_df.to_csv(index=False).encode("utf-8"),
                "day215_batch_results.csv",
                "text/csv",
            )
