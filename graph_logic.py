"""
Day215 — Week4 Day3: Streamlit UI backend logic
================================================
Goal: wrap Day213/214's LangGraph agent (classify_node -> conditional edge ->
mcp_lookup_node / human_review_node) behind a function the Streamlit app can
call, AND fix the Day214 bonus finding: mcp_lookup_node was spawning a brand
new StdioTransport subprocess on every single call, which is why auto_route
tickets (~3.8-4.0s) were ~190-200x slower than human_review tickets (~20ms).

Method: a persistent MCP client that opens its subprocess connection ONCE,
on first use, and keeps it alive for the life of the Streamlit process (via
a background thread running its own asyncio event loop), instead of
re-opening StdioTransport per call. Uses the same thread-bridge pattern
established Day205/207/213 (sync caller -> async MCP client), extended here
to ALSO persist the connection across calls, not just bridge a single call.
"""

import asyncio
import sys
import threading
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# TASK 1: Persistent MCP client manager
# ---------------------------------------------------------------------------

class MCPClientManager:
    """
    Opens one MCP client connection on construction and reuses it for every
    subsequent tool call. Runs its own event loop on a background daemon
    thread so a synchronous caller (graph.invoke(), or a Streamlit button
    handler) can submit async work via run_coroutine_threadsafe without
    creating a new subprocess each time.

    Real (non-mock) mode requires: fastmcp==3.4.4, and Day204's
    resumegap_mcp_server.py (or the TeleServe MCP server, whichever Day204
    file is being reused) reachable at MCP_SERVER_PATH below.
    """

    MCP_SERVER_PATH = "resumegap_mcp_server.py"  # <-- point at Day204's real server file
    LOG_FILE = Path("/tmp/day215_mcp_client.log")

    def __init__(self, mock_mode: bool = True):
        self.mock_mode = mock_mode
        self._call_count = 0
        self._spawn_count = 0  # should stay at 1 in real mode; proves no re-spawn

        if self.mock_mode:
            # No real subprocess in mock mode - simulate the one-time
            # "connect" cost (small here; in real mode Day214 measured
            # ~3.8-4.0s per StdioTransport subprocess spawn) so a
            # persistent-vs-per-call comparison stays directionally
            # meaningful without needing GPU/a real MCP server.
            time.sleep(0.05)
            self._spawn_count = 1
            return

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._client = None
        fut = asyncio.run_coroutine_threadsafe(self._init_client(), self._loop)
        fut.result(timeout=30)

    def _run_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _init_client(self):
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport
        transport = StdioTransport(
            command=sys.executable,  # same interpreter that's running THIS process,
                                      # not a bare "python" that can resolve to a
                                      # different venv (Day215 lesson: hermes-agent
                                      # venv shadowed "python" and had no fastmcp installed)
            args=[self.MCP_SERVER_PATH],
            log_file=self.LOG_FILE,
        )
        self._client = Client(transport)
        await self._client.__aenter__()  # subprocess spawned exactly once, here
        self._spawn_count += 1

    def call_tool(self, tool_name: str, params: dict, timeout: float = 10.0):
        """Synchronous call site — this is what classify_node/mcp_lookup_node call."""
        self._call_count += 1

        if self.mock_mode:
            # Simulate real per-call cost with the connection already open:
            # a few ms, not the ~3.8-4.0s subprocess-spawn cost from Day214.
            time.sleep(0.02)
            return {"tool": tool_name, "params": params, "mock_result": "ok"}

        async def _call():
            return await self._client.call_tool(tool_name, params)

        fut = asyncio.run_coroutine_threadsafe(_call(), self._loop)
        return fut.result(timeout=timeout)

    def close(self):
        if self.mock_mode:
            return
        async def _close():
            await self._client.__aexit__(None, None, None)
        fut = asyncio.run_coroutine_threadsafe(_close(), self._loop)
        fut.result(timeout=10)
        self._loop.call_soon_threadsafe(self._loop.stop)


# ---------------------------------------------------------------------------
# TASK 2: Classifier wrapper (Day211's predict_ticket_priority contract)
# ---------------------------------------------------------------------------

def classify_ticket(text: str, mock_mode: bool = True) -> dict:
    """
    Real mode: import and call Day211's day211_inference_wrapper.predict_ticket_priority.
    Mock mode: deterministic stand-in so the UI/graph wiring can be verified
    without GPU/model (same MOCK_MODE convention as Day213).
    """
    if mock_mode:
        # crude keyword heuristic purely for UI testing, NOT a real model
        t = text.lower()
        if any(k in t for k in ["down", "outage", "not working", "critical", "urgent"]):
            priority, confidence = "P1", 0.91
        elif any(k in t for k in ["slow", "intermittent", "sometimes"]):
            priority, confidence = "P2", 0.55
        else:
            priority, confidence = "P3", 0.82
        return {
            "priority": priority,
            "confidence": confidence,
            "all_probs": {"P1": 0.0, "P2": 0.0, "P3": 0.0},
            "routing_decision": "human_review" if confidence < 0.60 else "auto_route",
        }

    from day211_inference_wrapper import predict_ticket_priority
    return predict_ticket_priority(text)


# ---------------------------------------------------------------------------
# TASK 3: Graph invocation wrapper (Day213/214's compiled StateGraph)
# ---------------------------------------------------------------------------

def run_ticket_through_graph(text: str, mock_mode: bool = True, mcp_manager: "MCPClientManager" = None) -> dict:
    """
    Mirrors Day213/214's node sequence:
      classify_node -> [conditional edge on routing_decision] ->
        auto_route    -> mcp_lookup_node -> END
        human_review  -> human_review_node -> END
    Returns a flat dict the Streamlit UI can render directly.
    """
    start = time.time()

    classification = classify_ticket(text, mock_mode=mock_mode)
    trace = ["classify_node"]

    result = {
        "priority": classification["priority"],
        "confidence": classification["confidence"],
        "routing_decision": classification["routing_decision"],
        "mcp_signal": None,
        "trace": trace,
    }

    if classification["routing_decision"] == "auto_route":
        mgr = mcp_manager or MCPClientManager(mock_mode=mock_mode)
        # resumegap_analyze's real schema needs resume_text/jd_text (min_length=20 each),
        # nested under "params" (Day204 Concept Note 2.4: single-Pydantic-model tools
        # are NOT auto-flattened). Reused generically here as the capstone's MCP-lookup
        # step, not a resume-specific call -- so we feed it the ticket text and a
        # synthetic priority-context string, both long enough to pass validation.
        params = {
            "params": {
                "resume_text": text if len(text) >= 20 else text.ljust(20, "."),
                "jd_text": (
                    f"Priority {classification['priority']} support ticket requiring "
                    f"appropriate routing, triage, and resolution by the support team."
                ),
                "top_n": 5,
            }
        }
        if mock_mode:
            tool_result = mgr.call_tool("resumegap_analyze", params)
            result["mcp_signal"] = tool_result.get("mock_result", "see tool_result")
        else:
            tool_result = mgr.call_tool("resumegap_analyze", params)
            # real mode: fastmcp's call_tool returns a CallToolResult; .data is the dict
            data = getattr(tool_result, "data", tool_result)
            result["mcp_signal"] = data
        trace.append("mcp_lookup_node")
    else:
        result["mcp_signal"] = "n/a — routed to human review, no MCP call made"
        trace.append("human_review_node")

    result["latency_ms"] = (time.time() - start) * 1000
    return result