# Act Aware Benchmark — Overview

## Goal

Take Act Aware (built at Barclays Hack-O-Hire, March 2026) from a hackathon demo to
something with measurable, defensible results:

1. Benchmark the existing anomaly-detection ensemble against public intrusion-detection
   datasets (NSL-KDD and CICIDS2017), producing real precision/recall/F1/ROC-AUC numbers.
2. Build a live, publicly hosted dashboard that replays labeled dataset traffic through
   the real detection pipeline and shows the metrics updating in real time.
3. Fold the results back into the portfolio case study (numbers + dashboard link,
   replacing the current purely qualitative description).

## Repo layout

This project lives outside the portfolio repo, as a sibling of it:

```
Personal Projects/
  Vedika Portfolio/        <- portfolio site (untouched by this work, updated at the end)
  act-aware-benchmark/     <- this project
    backend/               <- clone of github.com/Vedika-u/hack_o_hire (untouched reference)
    frontend/               <- clone of github.com/Vedika-u/aware-security-hub (untouched reference)
    benchmark/             <- new work: data pipeline, eval harness, results
    docs/                  <- this folder
```

`backend/` and `frontend/` are the original hackathon repos, cloned read-only for
reference and for extracting the detection logic. We do not modify them in place —
anything reused gets copied/adapted into `benchmark/src/`, so the original hackathon
repos stay exactly as submitted.

## Why this design

- **Per-record scoring, not behavioral windows.** Act Aware's production pipeline
  aggregates raw logs into 15-minute per-user behavioral windows (`aggregate_events` in
  `backend/detection.py`) before scoring. NSL-KDD and CICIDS2017 are labeled at the
  connection/flow level, not the user-session level, and the published literature
  benchmarks detectors on individual records. Forcing dataset rows into synthetic
  per-user windows would (a) be a large, fragile engineering effort with no clear
  "correct" grouping key in a labeled dataset, and (b) make the resulting numbers
  incomparable to any published baseline. Instead we extract the reusable core of
  `run_ensemble_detection` — fit IForest + LOF + HBOS on a numeric feature matrix,
  normalize each model's scores to [0,1], average them — and feed it dataset feature
  columns directly, one row per record. See [02-ensemble-adaptation.md](02-ensemble-adaptation.md).
- **Honest framing over inflated claims.** Because the benchmark validates the
  detection ensemble in isolation rather than the full aggregation → detection →
  correlation → LLM pipeline, the dashboard and portfolio copy say so explicitly. This
  is a stronger, more credible story than implying the whole SIEM-SOAR system was
  benchmarked end-to-end.
- **Static-results fallback + live-replay as the main deliverable.** The plan builds a
  precomputed results view first (cheap, always works, is what a quick skim actually
  reads) and a live-replay demo on top of it (the impressive part, but the higher-risk
  one — see [04-dashboard.md](04-dashboard.md) for the guardrails a public replay
  endpoint needs).

## Phases

| Phase | Doc | Deliverable |
|---|---|---|
| 0 | this doc | Repos cloned, project scaffolded |
| 1 | [01-datasets.md](01-datasets.md) | NSL-KDD and CICIDS2017 acquired and preprocessed |
| 2 | [02-ensemble-adaptation.md](02-ensemble-adaptation.md) | Ensemble extracted for per-record scoring |
| 3 | [03-eval-harness.md](03-eval-harness.md) | Precision/recall/F1/ROC-AUC, per-attack-category breakdown, baseline comparison |
| 4 | [04-dashboard.md](04-dashboard.md) | Live-replay backend + frontend, hosted publicly |
| 5 | [05-portfolio-integration.md](05-portfolio-integration.md) | `content.ts` updated with real numbers + dashboard link |

## Status

Not yet started — this is the design doc set. See each phase doc for current status
and open decisions before implementation begins.
