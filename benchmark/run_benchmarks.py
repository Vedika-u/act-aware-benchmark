"""Driver script for Phase 3 (docs/03-eval-harness.md): loads each dataset,
runs the extracted ensemble (docs/02-ensemble-adaptation.md), and writes
benchmark/results/{dataset}.json.

Baseline comparison numbers are pulled from published unsupervised-anomaly
papers evaluating the same model families (IForest/LOF) on the same
datasets — see each entry's "source" field for exact citation. Only
unsupervised-anomaly-ensemble baselines are used, not supervised deep
learning SOTA, per docs/03-eval-harness.md ("not a fair comparison to an
unsupervised anomaly ensemble").
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from datasets import nsl_kdd, cicids2017  # noqa: E402
from eval_harness import evaluate_dataset, write_results  # noqa: E402
from ensemble import fit_ensemble, score as score_ensemble  # noqa: E402
from replay_export import export_replay_rows  # noqa: E402

NSL_KDD_BASELINES = [
    {
        "source": "Rao & Mane (2021), 'Zero-shot learning approach to adaptive "
        "Cybersecurity using Explainable AI', arXiv:2106.14647",
        "metric": "precision (attack class, Isolation Forest only)",
        "value": 0.92,
        "caveat": "Evaluated on NSL-KDD training data itself (fit+score on the "
        "same set), not the KDDTest+ generalization split this benchmark uses "
        "— not directly comparable to this benchmark's test-set numbers, "
        "included as a rough sanity check only.",
    },
    {
        "source": "Rao & Mane (2021), 'Zero-shot learning approach to adaptive "
        "Cybersecurity using Explainable AI', arXiv:2106.14647",
        "metric": "recall (attack class, Isolation Forest only)",
        "value": 0.89,
        "caveat": "Same caveat as above.",
    },
    {
        "source": "Rao & Mane (2021), 'Zero-shot learning approach to adaptive "
        "Cybersecurity using Explainable AI', arXiv:2106.14647",
        "metric": "f1 (attack class, Isolation Forest only)",
        "value": 0.91,
        "caveat": "Same caveat as above.",
    },
]

CICIDS2017_BASELINES = [
    {
        "source": "Xu & Liu (2025), 'Robust Anomaly Detection in Network Traffic: "
        "Evaluating Machine Learning Models on CICIDS2017', arXiv:2506.19877, Table II",
        "metric": "precision (LOF, Overall Test Set, trained on benign traffic only)",
        "value": 0.9106,
    },
    {
        "source": "Xu & Liu (2025), arXiv:2506.19877, Table II",
        "metric": "recall (LOF, Overall Test Set)",
        "value": 0.8341,
    },
    {
        "source": "Xu & Liu (2025), arXiv:2506.19877, Table II",
        "metric": "f1 (LOF, Overall Test Set)",
        "value": 0.8706,
    },
    {
        "source": "Xu & Liu (2025), arXiv:2506.19877, Table III",
        "metric": "recall (LOF, Unknown-Attack-Only Test Set — generalization to novel attack types)",
        "value": 0.8370,
        "caveat": "Their 'unknown attack' split excludes 3 specific attack types from "
        "training; this benchmark's fit/test split (docs/03-eval-harness.md) does not "
        "hold out specific attack types, so treat as directionally comparable only.",
    },
]


def main():
    print("=" * 70)
    print("NSL-KDD")
    print("=" * 70)
    t0 = time.time()
    data = nsl_kdd.load()
    print(f"loaded in {time.time()-t0:.1f}s: X_train={data['X_train'].shape} X_test={data['X_test'].shape}")
    t0 = time.time()
    results = evaluate_dataset(
        "nsl_kdd", data, baseline_comparison=NSL_KDD_BASELINES, extra_contamination=data["train_attack_ratio"]
    )
    print(f"evaluated in {time.time()-t0:.1f}s")
    path = write_results("nsl_kdd", results)
    print(f"wrote {path}")

    t0 = time.time()
    models = fit_ensemble(data["X_train"], contamination=0.15)
    result = score_ensemble(models, data["X_test"])
    replay_path = export_replay_rows(
        "nsl_kdd", data["X_test"], data["y_test_binary"], data["y_test_category"], result, data["feature_names"]
    )
    print(f"exported replay rows in {time.time()-t0:.1f}s -> {replay_path}")

    print("=" * 70)
    print("CICIDS2017")
    print("=" * 70)
    sample_size = 150_000
    t0 = time.time()
    data = cicids2017.load(sample_size=sample_size)
    print(f"loaded in {time.time()-t0:.1f}s: X_train={data['X_train'].shape} X_test={data['X_test'].shape}")
    t0 = time.time()
    results = evaluate_dataset(
        "cicids2017", data, baseline_comparison=CICIDS2017_BASELINES, extra_contamination=data["train_attack_ratio"]
    )
    results["sampling_note"] = (
        f"Stratified subsample of {sample_size:,} rows out of the full 2,830,743-row "
        "CICIDS2017 dataset (see docs/01-datasets.md's size note). LOF's fit cost does "
        "not scale linearly with row count — an empirical timing check found fit+score "
        "on a 500,000-row subsample did not complete in a reasonable time (killed after "
        "~12 minutes with no result), while 150,000 rows completed end-to-end in under "
        "2 minutes, so 150,000 was chosen as a tractable, verified size rather than "
        "guessed. Sampling was stratified by attack category so relative rarity is "
        "preserved; extremely rare categories (Infiltration: 36 rows, Heartbleed: 11 "
        "rows in the FULL dataset) may end up with 0-few test-set samples purely from "
        "that rarity, independent of subsampling — see recall_by_category's n_samples "
        "for each run."
    )
    print(f"evaluated in {time.time()-t0:.1f}s")
    path = write_results("cicids2017", results)
    print(f"wrote {path}")

    t0 = time.time()
    models = fit_ensemble(data["X_train"], contamination=0.15)
    result = score_ensemble(models, data["X_test"])
    replay_path = export_replay_rows(
        "cicids2017", data["X_test"], data["y_test_binary"], data["y_test_category"], result, data["feature_names"]
    )
    print(f"exported replay rows in {time.time()-t0:.1f}s -> {replay_path}")


if __name__ == "__main__":
    main()
