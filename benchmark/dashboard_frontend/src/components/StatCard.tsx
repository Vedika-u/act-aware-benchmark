import { Card, CardTitle, CardValue } from "./ui/card";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  tone = "default",
  sub,
}: {
  label: string;
  value: string;
  tone?: "default" | "success" | "warning" | "critical";
  sub?: string;
}) {
  const toneClass = {
    default: "text-foreground",
    success: "text-success",
    warning: "text-warning",
    critical: "text-critical",
  }[tone];

  return (
    <Card>
      <CardTitle>{label}</CardTitle>
      <CardValue className={cn(toneClass)}>{value}</CardValue>
      {sub && <div className="text-xs text-muted-foreground">{sub}</div>}
    </Card>
  );
}
