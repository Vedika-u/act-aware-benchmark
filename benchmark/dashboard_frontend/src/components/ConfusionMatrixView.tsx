import { Card, CardTitle } from "./ui/card";

export function ConfusionMatrixView({
  tn,
  fp,
  fn,
  tp,
  title = "Confusion Matrix",
}: {
  tn: number;
  fp: number;
  fn: number;
  tp: number;
  title?: string;
}) {
  const cellClass = "flex flex-col items-center justify-center rounded-md py-4 font-mono";
  return (
    <Card>
      <CardTitle className="mb-3">{title}</CardTitle>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div className={`${cellClass} bg-success/10 text-success`}>
          <span className="text-2xl font-semibold">{tn.toLocaleString()}</span>
          <span className="text-xs text-muted-foreground mt-1">True Negative</span>
        </div>
        <div className={`${cellClass} bg-warning/10 text-warning`}>
          <span className="text-2xl font-semibold">{fp.toLocaleString()}</span>
          <span className="text-xs text-muted-foreground mt-1">False Positive</span>
        </div>
        <div className={`${cellClass} bg-critical/10 text-critical`}>
          <span className="text-2xl font-semibold">{fn.toLocaleString()}</span>
          <span className="text-xs text-muted-foreground mt-1">False Negative</span>
        </div>
        <div className={`${cellClass} bg-accent/10 text-accent`}>
          <span className="text-2xl font-semibold">{tp.toLocaleString()}</span>
          <span className="text-xs text-muted-foreground mt-1">True Positive</span>
        </div>
      </div>
    </Card>
  );
}
