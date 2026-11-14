import { useTranslations } from "next-intl";
import { Bell, Search } from "lucide-react";

export function Topbar({ title }: { title: string }) {
  const t = useTranslations("admin");

  return (
    <header className="flex h-16 items-center justify-between gap-4 border-b border-ad-border bg-ad-surface px-4 md:px-6">
      <h1 className="text-lg font-semibold text-ad-ink">{title}</h1>
      <div className="flex items-center gap-2">
        <button
          aria-label={t("topbar.search")}
          className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-ad-ink-muted hover:bg-ad-primary-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ad-primary"
        >
          <Search className="h-5 w-5" aria-hidden />
        </button>
        <button
          aria-label={t("topbar.notifications")}
          className="flex min-h-11 min-w-11 items-center justify-center rounded-lg text-ad-ink-muted hover:bg-ad-primary-soft focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ad-primary"
        >
          <Bell className="h-5 w-5" aria-hidden />
        </button>
        <span className="flex h-9 w-9 items-center justify-center rounded-full bg-ad-primary text-sm font-medium text-white">
          RF
        </span>
      </div>
    </header>
  );
}
