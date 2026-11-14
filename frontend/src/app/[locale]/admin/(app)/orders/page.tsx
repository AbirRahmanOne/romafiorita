import { use } from "react";
import { setRequestLocale } from "next-intl/server";
import { PlaceholderPage } from "@/components/admin/PlaceholderPage";

export default function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = use(params);
  setRequestLocale(locale);
  return <PlaceholderPage navKey="orders" emptyKey="orders" />;
}
