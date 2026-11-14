import type { Metadata } from "next";
import { getTranslations, setRequestLocale } from "next-intl/server";
import { Breadcrumbs } from "@/components/storefront/Breadcrumbs";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const t = await getTranslations({ locale, namespace: "contact" });
  return {
    title: t("title"),
    description: t("description"),
    alternates: { canonical: `/${locale}/contact` },
  };
}

export default async function ContactPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("contact");
  const c = await getTranslations("catalog");

  const rows: Array<[string, string]> = [
    [t("email"), "info@romafiorita.com"],
    [t("phone"), "[PHONE]"],
    [t("address"), "[ROME ADDRESS]"],
  ];

  return (
    <div className="mx-auto max-w-2xl px-4 py-10 sm:px-8">
      <Breadcrumbs
        items={[
          { href: "/", label: c("home") },
          { href: "/contact", label: t("title") },
        ]}
      />
      <h1 className="font-[family-name:var(--font-cormorant)] text-5xl font-semibold text-rf-ink">
        {t("title")}
      </h1>
      <p className="mt-4 text-lg text-rf-ink-muted">{t("description")}</p>
      <dl className="mt-8 divide-y divide-rf-border border-y border-rf-border">
        {rows.map(([label, value]) => (
          <div key={label} className="flex justify-between gap-4 py-3">
            <dt className="text-rf-ink-muted">{label}</dt>
            <dd className="font-medium text-rf-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
