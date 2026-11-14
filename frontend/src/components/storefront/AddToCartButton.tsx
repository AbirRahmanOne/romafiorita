"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Check } from "lucide-react";
import { Button, type ButtonProps } from "@/components/ui/button";
import { useCart, type CartItem } from "@/lib/cart";

export function AddToCartButton({
  item,
  size,
  className,
}: {
  item: Omit<CartItem, "qty">;
  size?: ButtonProps["size"];
  className?: string;
}) {
  const t = useTranslations("product");
  const { add } = useCart();
  const [added, setAdded] = useState(false);

  function onClick() {
    add(item);
    setAdded(true);
    setTimeout(() => setAdded(false), 1500);
  }

  return (
    <Button size={size} className={className} onClick={onClick}>
      {added ? (
        <>
          <Check className="h-4 w-4" aria-hidden /> {t("added")}
        </>
      ) : (
        t("add")
      )}
    </Button>
  );
}
