import { use } from "react";
import type { Metadata } from "next";
import { useLocale, useTranslations } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { Breadcrumbs } from "@/components/storefront/Breadcrumbs";
import { ProductCard } from "@/components/storefront/ProductCard";
import { cn } from "@/lib/utils";
import { occasions, getProductsByOccasion } from "@/lib/sample-products";
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

export default function BouquetsPage({
  params,
  searchParams,
}: {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ occasion?: string }>;
}) {
  const { locale } = use(params);
  const { occasion } = use(searchParams);
  setRequestLocale(locale);
  const t = useTranslations("catalog");
  const activeLocale = useLocale() as Locale;

  const products = getProductsByOccasion(occasion);

  const chip = (label: string, href: string, active: boolean) => (
    <Link
      key={href}
      href={href}
      aria-current={active ? "true" : undefined}
      className={cn(
        "rounded-full border px-4 py-1.5 text-sm transition-colors",
        active
          ? "border-rf-primary bg-rf-primary text-white"
          : "border-rf-border text-rf-ink-muted hover:border-rf-primary hover:text-rf-primary",
      )}
    >
      {label}
    </Link>
  );

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <Breadcrumbs
        items={[
          { href: "/", label: t("home") },
          { href: "/bouquets", label: t("bouquetsTitle") },
        ]}
      />
      <h1 className="font-[family-name:var(--font-cormorant)] text-4xl font-bold text-rf-ink">
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
