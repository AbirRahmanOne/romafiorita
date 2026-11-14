import Image from "next/image";
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Breadcrumbs } from "@/components/storefront/Breadcrumbs";
import { DeliveryChecker } from "@/components/storefront/DeliveryChecker";
import { AddToCartButton } from "@/components/storefront/AddToCartButton";
import { Badge } from "@/components/ui/badge";
import { JsonLd } from "@/components/JsonLd";
import { formatPrice } from "@/lib/utils";
import { occasionLabel } from "@/lib/occasions";
import { productImage } from "@/lib/images";
import { getProduct, productDescription, productName } from "@/lib/api";
import type { Locale } from "@/i18n/routing";

const SITE = "https://romafiorita.com";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}): Promise<Metadata> {
  const { locale, slug } = await params;
  const product = await getProduct(slug);
  if (!product) return {};
  const l = locale as Locale;
  return {
    title: productName(product, l),
    description: productDescription(product, l),
    alternates: { canonical: `/${locale}/bouquets/${slug}` },
  };
}

export default async function ProductPage({
  params,
}: {
  params: Promise<{ locale: string; slug: string }>;
}) {
  const { locale, slug } = await params;
  setRequestLocale(locale);
  const product = await getProduct(slug);
  if (!product) notFound();

  const t = await getTranslations();
  const l = locale as Locale;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: productName(product, l),
    description: productDescription(product, l),
    offers: {
      "@type": "Offer",
      price: (product.base_price_cents / 100).toFixed(2),
      priceCurrency: "EUR",
      availability: "https://schema.org/InStock",
      url: `${SITE}/${locale}/bouquets/${slug}`,
    },
  };

  return (
    <div className="mx-auto max-w-[1320px] px-4 py-10 sm:px-8">
      <JsonLd data={jsonLd} />
      <Breadcrumbs
        items={[
          { href: "/", label: t("catalog.home") },
          { href: "/bouquets", label: t("catalog.bouquetsTitle") },
          { href: `/bouquets/${slug}`, label: productName(product, l) },
        ]}
      />

      <div className="grid gap-10 lg:grid-cols-2">
        <div className="rf-plate relative aspect-[4/5] overflow-hidden">
          <Image
            src={productImage(product.slug)}
            alt={productName(product, l)}
            fill
            sizes="(max-width: 1024px) 100vw, 50vw"
            className="object-cover"
            priority
          />
        </div>

        <div>
          <Badge>{occasionLabel(product.occasion, l)}</Badge>
          <h1 className="mt-3 font-[family-name:var(--font-cormorant)] text-5xl font-semibold text-rf-ink">
            {productName(product, l)}
          </h1>
          <p className="mt-3 text-2xl font-medium text-rf-primary-strong">
            {formatPrice(product.base_price_cents, l)}
          </p>

          <div className="mt-6">
            <h2 className="text-xs font-semibold uppercase tracking-[0.14em] text-rf-ink-muted">
              {t("productDetail.descriptionTitle")}
            </h2>
            <p className="mt-2 text-rf-ink-muted">
              {productDescription(product, l)}
            </p>
          </div>

          <div className="mt-6">
            <AddToCartButton
              size="lg"
              className="w-full sm:w-auto"
              item={{
                slug: product.slug,
                name: productName(product, l),
                priceCents: product.base_price_cents,
                image: productImage(product.slug),
              }}
            />
          </div>

          <div className="mt-8">
            <DeliveryChecker />
          </div>
        </div>
      </div>
    </div>
  );
}
