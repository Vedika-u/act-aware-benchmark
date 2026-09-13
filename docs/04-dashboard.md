# Live-Replay Dashboard

Chosen scope (per project decision): live-replay demo as the primary deliverable, not
just a static results page — this is the higher-effort, higher-payoff option, so it
gets a real design pass rather than being an afterthought.

## What it does

A public visitor opens the dashboard and watches labeled dataset rows (NSL-KDD and/or
CICIDS2017 test-set records) get streamed, one at a time or in small batches, through
the actual extracted ensemble scoring logic
([02-ensemble-adaptation.md](02-ensemble-adaptation.md)), with:

- a live-scrolling feed of events (row features summarized + ground-truth label +
  ensemble score + predicted label)
- a running confusion matrix that updates as rows stream in
- running precision/recall/F1 that update live, converging toward the precomputed
  benchmark numbers as the replay progresses (this convergence *is* the demo — it
  visibly proves the precomputed numbers aren't fabricated)
- a toggle between NSL-KDD and CICIDS2017 replay
- a static "final benchmark results" panel (from
  [03-eval-harness.md](03-eval-harness.md)'s JSON output) always visible alongside the
  live view, so a visitor who doesn't want to wait for the replay to finish still sees
  the headline numbers immediately

## Architecture

```
frontend (React/Vite, styled consistent with aware-security-hub)
      │  websocket or SSE stream
      ▼
backend (FastAPI, thin wrapper around benchmark/src/ensemble.py)
      │
      ▼
fixed replay dataset (pre-loaded NSL-KDD/CICIDS2017 test rows, already
scored offline — replay speed is a UI pacing choice, not live model
inference per row, see "real-time" note below)
```

### "Real-time" clarification

Streaming genuine per-row PyOD inference live, in response to arbitrary public
traffic, isn't the right design — `IForest`/`LOF`/`HBOS` here are fit once against a
fixed training split (see [03-eval-harness.md](03-eval-harness.md)'s fit/score
section); there's no meaningful "re-fit per visitor" step. What's real: every row's
ensemble score was computed by the actual extracted ensemble logic on genuine dataset
rows — nothing is faked, animated, or randomly generated. What's staged for the demo:
the *replay pacing* (rows revealed at a visitor-controlled or fixed rate rather than as
fast as possible) and the *dataset* (fixed test-set rows, not arbitrary user-submitted
input). The dashboard copy should say this plainly rather than implying live model
retraining per visitor.

## Guardrails (public endpoint)

Since this is a live backend exposed to the public internet:
- **No arbitrary input.** The replay endpoint only serves pre-loaded, pre-scored
  dataset rows — never accepts user-uploaded data for scoring. Removes the entire
  injection/abuse-via-malicious-input surface.
- **Rate limiting** per IP/session on the replay-control endpoints.
- **Bounded resource use**: replay is reading precomputed scores from a small file/DB,
  not re-running PyOD inference per request — cheap regardless of traffic.
- **Session-scoped state only** (which row a given visitor's replay is on) — no shared
  mutable state between visitors, no persistence needed beyond the process lifetime.
- **CORS** locked to the dashboard's own frontend origin.

## Hosting

- Backend: Render or Fly.io (small instance; scale-to-zero acceptable given bursty
  portfolio-visitor traffic patterns).
- Frontend: Vercel or Netlify, matching the pattern already used for the portfolio
  site's GitHub Pages deploy (see portfolio repo's recent "Add GitHub Pages deployment"
  commit) — consistent tooling across the two.
- Wire real CORS + environment-based API base URL (no hardcoded IPs — note the existing
  `backend/detection.py` has a hardcoded Elasticsearch IP left over from the hackathon;
  don't repeat that pattern here).

## Visual design

Reuse `frontend/` (aware-security-hub)'s existing component library and Tailwind theme
for visual continuity with the rest of the SOC dashboard aesthetic already built for
Act Aware, rather than designing a new visual language from scratch — the benchmark
dashboard should read as "part of Act Aware," not as an unrelated side project.

## Status

Not yet built. Depends on Phase 3 (eval harness) producing the precomputed results JSON
that seeds both the static panel and the replay dataset's pre-scored rows.
