"use client";

import { Fragment } from "react";
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
    <span
      className="mr-2 text-[13px] tracking-[0.08em]"
      role="group"
      aria-label={t("label")}
    >
      {routing.locales.map((locale, i) => (
        <Fragment key={locale}>
          {i > 0 && <span className="text-rf-ink-muted"> / </span>}
          <button
            onClick={() => router.replace(pathname, { locale })}
            aria-current={locale === active ? "true" : undefined}
            className={cn(
              "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rf-primary",
              locale === active
                ? "text-rf-ink underline underline-offset-4"
                : "text-rf-ink-muted hover:text-rf-ink",
            )}
          >
            {t(locale)}
          </button>
        </Fragment>
      ))}
    </span>
  );
}
