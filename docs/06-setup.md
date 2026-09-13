# Setup & Running Locally

This doc covers the parts of the repo you actually need to run the benchmark
and the dashboard. `backend/` and `frontend/` (see below) are reference-only
and **not required** for any of this.

## Prerequisites

- Python 3.11+ (developed against 3.13)
- Node.js 20+ and either `npm` or `bun` (the dashboard frontend has a
  `bun.lock`; `npm` works too since there's also a `package.json`)

## 1. Clone and get the datasets

```bash
git clone <this-repo-url> act-aware-benchmark
cd act-aware-benchmark
```

Raw dataset files are **not** committed (NSL-KDD is ~20MB, CICIDS2017 is
~850MB — both gitignored). Download them per the source links recorded in:

- [`benchmark/data/nsl_kdd/raw/SOURCE.md`](../benchmark/data/nsl_kdd/raw/SOURCE.md)
- [`benchmark/data/cicids2017/raw/SOURCE.md`](../benchmark/data/cicids2017/raw/SOURCE.md)

and place the files at `benchmark/data/nsl_kdd/raw/` (`KDDTrain+.txt`,
`KDDTest+.txt`) and `benchmark/data/cicids2017/raw/` (the per-day CSVs), matching
the filenames already referenced in `benchmark/src/datasets/`.

## 2. Benchmark / eval harness (Python)

```bash
cd benchmark
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the parity + unit tests:

```bash
pytest tests/
```

Run the full benchmark (loads both datasets, fits the ensemble, writes
`benchmark/results/{dataset}.json`, exports replay rows for the dashboard):

```bash
python run_benchmarks.py
```

This is the only command that regenerates `results/*.json` and
`dashboard_backend/data/*.json` — run it after touching anything in
`benchmark/src/` (dataset adapters, ensemble logic, or the eval harness).
`results/*.json` for both datasets is already committed, so you don't need
to re-run this just to inspect the numbers — only to reproduce or update
them.

## 3. Dashboard backend (FastAPI)

Serves the precomputed results and paces the live-replay SSE stream. It never
runs inference on request — see [04-dashboard.md](04-dashboard.md).

```bash
cd benchmark/dashboard_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ALLOWED_ORIGINS=http://localhost:5173 uvicorn app.main:app --reload --port 8000
```

Check it's up: `curl http://localhost:8000/api/health`.

Requires `benchmark/results/{dataset}.json` and
`benchmark/dashboard_backend/data/{dataset}.json` to already exist — i.e. run
step 2's `run_benchmarks.py` at least once first.

## 4. Dashboard frontend (React + Vite)

```bash
cd benchmark/dashboard_frontend
npm install       # or: bun install
npm run dev       # or: bun run dev
```

The dev server defaults to `http://localhost:5173` and expects the dashboard
backend reachable at `http://localhost:8000` by default. If you're running
the backend elsewhere, copy `.env.example` to `.env` and set `VITE_API_BASE`.

```bash
npm run build     # production build -> dist/
npm run lint
```

## 5. Deploying

Deploy configs already exist in the repo:

- `benchmark/dashboard_backend/render.yaml` — Render web service
  (`uvicorn app.main:app`), with `ALLOWED_ORIGINS` set as an env var.
- `benchmark/dashboard_frontend/vercel.json` — Vercel static build
  (`npm run build`, `dist/`, SPA rewrite).

Neither is deployed yet as of this writing — see the repo's `README.md` for
current status. When you do deploy, update `ALLOWED_ORIGINS` on the backend
to the real frontend origin, and the frontend's API base URL to the real
backend origin (no hardcoded IPs — see the caveat in
[04-dashboard.md](04-dashboard.md)).

## 6. Reference-only: `backend/` and `frontend/`

These are the original hackathon repos (Act Aware's live SIEM-SOAR platform),
kept read-only for reference — see [00-overview.md](00-overview.md). They're
excluded from this repo's git history and `.gitignore`d; clone them
separately if you want to browse the original code:

```bash
git clone https://github.com/Vedika-u/hack_o_hire.git backend
git clone https://github.com/Vedika-u/aware-security-hub.git frontend
```

Running them requires a live Elasticsearch cluster and an Ollama instance
(local LLM) — copy `backend/.env.example` to `backend/.env` and point it at
your own instances. **Do not reuse the values that used to be in this file**
— they pointed at a real hackathon-demo Elasticsearch/Ollama host and have
been redacted; if you have access to that original repo's git history,
rotate those credentials rather than trusting them.
