# Demo GIF — Recording Script

I can't record your screen for you, so here's the exact shot list. Free tool: **ScreenToGif** (Windows) or **Peek** (Linux) — both free, no watermark, direct GIF export. Target: 12–18 seconds, under 8MB so it renders inline on GitHub.

## Shot list (record in this order, one continuous take)

1. **(0:00–0:02)** App loads — show the title and the "Single Ticket" tab already selected.
2. **(0:02–0:06)** Paste in a clear P1 ticket (e.g. an outage-phrased ticket from `sample_tickets.csv`). Click **Classify**. Let the priority/confidence/routing badges render — pause 1s so the GIF captures the settled state, not mid-render.
3. **(0:06–0:09)** Switch to the **Batch CSV** tab. Upload `sample_tickets.csv`. Click **Run Batch**.
4. **(0:09–0:14)** Let the results table populate. Scroll once so the viewer sees the mix of `auto_route` / `human_review` rows and the per-row latency column (this is the number that sells the persistent-client fix — make sure it's visible).
5. **(0:14–0:18)** End on the summary metrics row (avg latency, routing split).

## Settings

- Resolution: crop to just the browser content area, no OS chrome, no taskbar.
- Frame rate: 10–15fps is enough for UI capture, keeps file size down.
- Export: GIF, then run through `gifsicle -O3` if over 8MB:
  ```bash
  gifsicle -O3 --colors 128 demo_raw.gif -o docs/demo.gif
  ```

## Where it goes

Save as `docs/demo.gif` in the repo root — the README already references it at `docs/demo.gif`, so no README edit needed once it's recorded and committed.