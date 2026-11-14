import * as React from "react";
import { cn } from "@/lib/utils";

type Variant = "primary" | "secondary" | "ghost";
type Size = "md" | "lg";

// "Classical" buttons: outline-led, small radius, heading font.
const variants: Record<Variant, string> = {
  primary:
    "border border-rf-primary text-rf-primary hover:bg-rf-primary/10 active:bg-rf-primary/20 focus-visible:ring-rf-primary",
  secondary:
    "border border-rf-border text-rf-ink hover:bg-rf-ink/[0.06] active:bg-rf-ink/10 focus-visible:ring-rf-primary",
  ghost:
    "text-rf-primary hover:bg-rf-primary/10 focus-visible:ring-rf-primary",
};

const sizes: Record<Size, string> = {
  md: "h-10 px-5 text-sm",
  lg: "h-12 px-7 text-base",
};

export function buttonClasses({
  variant = "primary",
  size = "md",
  className,
}: { variant?: Variant; size?: Size; className?: string } = {}) {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-[4px] font-[family-name:var(--font-cormorant)] font-semibold tracking-wide transition-colors",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
    "disabled:pointer-events-none disabled:opacity-45",
    variants[variant],
    sizes[size],
    className,
  );
}

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={buttonClasses({ variant, size, className })}
      {...props}
    />
  ),
);
Button.displayName = "Button";
