import * as React from "react";
import { cn } from "@/lib/utils";

export function Badge({
  className,
  ...props
}: React.HTMLAttributes<HTMLSpanElement>) {
  return (
    <span
      className={cn(
        "inline-flex items-center text-xs font-medium uppercase tracking-[0.14em] text-rf-primary-strong",
        className,
      )}
      {...props}
    />
  );
}
