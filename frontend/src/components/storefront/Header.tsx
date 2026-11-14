import { useTranslations } from "next-intl";
import { ShoppingBag } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { LocaleSwitcher } from "./LocaleSwitcher";

export function Header() {
  const t = useTranslations("nav");

  const links = [
    { href: "/bouquets", label: t("bouquets") },
    { href: "/plants", label: t("plants") },
    { href: "/occasions", label: t("occasions") },
    { href: "/about", label: t("about") },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-rf-border bg-rf-bg/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-4">
        <Link
          href="/"
          className="font-[family-name:var(--font-cormorant)] text-2xl font-bold text-rf-ink"
        >
          Roma Fiorita
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-rf-ink-muted transition-colors hover:text-rf-primary"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <LocaleSwitcher />
          <Link
            href="/cart"
            aria-label={t("cart")}
            className="flex min-h-11 min-w-11 items-center justify-center rounded-full text-rf-ink hover:bg-rf-blush focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rf-primary"
          >
            <ShoppingBag className="h-5 w-5" aria-hidden />
          </Link>
        </div>
      </div>
    </header>
  );
}
