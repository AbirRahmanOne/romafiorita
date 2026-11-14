import { use } from "react";
import type { Metadata } from "next";
import { useTranslations } from "next-intl";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { buttonClasses } from "@/components/ui/button";
import { TrustStrip } from "@/components/storefront/TrustStrip";
import { ProductCard } from "@/components/storefront/ProductCard";
import { sampleProducts } from "@/lib/sample-products";
import { routing } from "@/i18n/routing";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "home" });
  return {
    title: t("metaTitle"),
    description: t("metaDescription"),
    alternates: {
      canonical: `/${locale}`,
      languages: {
        ...Object.fromEntries(routing.locales.map((l) => [l, `/${l}`])),
        "x-default": `/${routing.defaultLocale}`,
      },
    },
  };
}

export default function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations("home");

  return (
    <>
      <section className="mx-auto max-w-6xl px-4 py-16 sm:py-24">
        <div className="max-w-2xl">
          <h1 className="font-[family-name:var(--font-cormorant)] text-4xl font-bold leading-tight text-rf-ink sm:text-5xl">
            {t("heroTitle")}
          </h1>
          <p className="mt-5 text-lg text-rf-ink-muted">{t("heroSubtitle")}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/bouquets" className={buttonClasses({ size: "lg" })}>
              {t("shopNow")}
            </Link>
            <Link
              href="/occasions"
              className={buttonClasses({ size: "lg", variant: "outline" })}
            >
              {t("seeOccasions")}
            </Link>
          </div>
        </div>
      </section>

      <TrustStrip />

      <section className="mx-auto max-w-6xl px-4 py-16">
        <h2 className="mb-8 font-[family-name:var(--font-cormorant)] text-3xl font-semibold text-rf-ink">
          {t("featuredTitle")}
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {sampleProducts.map((product) => (
            <ProductCard key={product.slug} product={product} />
          ))}
        </div>
      </section>
    </>
  );
}
