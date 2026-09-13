"""
Reusable core of Act Aware's Layer 6 detection ensemble
(backend/detection.py::run_ensemble_detection), extracted for per-record
scoring on labeled IDS datasets instead of per-user behavioral windows.

Kept identical to the original: model choice (IForest/LOF/HBOS), hyperparameters
(contamination, iforest random_state=42), min-max score normalization, and
simple averaging into one ensemble score. Deliberately not ported: severity
bucketing, top-feature attribution, and the DetectionOutput schema — those are
live-SOC-dashboard UI concerns, not part of what a precision/recall benchmark
measures. See docs/02-ensemble-adaptation.md.
"""

from dataclasses import dataclass

import numpy as np
from pyod.models.hbos import HBOS
from pyod.models.iforest import IForest
from pyod.models.lof import LOF


def _normalize(scores: np.ndarray) -> np.ndarray:
    mn, mx = scores.min(), scores.max()
    if mx == mn:
        return np.zeros_like(scores)
    return (scores - mn) / (mx - mn)


@dataclass
class EnsembleResult:
    ensemble_score: np.ndarray
    iforest_score: np.ndarray
    lof_score: np.ndarray
    hbos_score: np.ndarray
    iforest_raw: np.ndarray
    lof_raw: np.ndarray
    hbos_raw: np.ndarray

    def label(self, threshold: float = 0.5) -> np.ndarray:
        return (self.ensemble_score >= threshold).astype(int)


def fit_ensemble(X_train: np.ndarray, contamination: float = 0.15):
    """Fit IForest+LOF+HBOS on X_train. Mirrors the model construction in
    backend/detection.py::run_ensemble_detection exactly (same classes, same
    contamination knob, same iforest random_state)."""
    iforest = IForest(contamination=contamination, random_state=42)
    lof = LOF(contamination=contamination)
    hbos = HBOS(contamination=contamination)

    iforest.fit(X_train)
    lof.fit(X_train)
    hbos.fit(X_train)

    return iforest, lof, hbos


def _build(models, iforest_raw, lof_raw, hbos_raw) -> EnsembleResult:
    iforest_score = _normalize(iforest_raw)
    lof_score = _normalize(lof_raw)
    hbos_score = _normalize(hbos_raw)
    ensemble_score = (iforest_score + lof_score + hbos_score) / 3.0
    return EnsembleResult(
        ensemble_score=ensemble_score,
        iforest_score=iforest_score,
        lof_score=lof_score,
        hbos_score=hbos_score,
        iforest_raw=iforest_raw,
        lof_raw=lof_raw,
        hbos_raw=hbos_raw,
    )


def score_train(models) -> EnsembleResult:
    """Score the data the models were just fit on, using each model's cached
    decision_scores_ (computed once during .fit()). This is what
    backend/detection.py::run_ensemble_detection uses, and it is NOT
    numerically identical to calling decision_function() again on the same
    data afterwards — sklearn's LOF in particular scores training points
    (via _decision_function during fit, excluding self-neighbors) differently
    from a later novelty-style decision_function() query. Use this path
    whenever "scoring" means "the same batch just fitted", to stay byte-for-byte
    consistent with production."""
    iforest, lof, hbos = models
    return _build(models, iforest.decision_scores_, lof.decision_scores_, hbos.decision_scores_)


def score(models, X: np.ndarray) -> EnsembleResult:
    """Score new data X with already-fitted (iforest, lof, hbos) models via
    decision_function(). Use this for a genuine train/test split (the eval
    harness's fit-on-train, score-on-test path — see docs/03-eval-harness.md);
    for scoring the exact same batch that was just fit on, use score_train()
    instead to match production's cached decision_scores_ values."""
    iforest, lof, hbos = models
    return _build(models, iforest.decision_function(X), lof.decision_function(X), hbos.decision_function(X))


def run_ensemble(X: np.ndarray, contamination: float = 0.15, threshold: float = 0.5) -> EnsembleResult:
    """Fit-and-score-on-the-same-set, matching how backend/detection.py's
    run_ensemble_detection actually runs in production (no separate offline
    training phase there). Used for reproducing/validating parity with the
    original; the eval harness itself uses fit_ensemble()+score() on separate
    train/test splits — see docs/03-eval-harness.md's fit/score section."""
    models = fit_ensemble(X, contamination=contamination)
    return score_train(models)
