import * as React from "react";
import { cn } from "@/lib/utils";

export function Card({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-[7px] border border-rf-border bg-rf-surface shadow-sm",
        className,
      )}
      {...props}
    />
  );
}
