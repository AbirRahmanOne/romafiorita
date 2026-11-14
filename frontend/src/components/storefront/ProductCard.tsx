import Image from "next/image";
import { useLocale, useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AddToCartButton } from "./AddToCartButton";
import { formatPrice } from "@/lib/utils";
import { occasionLabel } from "@/lib/occasions";
import { productImage } from "@/lib/images";
import { productDescription, productName, type Product } from "@/lib/api";
import type { Locale } from "@/i18n/routing";

export function ProductCard({ product }: { product: Product }) {
  const locale = useLocale() as Locale;
  const t = useTranslations("product");
  const name = productName(product, locale);
  const image = productImage(product.slug);

  return (
    <Card className="group overflow-hidden">
      <Link href={`/bouquets/${product.slug}`} className="block">
        <div className="rf-plate relative aspect-[4/5] overflow-hidden">
          <Image
            src={image}
            alt={name}
            fill
            sizes="(max-width: 640px) 100vw, 33vw"
            className="object-cover"
          />
        </div>
      </Link>
      <div className="space-y-2 p-4">
        <Badge>{occasionLabel(product.occasion, locale)}</Badge>
        <h3 className="font-[family-name:var(--font-cormorant)] text-2xl font-semibold text-rf-ink">
          <Link href={`/bouquets/${product.slug}`}>{name}</Link>
        </h3>
        <p className="line-clamp-2 text-sm text-rf-ink-muted">
          {productDescription(product, locale)}
        </p>
        <div className="flex items-center justify-between pt-2">
          <span className="font-medium text-rf-ink">
            {t("from", {
              price: formatPrice(product.base_price_cents, locale),
            })}
          </span>
          <AddToCartButton
            item={{
              slug: product.slug,
              name,
              priceCents: product.base_price_cents,
              image,
            }}
          />
        </div>
      </div>
    </Card>
  );
}
