import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";

export function Footer() {
  const t = useTranslations("footer");

  const infoLinks = [
    { href: "/terms", label: t("terms") },
    { href: "/privacy", label: t("privacy") },
    { href: "/cookies", label: t("cookies") },
    { href: "/contact", label: t("contact") },
  ];

  return (
    <footer className="mt-20 border-t border-rf-border bg-rf-blush/50">
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-12 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <p className="font-[family-name:var(--font-cormorant)] text-3xl text-rf-ink">
            Roma <em className="not-italic text-rf-primary">Fiorita</em>
          </p>
          <p className="mt-2 max-w-xs text-sm text-rf-ink-muted">{t("tagline")}</p>
        </div>

        <nav aria-label={t("links")}>
          <h2 className="text-sm font-bold text-rf-ink">{t("links")}</h2>
          <ul className="mt-3 space-y-2">
            {infoLinks.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className="text-sm text-rf-ink-muted hover:text-rf-primary"
                >
                  {l.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <div className="text-sm text-rf-ink-muted">
          <h2 className="text-sm font-bold text-rf-ink">{t("legalName")}</h2>
          <address className="mt-3 space-y-1 not-italic">
            <p>{t("address")}</p>
            <p>{t("vat")}</p>
            <p>{t("pec")}</p>
          </address>
          <p className="mt-4 text-xs" aria-label={t("payments")}>
            Visa · Mastercard · Apple Pay · Google Pay · PayPal
          </p>
        </div>
      </div>
      <div className="border-t border-rf-border py-4 text-center text-xs text-rf-ink-muted">
        © {new Date().getFullYear()} Roma Fiorita. {t("rights")}
      </div>
    </footer>
  );
}
