"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Truck, Bike } from "lucide-react";
import { Button } from "@/components/ui/button";
import { classifyCap, type DeliveryZoneResult } from "@/lib/delivery";

export function DeliveryChecker() {
  const t = useTranslations("deliveryChecker");
  const [cap, setCap] = useState("");
  const [result, setResult] = useState<DeliveryZoneResult | null>(null);

  function check(e: React.FormEvent) {
    e.preventDefault();
    setResult(classifyCap(cap));
  }

  const message =
    result === "ROME"
      ? t("rome")
      : result === "ITALY"
        ? t("italy")
        : result === "UNSUPPORTED"
          ? t("unsupported")
          : null;

  return (
    <div className="rounded-2xl border border-rf-border bg-rf-blush/50 p-5">
      <h2 className="mb-3 font-medium text-rf-ink">{t("title")}</h2>
      <form onSubmit={check} className="flex gap-2">
        <input
          inputMode="numeric"
          maxLength={5}
          value={cap}
          onChange={(e) => setCap(e.target.value)}
          placeholder={t("placeholder")}
          aria-label={t("placeholder")}
          className="h-11 flex-1 rounded-full border border-rf-border bg-rf-surface px-4 focus:outline-none focus:ring-2 focus:ring-rf-primary"
        />
        <Button type="submit">{t("check")}</Button>
      </form>
      {message && (
        <p
          className="mt-3 flex items-center gap-2 text-sm text-rf-ink"
          role="status"
        >
          {result === "ROME" && (
            <Bike className="h-4 w-4 text-rf-primary" aria-hidden />
          )}
          {result === "ITALY" && (
            <Truck className="h-4 w-4 text-rf-primary" aria-hidden />
          )}
          {message}
        </p>
      )}
    </div>
  );
}
