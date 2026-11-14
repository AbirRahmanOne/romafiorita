import { useTranslations } from "next-intl";
import { Camera, BadgeEuro, Clock } from "lucide-react";

export function TrustStrip() {
  const t = useTranslations("trust");

  const items = [
    { icon: Camera, title: t("photoTitle"), body: t("photoBody") },
    { icon: BadgeEuro, title: t("priceTitle"), body: t("priceBody") },
    { icon: Clock, title: t("timeTitle"), body: t("timeBody") },
  ];

  return (
    <section aria-label={t("title")} className="bg-rf-blush/60 py-12">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 sm:grid-cols-3">
        {items.map(({ icon: Icon, title, body }) => (
          <div key={title} className="flex flex-col items-center text-center">
            <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-rf-primary-soft text-rf-primary">
              <Icon className="h-6 w-6" aria-hidden />
            </span>
            <h3 className="font-medium text-rf-ink">{title}</h3>
            <p className="mt-1 text-sm text-rf-ink-muted">{body}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
