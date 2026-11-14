import { useTranslations } from "next-intl";
import { Topbar } from "./Topbar";
import { EmptyState } from "./EmptyState";

/** Section shell: localized top bar + an empty state. Replaced with real
 * screens in later phases (see the admin-dashboard-features skill). */
export function PlaceholderPage({
  navKey,
  emptyKey,
}: {
  navKey: string;
  emptyKey: string;
}) {
  const t = useTranslations("admin");
  return (
    <>
      <Topbar title={t(`nav.${navKey}`)} />
      <div className="p-4 md:p-6">
        <EmptyState message={t(`empty.${emptyKey}`)} />
      </div>
    </>
  );
}
