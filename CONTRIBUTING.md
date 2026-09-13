# Contributing

This is a small, mostly-solo project, so the rules here are lightweight —
they exist to stop the docs from silently going stale, since the `docs/`
folder and root `README.md` are what make this repo readable to someone who
didn't build it.

## Rule: code changes update docs in the same change

If a change affects any of the following, update the matching doc **in the
same commit/PR**, not as a follow-up:

| If you change... | Update... |
|---|---|
| `benchmark/src/ensemble.py` (model choice, hyperparameters, scoring math) | [`docs/02-ensemble-adaptation.md`](docs/02-ensemble-adaptation.md) |
| `benchmark/src/eval_harness.py` (metrics computed, fit/score methodology) | [`docs/03-eval-harness.md`](docs/03-eval-harness.md) |
| dataset adapters in `benchmark/src/datasets/` | [`docs/01-datasets.md`](docs/01-datasets.md) |
| `benchmark/dashboard_backend/` or `benchmark/dashboard_frontend/` (API shape, replay behavior, guardrails) | [`docs/04-dashboard.md`](docs/04-dashboard.md) |
| setup/run steps, new env vars, new dependencies, deploy config | [`docs/06-setup.md`](docs/06-setup.md) |
| headline results in `benchmark/results/*.json`, project status, repo layout | root [`README.md`](README.md) (the "Results" and "Status" sections) |
| anything that changes what's true about the project at a glance (new phase done, new dataset benchmarked, dashboard actually deployed) | root [`README.md`](README.md) |

If you're not sure a change is "significant enough" to need a doc update:
if a stranger reading only the docs would now believe something false about
the code, it needs the update.

## Rule: don't report numbers that don't exist yet

Per [`docs/00-overview.md`](docs/00-overview.md)'s "honest framing" principle:
never add placeholder, estimated, or "should be around X" numbers to the
README or `docs/`. If a benchmark run hasn't completed, the status stays
`🚧 pending` until `benchmark/results/{dataset}.json` actually has the
number.

## Running the checks before committing

```bash
cd benchmark
pytest tests/                # parity test: ensemble.py must still match backend/detection.py's math
```

There's no separate lint/typecheck step for the Python side yet. For the
dashboard frontend: `cd benchmark/dashboard_frontend && npm run lint`.
