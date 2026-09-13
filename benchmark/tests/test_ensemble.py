"""Parity test: benchmark/src/ensemble.py must reproduce the same scores as
backend/detection.py::run_ensemble_detection given identical input, since
steps 2-5 of the original were extracted verbatim (see docs/02-ensemble-adaptation.md)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ensemble import run_ensemble  # noqa: E402


def _reference_run_ensemble_detection(X: np.ndarray, contamination: float = 0.15):
    """Inlined copy of the scoring math in backend/detection.py::run_ensemble_detection
    (the part after behaviors_to_dataframe), for a direct side-by-side comparison
    without importing the original module's UniversalEvent/schema dependencies."""
    from pyod.models.hbos import HBOS
    from pyod.models.iforest import IForest
    from pyod.models.lof import LOF

    iforest = IForest(contamination=contamination, random_state=42)
    lof = LOF(contamination=contamination)
    hbos = HBOS(contamination=contamination)

    iforest.fit(X)
    lof.fit(X)
    hbos.fit(X)

    def normalize(scores):
        mn, mx = scores.min(), scores.max()
        if mx == mn:
            return np.zeros_like(scores)
        return (scores - mn) / (mx - mn)

    i_scores = normalize(iforest.decision_scores_)
    l_scores = normalize(lof.decision_scores_)
    h_scores = normalize(hbos.decision_scores_)
    return (i_scores + l_scores + h_scores) / 3.0


def test_matches_original_detection_logic():
    rng = np.random.RandomState(0)
    X_normal = rng.normal(0, 1, size=(80, 6))
    X_anom = rng.normal(6, 1, size=(10, 6))
    X = np.vstack([X_normal, X_anom])

    expected = _reference_run_ensemble_detection(X, contamination=0.15)
    result = run_ensemble(X, contamination=0.15)

    np.testing.assert_allclose(result.ensemble_score, expected, rtol=1e-10, atol=1e-12)


def test_label_thresholding():
    rng = np.random.RandomState(1)
    X = rng.normal(0, 1, size=(50, 4))
    result = run_ensemble(X)
    labels = result.label(threshold=0.5)
    assert set(np.unique(labels)).issubset({0, 1})
    assert labels.shape == (50,)


if __name__ == "__main__":
    test_matches_original_detection_logic()
    test_label_thresholding()
    print("All ensemble parity tests passed.")
