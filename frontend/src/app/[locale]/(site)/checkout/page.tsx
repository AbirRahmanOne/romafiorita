"use client";

import { useState } from "react";
import { useLocale, useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { useCart } from "@/lib/cart";
import { formatPrice } from "@/lib/utils";
import { Button, buttonClasses } from "@/components/ui/button";

export default function CheckoutPage() {
  const t = useTranslations("checkout");
  const tc = useTranslations("cart");
  const locale = useLocale();
  const { items, totalCents, clear, ready } = useCart();
  const [confirmed, setConfirmed] = useState(false);

  if (confirmed) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center sm:px-8">
        <h1 className="font-[family-name:var(--font-cormorant)] text-4xl font-semibold text-rf-ink">
          {t("confirmedTitle")}
        </h1>
        <p className="mt-4 text-rf-ink-muted">{t("confirmedBody")}</p>
        <Link href="/bouquets" className={buttonClasses({ className: "mt-6" })}>
          {tc("continue")}
        </Link>
      </div>
    );
  }

  if (ready && items.length === 0) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-20 text-center sm:px-8">
        <h1 className="font-[family-name:var(--font-cormorant)] text-4xl font-semibold text-rf-ink">
          {t("title")}
        </h1>
        <p className="mt-4 text-rf-ink-muted">{t("empty")}</p>
        <Link href="/bouquets" className={buttonClasses({ className: "mt-6" })}>
          {tc("continue")}
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-8">
      <h1 className="font-[family-name:var(--font-cormorant)] text-5xl font-semibold text-rf-ink">
        {t("title")}
      </h1>

      <div className="mt-6 rounded-[7px] border border-rf-border bg-rf-blush/50 p-4 text-sm text-rf-ink-muted">
        {t("note")}
      </div>

      <h2 className="mt-8 text-xs font-semibold uppercase tracking-[0.14em] text-rf-ink-muted">
        {t("summary")}
      </h2>
      <ul className="mt-3 divide-y divide-rf-border border-y border-rf-border">
        {items.map((i) => (
          <li key={i.slug} className="flex justify-between gap-4 py-3">
            <span className="text-rf-ink">
              {i.name}{" "}
              <span className="text-rf-ink-muted">× {i.qty}</span>
            </span>
            <span className="tabular-nums text-rf-ink">
              {formatPrice(i.priceCents * i.qty, locale)}
            </span>
          </li>
        ))}
      </ul>
      <div className="mt-4 flex items-center justify-between">
        <span className="font-medium text-rf-ink">{t("total")}</span>
        <span className="text-xl font-semibold text-rf-ink">
          {formatPrice(totalCents, locale)}
        </span>
      </div>

      <div className="mt-8 flex flex-wrap gap-3">
        <Button
          size="lg"
          onClick={() => {
            clear();
            setConfirmed(true);
          }}
        >
          {t("placeOrder")}
        </Button>
        <Link
          href="/cart"
          className={buttonClasses({ size: "lg", variant: "secondary" })}
        >
          {t("back")}
        </Link>
      </div>
    </div>
  );
}
