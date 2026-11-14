"use client";

import { useTranslations } from "next-intl";
import { ShoppingBag } from "lucide-react";
import { Link } from "@/i18n/navigation";
import { useCart } from "@/lib/cart";
import { buttonClasses } from "@/components/ui/button";

export function CartLink() {
  const t = useTranslations("nav");
  const { count, ready } = useCart();

  return (
    <Link
      href="/cart"
      aria-label={t("cart")}
      className={buttonClasses({ variant: "secondary", className: "relative gap-2" })}
    >
      <ShoppingBag className="h-[17px] w-[17px]" aria-hidden />
      {ready && count > 0 && (
        <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-rf-primary px-1 text-xs font-medium tabular-nums text-white">
          {count}
        </span>
      )}
    </Link>
  );
}
