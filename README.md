<div align="center">

# Act Aware Benchmark

**Turning a hackathon SIEM-SOAR demo into a benchmarked, defensible anomaly detector.**

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](benchmark/requirements.txt)
[![PyOD](https://img.shields.io/badge/PyOD-IForest_%2B_LOF_%2B_HBOS-FF6F00)](https://pyod.readthedocs.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-live--replay_API-009688?logo=fastapi&logoColor=white)](benchmark/dashboard_backend)
[![React](https://img.shields.io/badge/React_19-dashboard-61DAFB?logo=react&logoColor=white)](benchmark/dashboard_frontend)
[![Tests](https://img.shields.io/badge/tests-parity_verified-brightgreen)](benchmark/tests/test_ensemble.py)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

</div>

---

## What this is

[Act Aware](backend/README.md) is an AI-powered SIEM-SOAR platform built at a
banking-security hackathon (Team Phoenix Core, March 2026): a 10-layer
pipeline that ingests security logs, builds behavioral profiles per user,
runs an unsupervised anomaly-detection ensemble (Isolation Forest + LOF +
HBOS) over 3,000+ engineered features, correlates multi-stage attacks, and
proposes human-approved SOAR response playbooks via a local LLM.

Like most hackathon projects, its detection claims were qualitative — "our
ensemble reduces false positives" with no independently reproducible number
behind it. **This repository is the follow-up work that fixes that.** It:

1. **Extracts the actual scoring logic** (`run_ensemble_detection` from
   [`backend/detection.py`](backend/detection.py)) out of its hackathon-specific
   pipeline, byte-for-byte, and verifies the extraction with a parity test
   ([`benchmark/tests/test_ensemble.py`](benchmark/tests/test_ensemble.py)).
2. **Benchmarks that exact logic** against public, peer-reviewed intrusion-detection
   datasets ([NSL-KDD](https://www.unb.ca/cic/datasets/nsl.html) and
   [CICIDS2017](https://www.unb.ca/cic/datasets/ids-2017.html)) — real
   precision/recall/F1/ROC-AUC numbers, a per-attack-category breakdown, and a
   comparison against published baselines, not self-graded metrics.
3. **Ships a live-replay dashboard** (FastAPI + React) that streams labeled
   test-set rows through the real ensemble and shows precision/recall
   converging live toward the precomputed numbers — visible proof the
   headline metrics aren't fabricated.

The point isn't just "I can train an anomaly detector." It's **methodological
honesty under pressure to look good**: reporting the as-shipped threshold
next to the tuned one, reporting per-category recall instead of hiding weak
categories behind a strong aggregate, citing exact baseline papers, and
scoping the claim to what was actually validated (the detection ensemble)
rather than implying the whole 10-layer pipeline was benchmarked end-to-end.
See [`docs/00-overview.md`](docs/00-overview.md) for the full reasoning.

## Results (NSL-KDD)

Fit on the official `KDDTrain+` split, scored on the official `KDDTest+`
split — which deliberately includes attack types absent from training, a
genuine generalization test, not held-out i.i.d. rows. Full methodology and
caveats in [`docs/03-eval-harness.md`](docs/03-eval-harness.md); raw output in
[`benchmark/results/nsl_kdd.json`](benchmark/results/nsl_kdd.json).

| Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|
| **0.5** (as shipped in production) | 0.984 | 0.005 | 0.010 | 0.878 | 0.885 |
| **0.075** (best-F1 on test set) | 0.786 | 0.952 | 0.861 | — | — |

The gap between those two rows is the actual finding, not a footnote: the
ensemble separates attack from normal traffic well (ROC-AUC 0.88), but the
`contamination=0.15`-derived threshold the hackathon build ships with is
miscalibrated for NSL-KDD's ~57% test-set attack ratio, so it barely fires.
Recall by attack category at the tuned threshold:

| DoS | Probe | R2L | U2R |
|---|---|---|---|
| 99.9% | 100% | 78.9% | 100% |

(R2L — remote-to-login attacks that look statistically similar to normal
traffic — is the known-hard category in the literature; see
[`docs/01-datasets.md`](docs/01-datasets.md).)

## Results (CICIDS2017)

Fit/scored on a stratified 150,000-row subsample of the full 2.83M-row
dataset (500K rows didn't finish fitting in a reasonable time — see
[`benchmark/results/cicids2017.json`](benchmark/results/cicids2017.json)'s
`sampling_note`). ~19.7% attack ratio, much lower and more realistic than
NSL-KDD's ~57%.

| Threshold | Precision | Recall | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|
| **0.5** (as shipped in production) | 0.319 | 0.011 | 0.021 | 0.700 | 0.407 |
| **0.190** (best-F1 on test set) | 0.526 | 0.455 | 0.488 | — | — |

Weaker separation than NSL-KDD (ROC-AUC 0.70 vs. 0.88) and a wide spread by
attack type at the tuned threshold — DoS 69%, DDoS 62%, but Botnet, Brute
Force, and PortScan recall near zero. Per-model breakdown shows LOF is
actually *hurting* the ensemble here (ROC-AUC 0.44, worse than random) while
HBOS (0.70) and IForest (0.69) carry it — a genuine "does the ensemble add
value" finding the aggregate score alone would hide. Published LOF-only
baselines on this dataset report precision/recall/F1 around 0.91/0.83/0.87
([Xu & Liu 2025](benchmark/results/cicids2017.json)), well above what this
run achieves — a real gap, reported rather than smoothed over.

## Live dashboard

Deploy configs exist ([`render.yaml`](benchmark/dashboard_backend/render.yaml)
for the API, [`vercel.json`](benchmark/dashboard_frontend/vercel.json) for the
frontend) but nothing is hosted publicly yet. Run it locally — see
[Quickstart](#quickstart) below or the full walkthrough in
[`docs/06-setup.md`](docs/06-setup.md).

## Architecture

```
                              ┌─────────────────────────┐
                              │   NSL-KDD / CICIDS2017   │
                              │   (labeled, public IDS   │
                              │    datasets)             │
                              └────────────┬─────────────┘
                                           │
                              benchmark/src/datasets/*.py
                                           │
                                           ▼
                          benchmark/src/ensemble.py
                   (IForest + LOF + HBOS — extracted verbatim
                    from backend/detection.py, parity-tested)
                                           │
                              benchmark/src/eval_harness.py
                        (precision/recall/F1/ROC-AUC/PR-AUC,
                         per-category recall, baseline comparison)
                                           │
                                           ▼
                         benchmark/results/{dataset}.json
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
              dashboard_backend (FastAPI)              static results panel
              /api/results, /api/replay (SSE)                  │
                        │                                      │
                        └──────────────┬───────────────────────┘
                                       ▼
                       dashboard_frontend (React + Vite)
                    live confusion matrix, precision/recall/F1
                       converging in real time as rows replay
```

`backend/` and `frontend/` are the original hackathon repos, vendored
read-only for reference and as the source of the ensemble logic being
benchmarked — untouched, and excluded from this repo's git history (see
[`docs/06-setup.md`](docs/06-setup.md) if you want to clone them yourself).
All new work lives in `benchmark/`.

## Repo layout

```
act-aware-benchmark/
├── README.md                 <- you are here
├── CONTRIBUTING.md           <- docs-stay-in-sync rule
├── docs/                     <- design docs: goals, datasets, methodology, setup
│   ├── 00-overview.md
│   ├── 01-datasets.md
│   ├── 02-ensemble-adaptation.md
│   ├── 03-eval-harness.md
│   ├── 04-dashboard.md
│   ├── 05-portfolio-integration.md
│   └── 06-setup.md
├── benchmark/                <- all new work
│   ├── src/
│   │   ├── datasets/          <- NSL-KDD / CICIDS2017 adapters
│   │   ├── ensemble.py        <- extracted, parity-tested detection logic
│   │   ├── eval_harness.py    <- metrics computation
│   │   └── replay_export.py   <- pre-scores rows for the live dashboard
│   ├── tests/                 <- parity test vs. the original hackathon logic
│   ├── data/                  <- raw datasets (gitignored) + SOURCE.md provenance
│   ├── results/                <- benchmark output JSON (committed, small)
│   ├── run_benchmarks.py      <- one command, runs everything above
│   ├── dashboard_backend/     <- FastAPI: serves results + paced SSE replay
│   └── dashboard_frontend/    <- React + Vite: live dashboard UI
├── backend/                   <- reference only, not tracked here (see above)
└── frontend/                  <- reference only, not tracked here (see above)
```

## Quickstart

```bash
git clone <this-repo-url> act-aware-benchmark && cd act-aware-benchmark

cd benchmark
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest tests/                      # parity + unit tests
python run_benchmarks.py           # regenerates results/*.json (needs data — see docs/06-setup.md)

cd dashboard_backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000 &

cd ../dashboard_frontend && npm install && npm run dev
```

Full step-by-step, including where to get the datasets and how to deploy:
[`docs/06-setup.md`](docs/06-setup.md).

## Tech stack

| Area | Stack |
|---|---|
| Detection ensemble | Python, PyOD (Isolation Forest, LOF, HBOS), scikit-learn, pandas, NumPy |
| Eval harness | pytest, custom metrics engine (precision/recall/F1/ROC-AUC/PR-AUC, per-category breakdown) |
| Dashboard API | FastAPI, Server-Sent Events, rate limiting, CORS-locked |
| Dashboard UI | React 19, TypeScript, Vite, Tailwind, Recharts |
| Original platform (reference) | FastAPI, Elasticsearch, tsfresh, NetworkX, LangGraph + Ollama (local LLM) |

## Documentation

| Doc | Covers |
|---|---|
| [00-overview.md](docs/00-overview.md) | Why this project exists, design principles, phase plan |
| [01-datasets.md](docs/01-datasets.md) | NSL-KDD & CICIDS2017 — format, labels, known difficulties |
| [02-ensemble-adaptation.md](docs/02-ensemble-adaptation.md) | Exactly what was extracted from the original detection code, and why |
| [03-eval-harness.md](docs/03-eval-harness.md) | Metrics, fit/score methodology, baseline comparison approach |
| [04-dashboard.md](docs/04-dashboard.md) | Live-replay design, "real-time" framing, public-endpoint guardrails |
| [05-portfolio-integration.md](docs/05-portfolio-integration.md) | How results feed back into the portfolio case study |
| [06-setup.md](docs/06-setup.md) | Full local setup, running the benchmark, deploying |

## Status

- ✅ NSL-KDD: benchmarked end-to-end, results committed
- ✅ CICIDS2017: benchmarked (stratified subsample), results committed
- 🚧 Live dashboard: built and runnable locally, not yet deployed publicly
- ⬜ Portfolio integration: pending the dashboard deploy above

## Contributing / keeping this repo honest

See [CONTRIBUTING.md](CONTRIBUTING.md) — the short version: if you change
what the code does, update the doc that describes it in the same change.

## Author

**Vedika Utturwar**
_(This benchmark and dashboard — the original Act Aware hackathon platform in
`backend/`/`frontend/` was a team effort, credited in
[`backend/README.md`](backend/README.md).)_

- GitHub: `<add-your-github-url>`
- LinkedIn: `<add-your-linkedin-url>`
- Portfolio: `<add-your-portfolio-url>`
- Email: `<add-your-email>`

## License

[MIT](LICENSE) — this is a portfolio project; use it as a reference freely.
