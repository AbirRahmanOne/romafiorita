import { getTranslations, setRequestLocale } from "next-intl/server";
import { Topbar } from "@/components/admin/Topbar";
import { KpiCard } from "@/components/admin/KpiCard";
import { EmptyState } from "@/components/admin/EmptyState";
import { listProducts } from "@/lib/api";

export default async function AdminDashboard({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("admin");

  // Only products have a backend so far; the rest are placeholders.
  let productCount = 0;
  try {
    productCount = (await listProducts({ limit: 1 })).total;
  } catch {
    /* API down — show 0 */
  }

  const kpis: Array<[string, string]> = [
    ["ordersToday", "0"],
    ["revenueToday", "€0,00"],
    ["pending", "0"],
    ["products", String(productCount)],
  ];

  return (
    <>
      <Topbar title={t("nav.dashboard")} />
      <div className="space-y-6 p-4 md:p-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {kpis.map(([key, value]) => (
            <KpiCard key={key} label={t(`kpi.${key}`)} value={value} />
          ))}
        </div>
        <EmptyState message={t("empty.dashboard")} />
      </div>
    </>
  );
}
