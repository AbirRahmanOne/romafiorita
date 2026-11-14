import { setRequestLocale, getTranslations } from "next-intl/server";
import { Topbar } from "@/components/admin/Topbar";
import { ProductsManager } from "@/components/admin/ProductsManager";
import { EmptyState } from "@/components/admin/EmptyState";
import { listProducts, type Product } from "@/lib/api";

export default async function Page({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  setRequestLocale(locale);
  const t = await getTranslations("admin");

  let products: Product[] = [];
  let failed = false;
  try {
    products = (await listProducts({ includeInactive: true, limit: 100 }))
      .items;
  } catch {
    failed = true;
  }

  return (
    <>
      <Topbar title={t("nav.products")} />
      <div className="p-4 md:p-6">
        {failed ? (
          <EmptyState message={t("empty.products")} />
        ) : (
          <ProductsManager initial={products} />
        )}
      </div>
    </>
  );
}
