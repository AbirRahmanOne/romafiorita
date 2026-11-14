import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { Breadcrumbs } from "@/components/storefront/Breadcrumbs";
import { ProductCard } from "@/components/storefront/ProductCard";
import { cn } from "@/lib/utils";
import { occasions } from "@/lib/occasions";
import { listProducts } from "@/lib/api";
import type { Locale } from "@/i18n/routing";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "catalog" });
  return {
    title: t("bouquetsTitle"),
    description: t("bouquetsDescription"),
    alternates: { canonical: `/${locale}/bouquets` },
  };
}

export default async function BouquetsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ occasion?: string }>;
}) {
  const { locale } = await params;
  const { occasion } = await searchParams;
  setRequestLocale(locale);
  const t = await getTranslations("catalog");
  const activeLocale = locale as Locale;

  const { items: products } = await listProducts({ occasion });

  const chip = (label: string, href: string, active: boolean) => (
    <Link
      key={href}
      href={href}
      aria-current={active ? "true" : undefined}
      className={cn(
        "rounded-[4px] border px-4 py-1.5 text-sm transition-colors",
        active
          ? "border-rf-primary bg-rf-primary/10 text-rf-primary-strong"
          : "border-rf-border text-rf-ink-muted hover:border-rf-primary hover:text-rf-primary",
      )}
    >
      {label}
    </Link>
  );

  return (
    <div className="mx-auto max-w-[1320px] px-4 py-10 sm:px-8">
      <Breadcrumbs
        items={[
          { href: "/", label: t("home") },
          { href: "/bouquets", label: t("bouquetsTitle") },
        ]}
      />
      <h1 className="font-[family-name:var(--font-cormorant)] text-5xl font-semibold text-rf-ink">
        {t("bouquetsTitle")}
      </h1>
      <p className="mt-2 max-w-2xl text-rf-ink-muted">
        {t("bouquetsDescription")}
      </p>

      <div
        className="mt-6 flex flex-wrap gap-2"
        role="group"
        aria-label={t("filterLabel")}
      >
        {chip(t("all"), "/bouquets", !occasion)}
        {occasions.map((o) =>
          chip(
            o.label[activeLocale],
            `/bouquets?occasion=${o.slug}`,
            occasion === o.slug,
          ),
        )}
      </div>

      {products.length === 0 ? (
        <p className="mt-12 text-rf-ink-muted">{t("empty")}</p>
      ) : (
        <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <ProductCard key={product.slug} product={product} />
          ))}
        </div>
      )}
    </div>
  );
}
