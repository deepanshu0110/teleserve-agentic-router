# Repo Freeze + Launch Checklist

## Repo freeze (do first, before any GitHub polish)

- [ ] `pip freeze > requirements.txt` from the **actual working venv** (not typed from memory) — pin every version, especially `langgraph==1.2.8`, `langchain-groq==1.1.2`, `fastmcp==3.4.4`, `peft`, `transformers`
- [ ] Confirm `requirements.txt` has **no `bitsandbytes`** — the merged model must run CPU-only; if `bitsandbytes` is still listed, Streamlit Community Cloud deploy will fail
- [ ] Delete the LoRA adapter folder from the repo if the merged model is committed instead (don't ship both — pick one, note the other in README as "training artifact, not required to run")
- [ ] Add `.gitignore`: `__pycache__/`, `.env`, `*.pyc`, `.streamlit/secrets.toml`
- [ ] Confirm `GROQ_API_KEY` is read from `st.secrets` or `os.environ`, never hardcoded — grep the repo for the literal key string before pushing
- [ ] Run the 18-ticket batch one final time on a clean clone to confirm nothing broke in the freeze

## GitHub repo settings

- [ ] **Description** (shows under repo name): "LangGraph agent that classifies support tickets with a fine-tuned DistilBERT model and routes them via a persistent MCP tool client, cutting tool calls from about 3.9 s to 68 ms."
- [ ] **Topics/tags:** `langgraph` `llm-agents` `mcp` `huggingface` `streamlit` `nlp` `distilbert` `lora` `agentic-ai` `python`
- [ ] **Social preview image:** 1280×640px — a screenshot of the routing-decision UI works; GitHub auto-generates one from the README's first image if none is set
- [ ] **License:** MIT (add via GitHub's "Add file → LICENSE" template if not already present)
- [ ] Pin this repo on your GitHub profile (max 6 pinned — replace your weakest current pin)

## Streamlit Community Cloud

- [ ] Python pinned to 3.11 in app settings (same gotcha as ResumeGapAI — no 3.14 wheel for scikit-learn)
- [ ] `GROQ_API_KEY` added under app Settings → Secrets, not committed to the repo
- [ ] Confirm cold-start time is acceptable on the free tier (your local cold start was 14,242ms — cloud cold start will be slower on first load after idle; this is expected, not a bug)

## Post-launch (same day)

- [ ] Post the repo link + demo GIF as a LinkedIn/portfolio update
- [ ] Add the repo link to your Upwork/Fiverr/Malt profile project section