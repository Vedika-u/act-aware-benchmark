"""Loads precomputed benchmark results + replay rows once at startup.

Guardrail (docs/04-dashboard.md): the replay endpoint only ever serves
pre-loaded, pre-scored rows from these files — it never accepts
user-submitted data for scoring, which removes the injection/abuse-via-
malicious-input surface entirely.
"""

import json
from pathlib import Path
from typing import Dict

BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = BENCHMARK_ROOT / "results"
REPLAY_DIR = Path(__file__).resolve().parents[1] / "data"

KNOWN_DATASETS = ("nsl_kdd", "cicids2017")


class Store:
    def __init__(self):
        self.results: Dict[str, dict] = {}
        self.replay: Dict[str, dict] = {}
        self._load()

    def _load(self):
        for name in KNOWN_DATASETS:
            results_path = RESULTS_DIR / f"{name}.json"
            replay_path = REPLAY_DIR / f"{name}.json"
            if results_path.exists():
                with open(results_path) as f:
                    self.results[name] = json.load(f)
            if replay_path.exists():
                with open(replay_path) as f:
                    self.replay[name] = json.load(f)

    def available_datasets(self):
        return sorted(set(self.results) & set(self.replay))

    def get_results(self, dataset: str):
        return self.results.get(dataset)

    def get_replay_rows(self, dataset: str):
        replay = self.replay.get(dataset)
        return replay["rows"] if replay else None

    def get_replay_threshold(self, dataset: str):
        replay = self.replay.get(dataset)
        return replay["threshold"] if replay else 0.5


store = Store()
