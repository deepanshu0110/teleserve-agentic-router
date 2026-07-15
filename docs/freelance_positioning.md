# Freelance Positioning — "AI Integration" Reframe

Why this framing: on Upwork's 2026 category data, "AI integration"-tagged work grew **+178% YoY**, and chatbot-shaped deliverables specifically grew **+71% YoY**. Clients aren't searching for "data scientist" as often as they're searching for "someone who can wire an LLM into my existing workflow safely." This repo is proof of exactly that — not a chatbot demo, a **routing decision system with a measured performance fix**, which is the part that reads as engineering rather than a tutorial follow-along.

## Profile project blurb (for Upwork/Fiverr/Malt project section)

> **AI Ticket-Routing Agent — LangGraph + Fine-Tuned Classifier + MCP Tools**
> Built an agent that classifies support tickets with a fine-tuned DistilBERT model, checks a live tool via MCP for edge cases, and routes low-confidence tickets to human review instead of guessing. Found and fixed a subprocess-respawn bug that was adding ~4s of latency per call — persistent connection pooling brought it down to ~68ms (208x). Deployed on Streamlit Cloud, fully CPU-based (no GPU dependency), so it's cheap to run and easy to hand off.

*(487 characters — well under the 1500 cap, leaves room to tailor per client.)*

## Proposal opening line (adapt per job post)

> I recently shipped an agentic ticket-router (LangGraph + a fine-tuned classifier + an MCP tool layer) where I found and fixed a real latency bug — a naive tool-call implementation was respawning a subprocess on every request, adding ~4 seconds each time. That's the kind of thing I look for on client integrations too: not just "does the LLM call work," but "does it work at the latency and cost a real user needs."

## Where NOT to use this framing

Don't lead with "AI integration" on jobs explicitly asking for classical BI/dashboard work (Power BI, Tableau, SQL reporting) — there the Month 4–5 portfolio and Naxely's dashboard work are the stronger opener. Reserve this repo and framing for jobs mentioning: chatbot, LLM, automation, agent, RAG, or "integrate AI into."