import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { Breadcrumbs } from "@/components/storefront/Breadcrumbs";
import { buttonClasses } from "@/components/ui/button";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "plants" });
  return {
    title: t("title"),
    description: t("description"),
    alternates: { canonical: `/${locale}/plants` },
  };
}

export default async function PlantsPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("plants");
  const c = await getTranslations("catalog");

  return (
    <div className="mx-auto max-w-[1320px] px-4 py-10 sm:px-8">
      <Breadcrumbs
        items={[
          { href: "/", label: c("home") },
          { href: "/plants", label: t("title") },
        ]}
      />
      <h1 className="font-[family-name:var(--font-cormorant)] text-5xl font-semibold text-rf-ink">
        {t("title")}
      </h1>
      <p className="mt-4 max-w-2xl text-lg text-rf-ink-muted">
        {t("description")}
      </p>
      <Link href="/bouquets" className={buttonClasses({ className: "mt-6" })}>
        {t("cta")}
      </Link>
    </div>
  );
}
