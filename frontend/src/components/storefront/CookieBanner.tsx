"use client";

import { useSyncExternalStore } from "react";
import { useTranslations } from "next-intl";
import { Link } from "@/i18n/navigation";
import { Button } from "@/components/ui/button";

const STORAGE_KEY = "rf-cookie-consent";

// Minimal external store over localStorage so the banner reads consent without
// a setState-in-effect (and without a hydration mismatch).
let listeners: Array<() => void> = [];
function emit() {
  for (const l of listeners) l();
}
function subscribe(cb: () => void) {
  listeners.push(cb);
  window.addEventListener("storage", cb);
  return () => {
    listeners = listeners.filter((l) => l !== cb);
    window.removeEventListener("storage", cb);
  };
}
function getSnapshot() {
  return localStorage.getItem(STORAGE_KEY);
}
function getServerSnapshot() {
  return null;
}

export function CookieBanner() {
  const t = useTranslations("cookie");
  const consent = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot,
  );

  function choose(value: "accepted" | "rejected") {
    localStorage.setItem(STORAGE_KEY, value);
    emit();
    // ponytail: analytics stays off until consent === "accepted"; wire GA4 here later.
  }

  if (consent) return null;

  return (
    <div
      role="dialog"
      aria-label={t("policy")}
      className="fixed inset-x-0 bottom-0 z-50 border-t border-rf-border bg-rf-surface p-4 shadow-lg"
    >
      <div className="mx-auto flex max-w-6xl flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-rf-ink-muted">
          {t("message")}{" "}
          <Link href="/cookies" className="underline hover:text-rf-primary">
            {t("policy")}
          </Link>
        </p>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => choose("rejected")}>
            {t("reject")}
          </Button>
          <Button onClick={() => choose("accepted")}>{t("accept")}</Button>
        </div>
      </div>
    </div>
  );
}
