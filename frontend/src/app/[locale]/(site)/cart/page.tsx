"use client";

import Image from "next/image";
import { useLocale, useTranslations } from "next-intl";
import { Minus, Plus, Trash2 } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { useCart } from "@/lib/cart";
import { formatPrice } from "@/lib/utils";
import { buttonClasses } from "@/components/ui/button";

export default function CartPage() {
  const t = useTranslations("cart");
  const locale = useLocale();
  const { items, totalCents, setQty, remove, ready } = useCart();

  if (ready && items.length === 0) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center sm:px-8">
        <h1 className="font-[family-name:var(--font-cormorant)] text-4xl font-semibold text-rf-ink">
          {t("title")}
        </h1>
        <p className="mt-4 text-rf-ink-muted">{t("empty")}</p>
        <Link href="/bouquets" className={buttonClasses({ className: "mt-6" })}>
          {t("continue")}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-8">
      <h1 className="font-[family-name:var(--font-cormorant)] text-5xl font-semibold text-rf-ink">
        {t("title")}
      </h1>

      <ul className="mt-8 divide-y divide-rf-border border-y border-rf-border">
        {items.map((i) => (
          <li key={i.slug} className="flex gap-4 py-4">
            <div className="rf-plate relative h-24 w-20 shrink-0 overflow-hidden">
              <Image src={i.image} alt={i.name} fill sizes="80px" className="object-cover" />
            </div>
            <div className="flex flex-1 flex-col">
              <div className="flex justify-between gap-4">
                <span className="font-[family-name:var(--font-cormorant)] text-xl font-semibold text-rf-ink">
                  {i.name}
                </span>
                <span className="font-medium text-rf-ink">
                  {formatPrice(i.priceCents * i.qty, locale)}
                </span>
              </div>
              <span className="text-sm text-rf-ink-muted">
                {formatPrice(i.priceCents, locale)} {t("each")}
              </span>
              <div className="mt-auto flex items-center justify-between pt-3">
                <div className="inline-flex items-center rounded-[4px] border border-rf-border">
                  <button
                    onClick={() => setQty(i.slug, i.qty - 1)}
                    aria-label={t("qty")}
                    className="flex h-9 w-9 items-center justify-center hover:bg-rf-ink/5"
                  >
                    <Minus className="h-4 w-4" aria-hidden />
                  </button>
                  <span className="w-8 text-center tabular-nums">{i.qty}</span>
                  <button
                    onClick={() => setQty(i.slug, i.qty + 1)}
                    aria-label={t("qty")}
                    className="flex h-9 w-9 items-center justify-center hover:bg-rf-ink/5"
                  >
                    <Plus className="h-4 w-4" aria-hidden />
                  </button>
                </div>
                <button
                  onClick={() => remove(i.slug)}
                  className="inline-flex items-center gap-1 text-sm text-rf-ink-muted hover:text-rf-danger"
                >
                  <Trash2 className="h-4 w-4" aria-hidden /> {t("remove")}
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-6 flex items-center justify-between">
        <span className="text-rf-ink-muted">{t("subtotal")}</span>
        <span className="text-xl font-semibold text-rf-ink">
          {formatPrice(totalCents, locale)}
        </span>
      </div>
      <p className="mt-2 text-sm text-rf-ink-muted">{t("deliveryNote")}</p>

      <div className="mt-6 flex flex-wrap gap-3">
        <Link href="/checkout" className={buttonClasses({ size: "lg" })}>
          {t("checkout")}
        </Link>
        <Link
          href="/bouquets"
          className={buttonClasses({ size: "lg", variant: "secondary" })}
        >
          {t("continue")}
        </Link>
      </div>
    </div>
  );
}
