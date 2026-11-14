import { Inbox } from "lucide-react";

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-ad-border bg-ad-surface py-20 text-center">
      <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-ad-primary-soft text-ad-primary">
        <Inbox className="h-6 w-6" aria-hidden />
      </span>
      <p className="text-sm text-ad-ink-muted">{message}</p>
    </div>
  );
}
