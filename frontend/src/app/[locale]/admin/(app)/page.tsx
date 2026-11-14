import { use } from "react";
import { useTranslations } from "next-intl";
import { setRequestLocale } from "next-intl/server";
import { Topbar } from "@/components/admin/Topbar";
import { KpiCard } from "@/components/admin/KpiCard";
import { EmptyState } from "@/components/admin/EmptyState";

export default function AdminDashboard({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  const t = useTranslations("admin");

  // Zeroed placeholders until the API feeds real KPIs.
  const kpis: Array<[string, string]> = [
    ["ordersToday", "0"],
    ["revenueToday", "€0,00"],
    ["pending", "0"],
    ["deliveriesToday", "0"],
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
