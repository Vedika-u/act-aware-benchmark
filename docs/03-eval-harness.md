# Evaluation Harness

## Purpose

Turn ensemble scores (from [02-ensemble-adaptation.md](02-ensemble-adaptation.md)) and
dataset ground truth (from [01-datasets.md](01-datasets.md)) into the actual numbers:
precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix — overall and broken out per
attack category — plus a comparison against published baselines.

## Pipeline

```
dataset adapter → X_train, X_test, y_test_binary, y_test_category
                        │
                        ▼
              run_ensemble(X_train + X_test or fit-on-train/score-test — see below)
                        │
                        ▼
              ensemble_score per test row
                        │
          ┌─────────────┴─────────────┐
          ▼                           ▼
   threshold sweep              fixed threshold (0.5)
   → PR curve, ROC curve        → confusion matrix, precision/recall/F1
          │                           │
          └─────────────┬─────────────┘
                         ▼
          per-attack-category breakdown (recall per category is the
          interesting number — overall recall hides that R2L/U2R
          are much harder than DoS/Probe)
                         ▼
          results JSON written to benchmark/results/{dataset}.json
```

### Fit/score split — a real decision, not a detail

PyOD's `IForest`/`LOF`/`HBOS` are unsupervised: `.fit(X)` doesn't use labels. Two
legitimate options:

1. **Fit on training split, score test split** (`.fit(X_train)`, then
   `.decision_function(X_test)`) — standard supervised-style evaluation, avoids any
   leakage from test rows into model fitting, matches how a deployed detector would
   actually behave (trained once, scores new data).
2. **Fit and score on the same set** (as `run_ensemble_detection` does today — it fits
   and scores the same behavior batch, since production has no separate "training
   set," just whatever window of live events just arrived).

Use **option 1** for the benchmark — it's the methodologically correct way to report
generalization, and it's directly what the NSL-KDD official test split (with unseen
attack types) is designed to measure. Note in the results writeup that this differs
slightly from how production scores each live window (fit+score together, since there
is no separate offline training phase there) — another instance of the "benchmark
tests the ensemble, not a byte-for-byte replica of the live pipeline" caveat from
[00-overview.md](00-overview.md).

## Metrics to compute

- Precision, recall, F1 (binary: normal vs. attack) at threshold 0.5
- Same, at best-F1 threshold (both reported, labeled — see
  [02-ensemble-adaptation.md](02-ensemble-adaptation.md))
- ROC-AUC, PR-AUC (threshold-independent, summarize overall separability)
- Confusion matrix (binary)
- Recall per attack category (DoS/Probe/R2L/U2R for NSL-KDD; per-attack-type for
  CICIDS2017) — this is the most important table in the whole benchmark, since a single
  aggregate recall number can look good purely by nailing the easy, high-volume attack
  types (DoS) while missing rare, hard ones (U2R) almost entirely
- Per-model contribution: how much each of IForest/LOF/HBOS individually would score
  (not just the ensemble average) — useful diagnostic, shows whether the ensemble is
  actually adding value over any single detector

## Baseline comparison

Both NSL-KDD and CICIDS2017 have a large published-baseline literature. Pull 2-3
commonly cited numbers per dataset (e.g., published IForest-only or comparable
unsupervised-ensemble results, not just supervised deep-learning SOTA which isn't a
fair comparison to an unsupervised anomaly ensemble) into a small table in the results
writeup. This is what turns "we got 91% precision" into a defensible claim rather than
a number with no reference point — cite exact papers/sources when added.

## Output format

`benchmark/results/{dataset_name}.json`:
```json
{
  "dataset": "nsl_kdd",
  "generated_at": "...",
  "contamination_used": 0.15,
  "threshold_default": 0.5,
  "threshold_best_f1": 0.0,
  "metrics_at_default_threshold": { "precision": 0.0, "recall": 0.0, "f1": 0.0, "confusion_matrix": [[0,0],[0,0]] },
  "metrics_at_best_f1_threshold": { "...": "..." },
  "roc_auc": 0.0,
  "pr_auc": 0.0,
  "recall_by_category": { "DoS": 0.0, "Probe": 0.0, "R2L": 0.0, "U2R": 0.0 },
  "per_model_scores": { "iforest": {"...": "..."}, "lof": {"...": "..."}, "hbos": {"...": "..."} },
  "baseline_comparison": [ { "source": "...", "metric": "...", "value": 0.0 } ]
}
```

This JSON is the single artifact both the static dashboard view and the live-replay
dashboard's "precomputed" fallback consume — see
[04-dashboard.md](04-dashboard.md).

## Status

Not yet built. Depends on Phase 1 (datasets) and Phase 2 (ensemble extraction) landing
first.
