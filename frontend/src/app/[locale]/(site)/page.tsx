import Image from "next/image";
import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Link } from "@/i18n/navigation";
import { buttonClasses } from "@/components/ui/button";
import { TrustStrip } from "@/components/storefront/TrustStrip";
import { ProductCard } from "@/components/storefront/ProductCard";
import { listProducts } from "@/lib/api";
import { HERO_IMAGE } from "@/lib/images";
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

export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("home");
  const { items: featured } = await listProducts({ limit: 3 });

  return (
    <>
      <section className="mx-auto max-w-[1320px] px-4 pt-10 sm:px-8 sm:pt-16">
        <div className="grid items-center gap-8 lg:grid-cols-2 lg:gap-16">
          <div className="flex flex-col gap-6">
            <span className="text-xs uppercase tracking-[0.14em] text-rf-primary-strong">
              {t("eyebrow")}
            </span>
            <h1 className="font-[family-name:var(--font-cormorant)] text-5xl font-normal leading-[0.98] tracking-tight text-rf-ink text-balance sm:text-6xl lg:text-7xl">
              {t("heroTitle")}
            </h1>
            <p className="max-w-lg text-lg leading-relaxed text-rf-ink-muted">
              {t("heroSubtitle")}
            </p>
            <div className="flex flex-wrap gap-3">
              <Link href="/bouquets" className={buttonClasses({ size: "lg" })}>
                {t("shopNow")}
              </Link>
              <Link
                href="/occasions"
                className={buttonClasses({ size: "lg", variant: "secondary" })}
              >
                {t("howItWorks")}
              </Link>
            </div>
            <div className="flex flex-wrap items-center gap-5 text-sm text-rf-ink-muted">
              <span className="text-rf-primary">{t("rating")}</span>
              <span>{t("reach")}</span>
            </div>
          </div>

          <figure className="m-0">
            <div className="rf-plate relative aspect-[11/10] w-full overflow-hidden">
              <Image
                src={HERO_IMAGE}
                alt={t("heroCaption")}
                fill
                sizes="(max-width: 1024px) 100vw, 50vw"
                className="object-cover"
                priority
              />
            </div>
            <figcaption className="mt-1 text-xs text-rf-ink-muted">
              {t("heroCaption")}
            </figcaption>
          </figure>
        </div>
      </section>

      <div className="mt-16">
        <TrustStrip />
      </div>

      <section className="mx-auto max-w-[1320px] px-4 py-16 sm:px-8">
        <h2 className="mb-8 font-[family-name:var(--font-cormorant)] text-4xl font-semibold text-rf-ink">
          {t("featuredTitle")}
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {featured.map((product) => (
            <ProductCard key={product.slug} product={product} />
          ))}
        </div>
      </section>
    </>
  );
}
