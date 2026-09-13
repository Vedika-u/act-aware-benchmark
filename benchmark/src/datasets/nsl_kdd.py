"""NSL-KDD dataset adapter. See docs/01-datasets.md.

Exposes load(), returning (X_train, X_test, y_test_binary, y_test_category)
so the eval harness (docs/03-eval-harness.md) is dataset-agnostic. Uses the
official train/test split as downloaded — see data/nsl_kdd/raw/SOURCE.md.
"""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "nsl_kdd" / "raw"

COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root",
    "num_file_creations", "num_shells", "num_access_files", "num_outbound_cmds",
    "is_host_login", "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
    "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "label", "difficulty",
]

CATEGORICAL_COLS = ["protocol_type", "service", "flag"]

# Attack name -> attack category. Covers every attack label present in both
# KDDTrain+ and KDDTest+ (KDDTest+ includes attack types absent from training,
# by design — see docs/01-datasets.md).
ATTACK_CATEGORY = {
    # DoS
    "back": "DoS", "land": "DoS", "neptune": "DoS", "pod": "DoS",
    "smurf": "DoS", "teardrop": "DoS", "apache2": "DoS", "udpstorm": "DoS",
    "processtable": "DoS", "worm": "DoS", "mailbomb": "DoS",
    # Probe
    "satan": "Probe", "ipsweep": "Probe", "nmap": "Probe", "portsweep": "Probe",
    "mscan": "Probe", "saint": "Probe",
    # R2L
    "guess_passwd": "R2L", "ftp_write": "R2L", "imap": "R2L", "phf": "R2L",
    "multihop": "R2L", "warezmaster": "R2L", "warezclient": "R2L", "spy": "R2L",
    "xlock": "R2L", "xsnoop": "R2L", "snmpguess": "R2L", "snmpgetattack": "R2L",
    "httptunnel": "R2L", "sendmail": "R2L", "named": "R2L",
    # U2R
    "buffer_overflow": "U2R", "loadmodule": "U2R", "rootkit": "U2R",
    "perl": "U2R", "sqlattack": "U2R", "xterm": "U2R", "ps": "U2R",
}


def _load_raw(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, names=COLUMNS, header=None)
    return df


def _category_for_label(label: str) -> str:
    if label == "normal":
        return "normal"
    cat = ATTACK_CATEGORY.get(label)
    if cat is None:
        raise KeyError(
            f"Unmapped NSL-KDD attack label {label!r} — add it to ATTACK_CATEGORY "
            f"in src/datasets/nsl_kdd.py"
        )
    return cat


def _encode_features(train_df: pd.DataFrame, test_df: pd.DataFrame):
    """One-hot encode categorical columns, fit on train+test union of categories
    (both files are static/known in advance, so this isn't test-time leakage of
    labels — only of which categorical values exist, which is standard practice
    for this dataset since KDDTest+ deliberately contains unseen attack *labels*,
    not unseen protocol/service/flag *values*)."""
    train_feat = train_df.drop(columns=["label", "difficulty"])
    test_feat = test_df.drop(columns=["label", "difficulty"])

    combined = pd.concat([train_feat, test_feat], keys=["train", "test"])
    encoded = pd.get_dummies(combined, columns=CATEGORICAL_COLS)

    numeric_cols = [c for c in encoded.columns]
    encoded[numeric_cols] = encoded[numeric_cols].astype(float)

    train_enc = encoded.xs("train")
    test_enc = encoded.xs("test")

    # Drop zero-variance columns (computed on train only, applied to both)
    variances = train_enc.var(axis=0)
    keep_cols = variances[variances > 0].index.tolist()
    train_enc = train_enc[keep_cols]
    test_enc = test_enc[keep_cols]

    return train_enc.values, test_enc.values, keep_cols


def load(data_dir: Path = DATA_DIR):
    train_path = data_dir / "KDDTrain+.txt"
    test_path = data_dir / "KDDTest+.txt"
    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError(
            f"NSL-KDD files not found in {data_dir}. See data/nsl_kdd/raw/SOURCE.md."
        )

    train_df = _load_raw(train_path)
    test_df = _load_raw(test_path)

    y_test_binary = (test_df["label"] != "normal").astype(int).values
    y_test_category = test_df["label"].map(_category_for_label).values

    X_train, X_test, feature_names = _encode_features(train_df, test_df)

    return {
        "X_train": np.asarray(X_train, dtype=float),
        "X_test": np.asarray(X_test, dtype=float),
        "y_test_binary": y_test_binary,
        "y_test_category": y_test_category,
        "feature_names": feature_names,
        "train_attack_ratio": float((train_df["label"] != "normal").mean()),
        "test_attack_ratio": float(y_test_binary.mean()),
    }


if __name__ == "__main__":
    d = load()
    print("X_train", d["X_train"].shape)
    print("X_test", d["X_test"].shape)
    print("train attack ratio", round(d["train_attack_ratio"], 4))
    print("test attack ratio", round(d["test_attack_ratio"], 4))
    cats, counts = np.unique(d["y_test_category"], return_counts=True)
    print("test category counts", dict(zip(cats.tolist(), counts.tolist())))
