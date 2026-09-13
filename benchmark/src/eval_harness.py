"""Evaluation harness — turns ensemble scores + dataset ground truth into
precision/recall/F1/ROC-AUC/PR-AUC, per-attack-category recall, and a
baseline comparison table. See docs/03-eval-harness.md.

Fit/score split: fit on X_train, score X_test (docs/03-eval-harness.md's
"option 1") — standard supervised-style evaluation, matches what the
official NSL-KDD test split (unseen attack types) is designed to measure.
This differs from how backend/detection.py's run_ensemble_detection scores
production data (fit+score on the same live window, since there's no
separate offline training phase there) — see docs/00-overview.md's framing
caveat.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    confusion_matrix,
    precision_recall_curve,
    average_precision_score,
    roc_auc_score,
)

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ensemble import fit_ensemble, score  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


def _metrics_at_threshold(y_true, ensemble_score, threshold):
    y_pred = (ensemble_score >= threshold).astype(int)
    tp = int(np.sum((y_pred == 1) & (y_true == 1)))
    fp = int(np.sum((y_pred == 1) & (y_true == 0)))
    fn = int(np.sum((y_pred == 0) & (y_true == 1)))
    tn = int(np.sum((y_pred == 0) & (y_true == 0)))
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "confusion_matrix": [[tn, fp], [fn, tp]],
    }


def _best_f1_threshold(y_true, ensemble_score):
    precisions, recalls, thresholds = precision_recall_curve(y_true, ensemble_score)
    # precision_recall_curve returns len(thresholds) == len(precisions) - 1
    f1s = np.zeros_like(thresholds)
    for i, (p, r) in enumerate(zip(precisions[:-1], recalls[:-1])):
        f1s[i] = 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    if len(thresholds) == 0:
        return 0.5
    best_idx = int(np.argmax(f1s))
    return float(thresholds[best_idx])


def _recall_by_category(y_test_category, ensemble_score, threshold):
    y_pred = (ensemble_score >= threshold).astype(int)
    out = {}
    for cat in sorted(set(y_test_category.tolist())):
        if cat == "normal":
            continue
        mask = y_test_category == cat
        n = int(mask.sum())
        recalled = int(np.sum(y_pred[mask] == 1))
        out[cat] = {
            "recall": round(recalled / n, 4) if n > 0 else None,
            "n_samples": n,
        }
    return out


def _per_model_metrics(y_true, model_score, name):
    auc = float(roc_auc_score(y_true, model_score)) if len(np.unique(y_true)) > 1 else None
    pr_auc = float(average_precision_score(y_true, model_score))
    return {"model": name, "roc_auc": round(auc, 4) if auc is not None else None, "pr_auc": round(pr_auc, 4)}


def evaluate_one_contamination(X_train, X_test, y_test_binary, y_test_category, contamination, threshold_default=0.5):
    models = fit_ensemble(X_train, contamination=contamination)
    result = score(models, X_test)

    roc_auc = float(roc_auc_score(y_test_binary, result.ensemble_score))
    pr_auc = float(average_precision_score(y_test_binary, result.ensemble_score))

    best_thresh = _best_f1_threshold(y_test_binary, result.ensemble_score)

    return {
        "contamination_used": contamination,
        "threshold_default": threshold_default,
        "threshold_best_f1": round(best_thresh, 4),
        "metrics_at_default_threshold": _metrics_at_threshold(y_test_binary, result.ensemble_score, threshold_default),
        "metrics_at_best_f1_threshold": _metrics_at_threshold(y_test_binary, result.ensemble_score, best_thresh),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "recall_by_category": _recall_by_category(y_test_category, result.ensemble_score, threshold_default),
        "recall_by_category_best_f1": _recall_by_category(y_test_category, result.ensemble_score, best_thresh),
        "per_model_scores": {
            "iforest": _per_model_metrics(y_test_binary, result.iforest_score, "iforest"),
            "lof": _per_model_metrics(y_test_binary, result.lof_score, "lof"),
            "hbos": _per_model_metrics(y_test_binary, result.hbos_score, "hbos"),
        },
    }


def evaluate_dataset(dataset_name, data, baseline_comparison=None, extra_contamination=None):
    """data: dict with X_train, X_test, y_test_binary, y_test_category
    (as returned by src/datasets/{nsl_kdd,cicids2017}.py's load()).

    Runs the ensemble at contamination=0.15 (matches what Act Aware ships in
    production, backend/detection.py) and, if extra_contamination is given, a
    second run matched to the dataset's real attack ratio — see
    docs/02-ensemble-adaptation.md's contamination caveat. Both are reported,
    labeled distinctly, rather than only the flattering one.
    """
    X_train, X_test = data["X_train"], data["X_test"]
    y_test_binary, y_test_category = data["y_test_binary"], data["y_test_category"]

    runs = [evaluate_one_contamination(X_train, X_test, y_test_binary, y_test_category, contamination=0.15)]
    if extra_contamination is not None and abs(extra_contamination - 0.15) > 1e-9:
        runs.append(
            evaluate_one_contamination(
                X_train, X_test, y_test_binary, y_test_category, contamination=extra_contamination
            )
        )

    results = {
        "dataset": dataset_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "train_attack_ratio": data.get("train_attack_ratio"),
        "test_attack_ratio": data.get("test_attack_ratio"),
        "n_train": int(X_train.shape[0]),
        "n_test": int(X_test.shape[0]),
        "n_features": int(X_train.shape[1]),
        "runs": runs,
        "baseline_comparison": baseline_comparison or [],
    }
    return results


def write_results(dataset_name, results):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / f"{dataset_name}.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=lambda o: None)
    return out_path
