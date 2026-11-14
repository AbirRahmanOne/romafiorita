import { useTranslations } from "next-intl";
import { Search, User } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { LocaleSwitcher } from "./LocaleSwitcher";
import { CartLink } from "./CartLink";

export function Header() {
  const t = useTranslations("nav");
  const a = useTranslations("announcement");

  const links = [
    { href: "/occasions", label: t("occasions") },
    { href: "/bouquets", label: t("bouquets") },
    { href: "/plants", label: t("plants") },
    { href: "/about", label: t("about") },
  ];

  return (
    <>
      {/* Announcement bar */}
      <div className="bg-rf-dark text-rf-surface">
        <div className="mx-auto flex max-w-[1320px] flex-wrap justify-between gap-3 px-4 py-2 text-xs tracking-[0.06em] sm:px-8">
          <span>{a("sameDay")}</span>
          <span className="text-rf-border">{a("national")}</span>
        </div>
      </div>

      <header className="sticky top-0 z-40 border-b border-rf-border bg-rf-bg">
        <div className="mx-auto flex max-w-[1320px] flex-wrap items-center gap-7 px-4 py-3.5 sm:px-8">
          <Link
            href="/"
            className="font-[family-name:var(--font-cormorant)] text-3xl leading-none tracking-wide text-rf-ink"
          >
            Roma <em className="not-italic text-rf-primary">Fiorita</em>
          </Link>

          <nav className="mr-auto hidden flex-wrap items-center gap-6 text-sm md:flex">
            {links.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="whitespace-nowrap text-rf-ink transition-colors hover:text-rf-primary-strong"
              >
                {l.label}
              </Link>
            ))}
          </nav>

          <div className="flex items-center gap-1">
            <LocaleSwitcher />
            <button
              aria-label={t("search")}
              className="flex h-9 w-9 items-center justify-center rounded-[4px] text-rf-ink hover:bg-rf-ink/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rf-primary"
            >
              <Search className="h-[18px] w-[18px]" aria-hidden />
            </button>
            <button
              aria-label={t("account")}
              className="flex h-9 w-9 items-center justify-center rounded-[4px] text-rf-ink hover:bg-rf-ink/[0.06] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rf-primary"
            >
              <User className="h-[18px] w-[18px]" aria-hidden />
            </button>
            <CartLink />
          </div>
        </div>
      </header>
    </>
  );
}
