"""CICIDS2017 dataset adapter. See docs/01-datasets.md.

Exposes load(), returning (X_train, X_test, y_test_binary, y_test_category)
so the eval harness (docs/03-eval-harness.md) is dataset-agnostic. No
official train/test split exists for this dataset, so we carve out a
stratified test split ourselves, preserving each attack category's relative
rarity (docs/01-datasets.md's preprocessing plan, step 6).
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "cicids2017" / "raw"

FILES = [
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
]

LABEL_COL = "Label"


def _category_for_label(label: str) -> str:
    if label == "BENIGN":
        return "normal"
    if label.startswith("DoS "):
        return "DoS"
    if label == "DDoS":
        return "DDoS"
    if label in ("FTP-Patator", "SSH-Patator"):
        return "Brute Force"
    if label.startswith("Web Attack"):
        return "Web Attack"
    if label == "Infiltration":
        return "Infiltration"
    if label == "Bot":
        return "Botnet"
    if label == "PortScan":
        return "PortScan"
    if label == "Heartbleed":
        return "Heartbleed"
    raise KeyError(f"Unmapped CICIDS2017 label {label!r} — add it to _category_for_label in src/datasets/cicids2017.py")


def _load_raw(data_dir: Path) -> pd.DataFrame:
    frames = []
    for fname in FILES:
        path = data_dir / fname
        if not path.exists():
            raise FileNotFoundError(f"Missing {path}. See data/cicids2017/raw/SOURCE.md.")
        df = pd.read_csv(path, low_memory=False)
        df.columns = [c.strip() for c in df.columns]
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def load(data_dir: Path = DATA_DIR, sample_size: int = None, test_size: float = 0.2, random_state: int = 42):
    df = _load_raw(data_dir)

    df[LABEL_COL] = df[LABEL_COL].apply(
        lambda s: "Web Attack" if isinstance(s, str) and s.startswith("Web Attack") else s
    )

    feature_cols = [c for c in df.columns if c != LABEL_COL]
    df[feature_cols] = df[feature_cols].apply(pd.to_numeric, errors="coerce")

    # Known issue: Flow Bytes/s and Flow Packets/s contain inf/NaN in the
    # released CSVs (docs/01-datasets.md's known difficulty). Replace with NaN
    # then drop any row with a NaN feature.
    df[feature_cols] = df[feature_cols].replace([np.inf, -np.inf], np.nan)
    df = df.dropna(subset=feature_cols)

    df["label_category"] = df[LABEL_COL].map(_category_for_label)

    if sample_size is not None and sample_size < len(df):
        df, _ = train_test_split(
            df, train_size=sample_size, stratify=df["label_category"], random_state=random_state
        )

    y_binary = (df["label_category"] != "normal").astype(int).values
    y_category = df["label_category"].values

    X_all = df[feature_cols].values.astype(float)

    variances = X_all.var(axis=0)
    keep_idx = np.where(variances > 0)[0]
    X_all = X_all[:, keep_idx]
    kept_feature_names = [feature_cols[i] for i in keep_idx]

    X_train, X_test, y_train_bin, y_test_binary, y_train_cat, y_test_category = train_test_split(
        X_all, y_binary, y_category, test_size=test_size, stratify=y_category, random_state=random_state
    )

    scaler = StandardScaler().fit(X_train)
    X_train = scaler.transform(X_train)
    X_test = scaler.transform(X_test)

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_test_binary": y_test_binary,
        "y_test_category": y_test_category,
        "feature_names": kept_feature_names,
        "train_attack_ratio": float(y_train_bin.mean()),
        "test_attack_ratio": float(y_test_binary.mean()),
    }


if __name__ == "__main__":
    d = load(sample_size=150_000)
    print("X_train", d["X_train"].shape)
    print("X_test", d["X_test"].shape)
    print("train attack ratio", round(d["train_attack_ratio"], 4))
    print("test attack ratio", round(d["test_attack_ratio"], 4))
    cats, counts = np.unique(d["y_test_category"], return_counts=True)
    print("test category counts", dict(zip(cats.tolist(), counts.tolist())))
