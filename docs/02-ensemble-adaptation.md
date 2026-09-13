# Ensemble Adaptation — Per-Record Scoring

## Source of truth

`backend/detection.py` — "Layer 6 — Anomaly Detection using PyOD Ensemble" (Act Aware's
production detection layer). Read in full while writing this doc; key functions:

- `aggregate_events(events, pipeline_id, window_minutes=15)` — groups raw log events by
  entity (user/host/ip) into 15-minute windows and computes 16 behavioral features
  (login failure ratio, event rate, unique IPs/hosts touched, file/db activity counts,
  after-hours/weekend flags, etc.). **Not reused** — this is specific to Act Aware's
  live log schema (`UniversalEvent`) and has no equivalent input in a labeled IDS
  dataset.
- `behaviors_to_dataframe(behaviors)` — flattens `AggregatedBehavior` objects into a
  feature `DataFrame`. **Not reused**, same reason.
- `run_ensemble_detection(behaviors, pipeline_id, contamination=0.15)` — **this is the
  part we extract.** Structurally:
  1. Build feature matrix `X` from the input DataFrame (currently via
     `behaviors_to_dataframe`).
  2. Fit `IForest`, `LOF`, `HBOS` (all from PyOD, `contamination=0.15`, `iforest`
     seeded with `random_state=42`) on `X`.
  3. Min-max normalize each model's `decision_scores_` to [0, 1].
  4. Average the three normalized scores into one `ensemble_score`.
  5. Threshold at 0.5 to produce a binary anomaly label, plus a severity bucket
     (critical/high/medium/low) from the score.

Steps 2-5 have no dependency on where `X` came from — they operate on any numeric
feature matrix. That's the reusable core.

## What changes for the benchmark

Extract steps 2-5 into a standalone function in `benchmark/src/ensemble.py`, e.g.:

```python
def run_ensemble(X: np.ndarray, contamination: float = 0.15, threshold: float = 0.5):
    """Fit IForest+LOF+HBOS on X, return per-row ensemble_score and binary label.
    Mirrors backend/detection.py::run_ensemble_detection, minus the
    behavioral-aggregation-specific input construction and Act Aware-specific
    output schema (DetectionOutput/severity/feature attribution) — those stay in
    the original for the live pipeline.
    """
```

Kept identical to the original: model choice, hyperparameters (`contamination=0.15`,
`iforest` `random_state=42`), score normalization method, ensemble averaging. This
matters for the benchmark's validity claim — we are testing *the same detection logic*
Act Aware runs in production, just fed a different (labeled, static) input instead of
live behavioral windows.

**Deliberately not ported**: the severity bucketing, top-feature attribution, and
`DetectionOutput` schema — those are UI/triage concerns for the live SOC dashboard, not
part of what a precision/recall benchmark measures.

## Threshold handling

The original hardcodes `threshold = 0.5`. For the benchmark, don't hardcode a single
threshold — sweep it to produce a precision-recall curve and report both:
- metrics at the original threshold (0.5), since that's what production actually runs
- best-F1 threshold on the test set, clearly labeled as such (not to be confused with
  "the number Act Aware runs in production")

Reporting only a tuned best-case threshold without also showing the as-shipped
threshold would be the kind of cherry-picking this whole effort is trying to avoid.

## Contamination parameter caveat

`contamination=0.15` (i.e., IForest/LOF/HBOS are told to expect ~15% of the training
data is anomalous) was presumably chosen for Act Aware's synthetic hackathon log
generator. NSL-KDD and CICIDS2017 have very different actual attack ratios (NSL-KDD
training set is roughly 47% attack; CICIDS2017 varies heavily by day/file, often much
lower). Document actual dataset attack ratios in [01-datasets.md](01-datasets.md)'s
per-dataset sections, and report results both with the original `0.15` (again, matching
what production ships) and with contamination matched to each dataset's real ratio —
labeled distinctly, same reasoning as the threshold point above.

## Status

Not yet extracted. Next action: copy `run_ensemble_detection`'s scoring logic (steps
2-5 above) into `benchmark/src/ensemble.py`, unit-test it against a small synthetic
matrix to confirm it reproduces the same scores as the original function given
identical input.
