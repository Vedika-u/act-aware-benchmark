"""FastAPI backend for the Act Aware benchmark live-replay dashboard.
See docs/04-dashboard.md. Thin wrapper: serves precomputed results (Phase 3)
and paced replay of precomputed, pre-scored rows — never runs live PyOD
inference on request, and never accepts user-submitted data for scoring.
"""

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .rate_limit import RateLimitMiddleware
from .replay import router as replay_router
from .store import store

ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

app = FastAPI(title="Act Aware Benchmark Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)

app.include_router(replay_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "datasets": store.available_datasets()}


@app.get("/api/datasets")
def list_datasets():
    out = []
    for name in store.available_datasets():
        results = store.get_results(name)
        default_run = results["runs"][0]
        out.append(
            {
                "dataset": name,
                "n_test": results["n_test"],
                "roc_auc": default_run["roc_auc"],
                "pr_auc": default_run["pr_auc"],
                "f1_best": default_run["metrics_at_best_f1_threshold"]["f1"],
            }
        )
    return out


@app.get("/api/results/{dataset}")
def get_results(dataset: str):
    results = store.get_results(dataset)
    if results is None:
        raise HTTPException(status_code=404, detail=f"Unknown dataset '{dataset}'")
    return results
