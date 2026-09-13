import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("glass-card p-5", className)} {...props} />;
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return <h3 className={cn("text-sm font-medium text-muted-foreground tracking-wide uppercase", className)} {...props} />;
}

export function CardValue({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("text-3xl font-semibold font-mono", className)} {...props} />;
}
