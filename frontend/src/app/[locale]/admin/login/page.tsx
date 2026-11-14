import { use } from "react";
import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";

export default function AdminLogin({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations("admin.login");

  return (
    <div className="flex min-h-screen items-center justify-center bg-ad-bg p-4 font-[family-name:var(--font-inter)] text-ad-ink">
      <div className="w-full max-w-sm rounded-xl border border-ad-border bg-ad-surface p-8 shadow-sm">
        <p className="text-sm text-ad-ink-muted">{t("subtitle")}</p>
        <h1 className="mt-1 text-2xl font-semibold">{t("title")}</h1>

        {/* ponytail: inert placeholder form; wires to the API /auth endpoint later */}
        <form className="mt-6 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              {t("email")}
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              className="mt-1 h-11 w-full rounded-lg border border-ad-border px-3 focus:outline-none focus:ring-2 focus:ring-ad-primary"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              {t("password")}
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              className="mt-1 h-11 w-full rounded-lg border border-ad-border px-3 focus:outline-none focus:ring-2 focus:ring-ad-primary"
            />
          </div>
          <button
            type="submit"
            disabled
            className="h-11 w-full rounded-lg bg-ad-primary font-medium text-white hover:bg-ad-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ad-primary focus-visible:ring-offset-2 disabled:opacity-50"
          >
            {t("submit")}
          </button>
        </form>
        <p className="mt-4 text-xs text-ad-ink-muted">{t("hint")}</p>
      </div>
    </div>
  );
}
