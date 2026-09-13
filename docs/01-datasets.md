# Datasets

## NSL-KDD

- **What it is**: a cleaned-up revision of the 1999 KDD Cup dataset — removes duplicate
  records that biased the original toward frequent attack types, so it is the more
  commonly cited baseline for anomaly-based IDS papers today.
- **Format**: two CSVs (`KDDTrain+.txt`, `KDDTest+.txt`), 41 features per connection
  record (duration, protocol_type, service, flag, byte counts, login/host statistics,
  etc.) plus a label column and a difficulty score.
- **Labels**: each row is `normal` or one of ~39 specific attack names, which roll up
  into four attack categories: **DoS**, **Probe**, **R2L** (remote-to-local), **U2R**
  (user-to-root).
- **Why it's useful here**: the official `KDDTest+` split intentionally includes attack
  types absent from the training set — this is a genuine test of generalization, not
  just held-out i.i.d. rows, and is exactly the kind of thing that makes a reported
  number defensible rather than cherry-picked.
- **Known difficulty**: R2L and U2R categories have very few samples and are known in
  the literature to be hard for anomaly-based (unsupervised) detectors specifically,
  since they often look statistically similar to normal traffic. Expect — and report —
  lower recall on these categories rather than tuning thresholds until they disappear.
- **Source**: the canonical files are mirrored in several public GitHub repos and on
  the University of New Brunswick's NSL-KDD page; pick one canonical source and record
  its exact URL/commit in `benchmark/data/nsl_kdd/SOURCE.md` when downloaded, so the
  benchmark is reproducible.

## CICIDS2017

- **What it is**: a 2017 Canadian Institute for Cybersecurity dataset capturing five
  days of realistic network traffic with a mix of benign activity and modern attacks
  (Brute Force, DoS/DDoS, Web Attacks, Infiltration, Botnet, Port Scan, Heartbleed).
- **Format**: released both as raw PCAPs and as pre-extracted flow-level CSVs (one file
  per day/attack scenario) via CICFlowMeter — ~80 flow features (duration, packet
  counts, byte counts, flag counts, inter-arrival times, etc.) plus a label column. Use
  the pre-extracted CSVs — re-deriving flow features from PCAPs is unnecessary extra
  work for this benchmark.
- **Why it's useful here**: much larger and more "modern" than NSL-KDD, and widely used
  in recent IDS papers, so results here are comparable to a large body of published
  baselines.
- **Known difficulty**: heavy class imbalance (benign traffic dominates), some known
  label-noise issues documented in later re-analyses of the dataset, and a handful of
  features that are near-duplicates or constant — worth a quick sanity pass (drop
  zero-variance columns, check for `NaN`/`Infinity` values which are known to appear in
  the released CSVs) before feeding data into the ensemble.
- **Size note**: full CICIDS2017 flow CSVs are several GB combined — plan for
  chunked/streaming loading rather than reading everything into memory at once, and
  consider benchmarking on a stratified subsample first to iterate quickly before
  running the full set.

## Preprocessing plan (both datasets)

1. Load native CSV/TXT into a DataFrame; keep the original label column separate from
   engineered features.
2. Map each dataset's fine-grained label to: `label_binary` (normal/attack) and
   `label_category` (attack family — DoS/Probe/R2L/U2R for NSL-KDD; DoS/DDoS/Brute
   Force/Web Attack/Infiltration/Botnet/PortScan/Heartbleed for CICIDS2017).
3. Encode categorical features (`protocol_type`, `service`, `flag` for NSL-KDD) —
   one-hot or ordinal, consistent with what `IForest`/`LOF`/`HBOS` expect (numeric
   input only).
4. Drop identifier-like or zero-variance columns.
5. Scale/normalize features — PyOD models are sensitive to feature scale; use the same
   normalization approach for both datasets so the harness code is shared.
6. Keep the official train/test split for NSL-KDD; for CICIDS2017 (no official split),
   carve out a stratified test set that preserves the relative rarity of each attack
   category.

Each dataset gets its own adapter module (`benchmark/src/datasets/nsl_kdd.py`,
`benchmark/src/datasets/cicids2017.py`) exposing a common interface — e.g. a function
returning `(X_train, X_test, y_test_binary, y_test_category)` — so the eval harness in
[03-eval-harness.md](03-eval-harness.md) is dataset-agnostic.

## Status

Not yet downloaded. Next action: confirm source URLs and download into
`benchmark/data/{nsl_kdd,cicids2017}/raw/`.
