# TeleServe Agentic Router

**A LangGraph-based support-ticket triage agent** that classifies incoming tickets with a fine-tuned DistilBERT (LoRA) model, checks a live MCP knowledge-base tool for edge cases, and routes each ticket to auto-resolution or human review. A persistent-connection fix cut the tool call from about 3.9 seconds to 68 ms per ticket.

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/streamlit-app-FF4B4B.svg)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/langgraph-1.2.8-1C3C3C.svg)](https://github.com/langchain-ai/langgraph)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
**[Live Demo → teleserve-agentic-router.streamlit.app](https://teleserve-agentic-router-tmwo3kyftn9ix8mdgaqk64.streamlit.app)** 

![Demo](docs/demo.gif)

---

## Why this exists

Most "chatbot" portfolio projects retrieve an answer and stop. This one makes a **decision under uncertainty**: it classifies a ticket, checks its own confidence, calls an external tool only when the ticket needs it, and hands off to a human when confidence drops below threshold. That is the same shape as a real support-routing system.

**Data note:** TeleServe India is a fictional telecom company. The classifier was trained on 450 synthetic tickets (150 per priority class, P1/P2/P3) generated from sentence templates, and tested on new-wording and hand-written sets described below.

## Architecture

```
                 ┌─────────────────┐
   ticket text → │  classify_node   │  (LoRA-merged DistilBERT, CPU inference)
                 └────────┬─────────┘
                          │ priority + confidence
                 ┌────────▼─────────┐
                 │ routing_decision  │  (confidence ≥ 0.60 ?)
                 └────┬────────┬────┘
             auto_route      human_review
                 │                │
        ┌────────▼────────┐      │
        │ mcp_lookup_node  │      │
        │ (persistent MCP  │      │
        │  client, ~68ms)  │      │
        └────────┬────────┘      │
                 └───────┬────────┘
                       END
```

- **Classifier:** DistilBERT + LoRA (PEFT), merged to full precision (`merge_and_unload`) for CPU-only inference. No `bitsandbytes` or GPU dependency, so it runs on Streamlit Community Cloud and on a laptop with no discrete GPU.
- **Orchestration:** LangGraph `StateGraph` with a conditional edge on `routing_decision`.
- **Tool layer:** a custom MCP server (FastMCP) queried through a **persistent `MCPClientManager`**: a background asyncio thread holding one long-lived `StdioTransport` subprocess, reused across every call instead of respawned per call.
- **UI:** Streamlit, single-ticket + batch CSV tabs, live display of priority, confidence, routing decision and MCP signal.

## Classifier evaluation: 100% on validation, 60% on new wording

The headline finding of this project is a generalisation gap. Full evaluation, with classification reports and confusion matrices, is in [`day210_Evaluation_Report.ipynb`](https://github.com/deepanshu0110/Month13-Agentic-AI-Portfolio/blob/main/day210_Evaluation_Report.ipynb) in the Month 13 repo.

| Test set | Size | Untrained baseline | Fine-tuned |
|---|---|---|---|
| Validation split (same templates as training) | 90 | 17.8% | **100.0%** |
| New templated set (different wording pool) | 90 | 37.8% | **60.0%** |
| Hand-written set (natural phrasing, no templates) | 30 | 36.7% | **60.0%** |

**Hand-written set, fine-tuned model:**

| Class | Precision | Recall | Support |
|---|---|---|---|
| P1 (critical) | 1.00 | 0.50 | 10 |
| P2 (moderate) | 0.75 | 0.30 | 10 |
| P3 (low) | 0.48 | 1.00 | 10 |

Confusion matrix (rows = true, columns = predicted):

```
       P1   P2   P3
P1     5    1    4
P2     0    3    7
P3     0    0   10
```

**What this shows:** the model memorised the training templates rather than learning what makes a ticket urgent. On natural phrasing it falls back to P3, and it missed 5 of 10 critical P1 tickets.

**Why the 0.60 threshold:** on the evaluation run, average confidence was 0.877 on correct predictions and 0.640 on incorrect ones, so low-confidence tickets go to human review.

## The latency bug

Early integration testing showed `auto_route` tickets taking about 3.8 to 4.0 s each, while `human_review` tickets returned in about 20 ms. The `human_review` path skips the MCP tool, so the slowdown had to be in `mcp_lookup_node`. Root cause: it spawned a **new subprocess on every call**. Fix: a singleton `MCPClientManager`, initialised once at app start via `st.cache_resource`, holding one persistent connection for the app's lifetime.

**Measured on an 18-ticket batch, real model and real MCP subprocess (not mocked):**

| | Before (subprocess per call) | After (persistent client) |
|---|---|---|
| Per-call latency, auto-routed ticket | about 3,800 to 4,000 ms | **68.4 ms avg** (range 48.7 to 98.5 ms) |
| One-time startup (model load + subprocess spawn) | not measured separately | 14,242 ms, paid once per app session |

Caveat: the "before" figure was measured during Colab integration testing with the 4-bit model, and the "after" figure on a local CPU with the merged model. Both use real MCP calls, but the setups are not identical.

## Known limitations

- **Generalisation:** 60% accuracy on new wording (see evaluation above). The model has not been retrained on more varied data yet.
- **Threshold evidence is thin:** on a separate 20-ticket test (Day 211), auto-routed tickets were classified correctly 68.75% of the time and human-review tickets 75%. Only 4 tickets went to human review, so this does not prove the threshold helps. A 50+ ticket test is needed.
- **In the live app:** 2 of 3 outage-style tickets in the 18-ticket batch were predicted P2 instead of P1. Both had low confidence and were sent to human review rather than auto-routed.

## Tech stack

`langgraph` `langchain-groq` `fastmcp` `peft` `transformers` `streamlit` `pandas` `scikit-learn`

## Quickstart

```bash
git clone https://github.com/deepanshu0110/teleserve-agentic-router.git
cd teleserve-agentic-router
pip install -r requirements.txt
streamlit run app.py
```

Requires a free [Groq API key](https://console.groq.com) set as `GROQ_API_KEY`. The model file is stored with Git LFS, so install [Git LFS](https://git-lfs.com) before cloning.

## Project structure

```
teleserve-agentic-router/
├── app.py                        # Streamlit UI (single-ticket + batch tabs)
├── graph_logic.py                # LangGraph StateGraph + MCPClientManager
├── day211_inference_wrapper.py   # predict_ticket_priority() on the merged model
├── resumegap_mcp_server.py       # FastMCP tool server (Day 204)
├── resumegap_engine.py           # matching engine used by the MCP tool
├── check_model.py                # sanity check that the merged model loads
├── teleserve_merged_215/         # merged full-precision DistilBERT (Git LFS)
├── day215_test_batch.csv         # 18-ticket batch used for the latency test
├── docs/
│   └── demo.gif
└── requirements.txt
```

## Roadmap

- [ ] Retrain on more varied, non-templated tickets and re-run the Day 210 evaluation
- [ ] Re-test the 0.60 threshold on 50+ fresh tickets
- [ ] Swap Groq for a local Ollama model (offline fallback)

---

Built as part of a structured 13-month applied AI/ML program. Related: [ResumeGapAI](https://resumegapai.streamlit.app) (live) · [Month 13 portfolio](https://github.com/deepanshu0110/Month13-Agentic-AI-Portfolio) (training and evaluation notebooks).
