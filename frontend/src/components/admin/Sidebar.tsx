"use client";

import { useTranslations } from "next-intl";
import { Link, usePathname } from "@/i18n/navigation";
import { adminNav } from "./nav-items";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const t = useTranslations("admin");
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 flex-col bg-ad-sidebar text-white md:flex">
      <div className="px-6 py-5 text-lg font-semibold">{t("wordmark")}</div>
      <nav className="flex-1 space-y-1 px-3">
        {adminNav.map(({ href, key, icon: Icon }) => {
          const active =
            href === "/admin" ? pathname === "/admin" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex min-h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60",
                active
                  ? "bg-ad-primary text-white"
                  : "text-white/80 hover:bg-white/10 hover:text-white",
              )}
            >
              <Icon className="h-5 w-5" aria-hidden />
              {t(`nav.${key}`)}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
