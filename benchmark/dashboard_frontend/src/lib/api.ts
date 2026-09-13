export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export interface RunMetrics {
  precision: number;
  recall: number;
  f1: number;
  confusion_matrix: number[][];
}

export interface CategoryRecall {
  recall: number | null;
  n_samples: number;
}

export interface BenchmarkRun {
  contamination_used: number;
  threshold_default: number;
  threshold_best_f1: number;
  metrics_at_default_threshold: RunMetrics;
  metrics_at_best_f1_threshold: RunMetrics;
  roc_auc: number;
  pr_auc: number;
  recall_by_category: Record<string, CategoryRecall>;
  recall_by_category_best_f1: Record<string, CategoryRecall>;
  per_model_scores: Record<string, { model: string; roc_auc: number | null; pr_auc: number }>;
}

export interface BaselineEntry {
  source: string;
  metric: string;
  value: number;
  caveat?: string;
}

export interface BenchmarkResults {
  dataset: string;
  generated_at: string;
  train_attack_ratio: number;
  test_attack_ratio: number;
  n_train: number;
  n_test: number;
  n_features: number;
  runs: BenchmarkRun[];
  baseline_comparison: BaselineEntry[];
  sampling_note?: string;
}

export interface DatasetSummary {
  dataset: string;
  n_test: number;
  roc_auc: number;
  pr_auc: number;
  f1_best: number;
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json();
}

export const api = {
  datasets: () => getJSON<DatasetSummary[]>("/api/datasets"),
  results: (dataset: string) => getJSON<BenchmarkResults>(`/api/results/${dataset}`),
  createReplaySession: async (dataset: string) => {
    const res = await fetch(`${API_BASE}/api/replay/sessions?dataset=${encodeURIComponent(dataset)}`, {
      method: "POST",
    });
    if (!res.ok) throw new Error(`create session -> ${res.status}`);
    return res.json() as Promise<{ session_id: string; dataset: string; n_rows: number }>;
  },
  replayStreamUrl: (sessionId: string, intervalMs: number) =>
    `${API_BASE}/api/replay/sessions/${sessionId}/stream?interval_ms=${intervalMs}`,
};
