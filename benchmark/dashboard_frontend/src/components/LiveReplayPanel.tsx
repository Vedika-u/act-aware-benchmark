import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Card, CardTitle } from "./ui/card";
import { ConfusionMatrixView } from "./ConfusionMatrixView";
import { StatCard } from "./StatCard";

interface ReplayRow {
  id: number;
  _key?: number; // client-assigned, for React list keys (row `id` is a dataset row index, not stream-unique)
  ground_truth_label: "normal" | "attack";
  ground_truth_category: string;
  ensemble_score: number;
  predicted_label: "normal" | "anomaly";
  correct: boolean;
  top_features: Record<string, number>;
}

interface RunningStats {
  confusion_matrix: { tp: number; fp: number; tn: number; fn: number };
  precision: number;
  recall: number;
  f1: number;
  n_seen: number;
  n_total: number;
}

const FEED_MAX = 12;

export function LiveReplayPanel({ dataset }: { dataset: string }) {
  const [feed, setFeed] = useState<ReplayRow[]>([]);
  const [running, setRunning] = useState<RunningStats | null>(null);
  const [status, setStatus] = useState<"idle" | "streaming" | "done">("idle");
  const eventSourceRef = useRef<EventSource | null>(null);
  const seqRef = useRef(0);
  const rowKeyRef = useRef(0);

  const start = async () => {
    eventSourceRef.current?.close();
    eventSourceRef.current = null;
    setFeed([]);
    setRunning(null);
    setStatus("streaming");

    // Guards against React StrictMode's dev-only double-invoke of this
    // effect: without this token check, the first (soon-cleaned-up)
    // invocation's async createReplaySession() can resolve after the
    // second invocation has already started its own session, leaving two
    // concurrent EventSources both writing into `feed`.
    const mySeq = ++seqRef.current;

    const { session_id } = await api.createReplaySession(dataset);
    if (mySeq !== seqRef.current) return; // superseded — abandon silently

    const es = new EventSource(api.replayStreamUrl(session_id, 250));
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      if (payload.done) {
        setStatus("done");
        es.close();
        return;
      }
      const row = { ...(payload.row as ReplayRow), _key: rowKeyRef.current++ };
      setFeed((prev) => [row, ...prev].slice(0, FEED_MAX));
      setRunning(payload.running as RunningStats);
    };
    es.onerror = () => {
      es.close();
      setStatus("done");
    };
  };

  useEffect(() => {
    start();
    return () => {
      seqRef.current++; // invalidate this invocation, even if still awaiting createReplaySession
      eventSourceRef.current?.close();
      eventSourceRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataset]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Live replay</h2>
          <p className="text-sm text-muted-foreground max-w-2xl">
            Streaming pre-scored test rows through the actual extracted ensemble output — nothing here is
            fabricated or re-generated per visitor. What's staged is the pacing: every row was scored offline by
            the real IForest+LOF+HBOS ensemble; this view just reveals results at a readable rate so you can watch
            precision/recall/F1 converge toward the precomputed benchmark numbers.
          </p>
        </div>
        <button
          onClick={start}
          disabled={status === "streaming"}
          className="shrink-0 px-4 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium disabled:opacity-50"
        >
          {status === "streaming" ? "Streaming…" : "Restart replay"}
        </button>
      </div>

      {running && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Rows seen" value={`${running.n_seen} / ${running.n_total}`} />
            <StatCard label="Running precision" value={running.precision.toFixed(3)} />
            <StatCard label="Running recall" value={running.recall.toFixed(3)} />
            <StatCard label="Running F1" value={running.f1.toFixed(3)} tone="success" />
          </div>
          <ConfusionMatrixView
            tn={running.confusion_matrix.tn}
            fp={running.confusion_matrix.fp}
            fn={running.confusion_matrix.fn}
            tp={running.confusion_matrix.tp}
            title="Running confusion matrix"
          />
        </>
      )}

      <Card>
        <CardTitle className="mb-3">Live feed</CardTitle>
        <div className="space-y-1.5 font-mono text-xs">
          {feed.length === 0 && <div className="text-muted-foreground">Waiting for rows…</div>}
          {feed.map((row) => (
            <div
              key={row._key ?? row.id}
              className={`flex items-center justify-between gap-3 px-3 py-2 rounded-md ${
                row.correct ? "bg-success/5" : "bg-critical/10"
              }`}
            >
              <span className="w-24 truncate">{row.ground_truth_category}</span>
              <span className="opacity-60">truth={row.ground_truth_label}</span>
              <span className="opacity-60">pred={row.predicted_label}</span>
              <span>score={row.ensemble_score.toFixed(3)}</span>
              <span className={row.correct ? "text-success" : "text-critical"}>
                {row.correct ? "✓" : "✗"}
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
