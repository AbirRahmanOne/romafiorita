import { useLocale, useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatPrice } from "@/lib/utils";
import type { Locale } from "@/i18n/routing";
import { occasionLabel, type SampleProduct } from "@/lib/sample-products";

export function ProductCard({ product }: { product: SampleProduct }) {
  const locale = useLocale() as Locale;
  const t = useTranslations("product");

  return (
    <Card className="group overflow-hidden">
      <Link href={`/bouquets/${product.slug}`} className="block">
        {/* ponytail: gradient placeholder until real R2 photography lands */}
        <div
          className="rf-plate aspect-[4/5] bg-gradient-to-br from-rf-primary-soft to-rf-blush"
          aria-hidden
        />
      </Link>
      <div className="space-y-2 p-4">
        <Badge>{occasionLabel(product.occasion, locale)}</Badge>
        <h3 className="font-[family-name:var(--font-cormorant)] text-2xl font-semibold text-rf-ink">
          <Link href={`/bouquets/${product.slug}`}>{product.name[locale]}</Link>
        </h3>
        <p className="line-clamp-2 text-sm text-rf-ink-muted">
          {product.description[locale]}
        </p>
        <div className="flex items-center justify-between pt-2">
          <span className="font-medium text-rf-ink">
            {t("from", { price: formatPrice(product.priceCents, locale) })}
          </span>
          <Button size="md">{t("add")}</Button>
        </div>
      </div>
    </Card>
  );
}
