import { useEffect, useState } from "react";
import { api, type BenchmarkResults } from "@/lib/api";
import { StaticResultsPanel } from "@/components/StaticResultsPanel";
import { LiveReplayPanel } from "@/components/LiveReplayPanel";

const DATASET_LABELS: Record<string, string> = {
  nsl_kdd: "NSL-KDD",
  cicids2017: "CICIDS2017",
};

function App() {
  const [datasets, setDatasets] = useState<string[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [results, setResults] = useState<BenchmarkResults | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .datasets()
      .then((d) => {
        const names = d.map((x) => x.dataset);
        setDatasets(names);
        setActive(names[0] ?? null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    if (!active) return;
    api.results(active).then(setResults).catch((e) => setError(String(e)));
  }, [active]);

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border">
        <div className="container py-6 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Act Aware — Detection Benchmark</h1>
            <p className="text-sm text-muted-foreground mt-1">
              The anomaly-detection ensemble (IForest + LOF + HBOS), validated against labeled public
              intrusion-detection datasets — not the full aggregation → detection → correlation → LLM pipeline.
            </p>
          </div>
        </div>
      </header>

      <main className="container py-8 space-y-8">
        {error && <div className="text-critical text-sm">{error}</div>}

        {datasets.length > 0 && (
          <div className="flex gap-2">
            {datasets.map((d) => (
              <button
                key={d}
                onClick={() => setActive(d)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  active === d
                    ? "bg-primary text-primary-foreground"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/70"
                }`}
              >
                {DATASET_LABELS[d] ?? d}
              </button>
            ))}
          </div>
        )}

        {results && (
          <div className="grid lg:grid-cols-2 gap-8">
            <StaticResultsPanel results={results} />
            {active && <LiveReplayPanel dataset={active} key={active} />}
          </div>
        )}

        {!results && !error && <div className="text-muted-foreground text-sm">Loading benchmark data…</div>}
      </main>
    </div>
  );
}

export default App;
