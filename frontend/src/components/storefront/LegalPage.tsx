import { getTranslations } from "next-intl/server";
import { Breadcrumbs } from "./Breadcrumbs";

type Section = "terms" | "privacy" | "cookies";

export async function LegalPage({ section }: { section: Section }) {
  const t = await getTranslations("legal");
  const c = await getTranslations("catalog");

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-8">
      <Breadcrumbs
        items={[
          { href: "/", label: c("home") },
          { href: `/${section}`, label: t(`${section}.title`) },
        ]}
      />
      <h1 className="font-[family-name:var(--font-cormorant)] text-5xl font-semibold text-rf-ink">
        {t(`${section}.title`)}
      </h1>
      <p className="mt-2 text-sm text-rf-ink-muted">{t("updated")}</p>
      <div className="mt-6 space-y-4 leading-relaxed text-rf-ink-muted">
        <p>{t(`${section}.p1`)}</p>
        <p>{t(`${section}.p2`)}</p>
        <p>{t(`${section}.p3`)}</p>
      </div>
      <p className="mt-8 rounded-[7px] border border-rf-border bg-rf-blush/50 p-4 text-sm text-rf-ink-muted">
        {t("reviewNote")}
      </p>
    </div>
  );
}
