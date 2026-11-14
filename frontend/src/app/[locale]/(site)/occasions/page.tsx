import { use } from "react";
import type { Metadata } from "next";
import { useLocale, useTranslations } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { Breadcrumbs } from "@/components/storefront/Breadcrumbs";
import { Card } from "@/components/ui/card";
import { occasions } from "@/lib/sample-products";
import type { Locale } from "@/i18n/routing";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "catalog" });
  return {
    title: t("occasionsTitle"),
    description: t("occasionsDescription"),
    alternates: { canonical: `/${locale}/occasions` },
  };
}

export default function OccasionsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations("catalog");
  const activeLocale = useLocale() as Locale;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <Breadcrumbs
        items={[
          { href: "/", label: t("home") },
          { href: "/occasions", label: t("occasionsTitle") },
        ]}
      />
      <h1 className="font-[family-name:var(--font-cormorant)] text-4xl font-bold text-rf-ink">
        {t("occasionsTitle")}
      </h1>
      <p className="mt-2 max-w-2xl text-rf-ink-muted">
        {t("occasionsDescription")}
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {occasions.map((o) => (
          <Link key={o.slug} href={`/bouquets?occasion=${o.slug}`}>
            <Card className="flex h-full flex-col justify-between p-6 transition-shadow hover:shadow-md">
              <h2 className="font-[family-name:var(--font-cormorant)] text-2xl font-semibold text-rf-ink">
                {o.label[activeLocale]}
              </h2>
              <span className="mt-4 text-sm font-medium text-rf-primary">
                {t("shopOccasion", { occasion: o.label[activeLocale] })} →
              </span>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
