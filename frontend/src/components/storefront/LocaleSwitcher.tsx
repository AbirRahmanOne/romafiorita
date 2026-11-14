"use client";

import { useLocale, useTranslations } from "next-intl";
import { usePathname, useRouter } from "@/i18n/navigation";
import { routing } from "@/i18n/routing";
import { cn } from "@/lib/utils";

export function LocaleSwitcher() {
  const t = useTranslations("localeSwitcher");
  const active = useLocale();
  const pathname = usePathname();
  const router = useRouter();

  return (
    <div
      className="inline-flex items-center rounded-full border border-rf-border p-0.5"
      role="group"
      aria-label={t("label")}
    >
      {routing.locales.map((locale) => (
        <button
          key={locale}
          onClick={() => router.replace(pathname, { locale })}
          aria-current={locale === active ? "true" : undefined}
          className={cn(
            "min-h-9 min-w-9 rounded-full px-3 text-sm font-medium transition-colors",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rf-primary",
            locale === active
              ? "bg-rf-primary text-white"
              : "text-rf-ink-muted hover:text-rf-ink",
          )}
        >
          {t(locale)}
        </button>
      ))}
    </div>
  );
}
