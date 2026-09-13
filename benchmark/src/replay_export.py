"""Exports a bounded, pre-scored row-by-row replay feed for the live-replay
dashboard (docs/04-dashboard.md). Every row's ensemble_score was computed by
the actual extracted ensemble logic on genuine dataset rows — replay pacing
is a UI concern (see docs/04-dashboard.md's "real-time" clarification), not
live per-row inference; this file is written once, offline, and the
dashboard backend only ever reads it back.
"""

import json
from pathlib import Path

import numpy as np

REPLAY_DIR = Path(__file__).resolve().parents[1] / "dashboard_backend" / "data"


def _feature_summary(x_row: np.ndarray, feature_names, top_n=5):
    idx = np.argsort(-np.abs(x_row))[:top_n]
    return {feature_names[i]: round(float(x_row[i]), 4) for i in idx}


def export_replay_rows(
    dataset_name: str,
    X_test: np.ndarray,
    y_test_binary: np.ndarray,
    y_test_category: np.ndarray,
    ensemble_result,
    feature_names,
    threshold: float = 0.5,
    max_rows: int = 1000,
    random_state: int = 42,
):
    rng = np.random.RandomState(random_state)
    n = X_test.shape[0]

    if n > max_rows:
        # Stratified-ish sample: sample proportionally within each category so
        # rare categories still appear, then shuffle order for replay.
        idx_parts = []
        categories = np.unique(y_test_category)
        for cat in categories:
            cat_idx = np.where(y_test_category == cat)[0]
            take = max(1, round(max_rows * len(cat_idx) / n))
            take = min(take, len(cat_idx))
            idx_parts.append(rng.choice(cat_idx, size=take, replace=False))
        idx = np.concatenate(idx_parts)
        rng.shuffle(idx)
        idx = idx[:max_rows]
    else:
        idx = np.arange(n)
        rng.shuffle(idx)

    rows = []
    for i in idx:
        score = float(ensemble_result.ensemble_score[i])
        predicted = "anomaly" if score >= threshold else "normal"
        ground_truth = "attack" if y_test_binary[i] == 1 else "normal"
        rows.append(
            {
                "id": int(i),
                "ground_truth_label": ground_truth,
                "ground_truth_category": str(y_test_category[i]),
                "ensemble_score": round(score, 4),
                "predicted_label": predicted,
                "correct": (predicted == "anomaly") == (ground_truth == "attack"),
                "top_features": _feature_summary(X_test[i], feature_names),
            }
        )

    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPLAY_DIR / f"{dataset_name}.json"
    with open(out_path, "w") as f:
        json.dump({"dataset": dataset_name, "threshold": threshold, "rows": rows}, f, indent=2)
    return out_path
