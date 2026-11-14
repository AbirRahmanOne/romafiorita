import { use } from "react";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { Breadcrumbs } from "@/components/storefront/Breadcrumbs";
import { DeliveryChecker } from "@/components/storefront/DeliveryChecker";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { JsonLd } from "@/components/JsonLd";
import { formatPrice } from "@/lib/utils";
import {
  getProductBySlug,
  occasionLabel,
  sampleProducts,
} from "@/lib/sample-products";
import type { Locale } from "@/i18n/routing";

const SITE = "https://romafiorita.com";

export function generateStaticParams() {
  return sampleProducts.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale, slug } = await params;
  const product = getProductBySlug(slug);
  if (!product) return {};
  const l = locale as Locale;
  return {
    title: product.name[l],
    description: product.description[l],
    alternates: { canonical: `/${locale}/bouquets/${slug}` },
  };
}

export default function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = use(params);
  setRequestLocale(locale);
  const product = getProductBySlug(slug);
  if (!product) notFound();

  const t = useTranslations();
  const l = useLocale() as Locale;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: product.name[l],
    description: product.description[l],
    offers: {
      "@type": "Offer",
      price: (product.priceCents / 100).toFixed(2),
      priceCurrency: "EUR",
      availability: "https://schema.org/InStock",
      url: `${SITE}/${locale}/bouquets/${slug}`,
    },
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-10">
      <JsonLd data={jsonLd} />
      <Breadcrumbs
        items={[
          { href: "/", label: t("catalog.home") },
          { href: "/bouquets", label: t("catalog.bouquetsTitle") },
          { href: `/bouquets/${slug}`, label: product.name[l] },
        ]}
      />

      <div className="grid gap-10 lg:grid-cols-2">
        {/* ponytail: gradient placeholder until real R2 photography lands */}
        <div
          className="aspect-[4/5] rounded-2xl bg-gradient-to-br from-rf-primary-soft to-rf-blush"
          aria-hidden
        />

        <div>
          <Badge>{occasionLabel(product.occasion, l)}</Badge>
          <h1 className="mt-3 font-[family-name:var(--font-cormorant)] text-4xl font-bold text-rf-ink">
            {product.name[l]}
          </h1>
          <p className="mt-3 text-2xl font-medium text-rf-ink">
            {formatPrice(product.priceCents, l)}
          </p>

          <div className="mt-6">
            <h2 className="text-sm font-bold uppercase tracking-wide text-rf-ink-muted">
              {t("productDetail.descriptionTitle")}
            </h2>
            <p className="mt-2 text-rf-ink-muted">{product.description[l]}</p>
          </div>

          <div className="mt-6">
            <Button size="lg" className="w-full sm:w-auto">
              {t("product.add")}
            </Button>
          </div>

          <div className="mt-8">
            <DeliveryChecker />
          </div>
        </div>
      </div>
    </div>
  );
}
