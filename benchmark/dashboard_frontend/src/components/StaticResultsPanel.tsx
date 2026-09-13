import type { BenchmarkResults } from "@/lib/api";
import { StatCard } from "./StatCard";
import { ConfusionMatrixView } from "./ConfusionMatrixView";
import { Card, CardTitle } from "./ui/card";

function pct(n: number) {
  return `${(n * 100).toFixed(1)}%`;
}

export function StaticResultsPanel({ results }: { results: BenchmarkResults }) {
  const run = results.runs[0];
  const cm = run.metrics_at_default_threshold.confusion_matrix;
  const [tn, fp] = cm[0];
  const [fn, tp] = cm[1];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Precomputed benchmark results</h2>
        <p className="text-sm text-muted-foreground">
          Full test set ({results.n_test.toLocaleString()} rows), ensemble fit on{" "}
          {results.n_train.toLocaleString()} training rows. Test-set attack ratio:{" "}
          {pct(results.test_attack_ratio)}.
        </p>
        {results.sampling_note && (
          <p className="text-xs text-muted-foreground mt-2 italic">{results.sampling_note}</p>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="ROC-AUC" value={run.roc_auc.toFixed(3)} />
        <StatCard label="PR-AUC" value={run.pr_auc.toFixed(3)} />
        <StatCard
          label="F1 @ threshold=0.5 (production)"
          value={run.metrics_at_default_threshold.f1.toFixed(3)}
          tone={run.metrics_at_default_threshold.f1 < 0.3 ? "critical" : "default"}
        />
        <StatCard label="F1 @ best-F1 threshold" value={run.metrics_at_best_f1_threshold.f1.toFixed(3)} tone="success" />
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <ConfusionMatrixView tn={tn} fp={fp} fn={fn} tp={tp} title={`Confusion Matrix (threshold=${run.threshold_default})`} />
        <Card>
          <CardTitle className="mb-3">Recall by attack category (threshold={run.threshold_default})</CardTitle>
          <div className="space-y-2">
            {Object.entries(run.recall_by_category).map(([cat, v]) => (
              <div key={cat} className="flex items-center justify-between text-sm">
                <span className="font-medium">{cat}</span>
                <span className="font-mono text-muted-foreground">
                  {v.recall === null ? "—" : pct(v.recall)} <span className="opacity-60">(n={v.n_samples})</span>
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      <Card>
        <CardTitle className="mb-3">Per-model contribution (ROC-AUC)</CardTitle>
        <div className="grid grid-cols-3 gap-4">
          {Object.values(run.per_model_scores).map((m) => (
            <div key={m.model} className="text-center">
              <div className="text-2xl font-mono font-semibold">{m.roc_auc?.toFixed(3) ?? "—"}</div>
              <div className="text-xs text-muted-foreground uppercase tracking-wide mt-1">{m.model}</div>
            </div>
          ))}
        </div>
      </Card>

      {results.baseline_comparison.length > 0 && (
        <Card>
          <CardTitle className="mb-3">Published baselines (context, not a controlled comparison)</CardTitle>
          <div className="space-y-3 text-sm">
            {results.baseline_comparison.map((b, i) => (
              <div key={i} className="border-b border-glass-border last:border-0 pb-2 last:pb-0">
                <div className="flex justify-between">
                  <span>{b.metric}</span>
                  <span className="font-mono">{b.value}</span>
                </div>
                <div className="text-xs text-muted-foreground mt-0.5">{b.source}</div>
                {b.caveat && <div className="text-xs text-warning/80 mt-0.5">{b.caveat}</div>}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
