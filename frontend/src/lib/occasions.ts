import type { Locale } from "@/i18n/routing";

export interface Occasion {
  slug: string;
  label: Record<Locale, string>;
}

// Occasions from the brief. Static bilingual data (not product content).
export const occasions: Occasion[] = [
  { slug: "love", label: { it: "Amore e anniversario", en: "Love & Anniversary" } },
  { slug: "birthday", label: { it: "Compleanno", en: "Birthday" } },
  { slug: "valentines", label: { it: "San Valentino", en: "Valentine's Day" } },
  {
    slug: "festa-della-donna",
    label: { it: "Festa della Donna", en: "Women's Day (8 March)" },
  },
  {
    slug: "festa-della-mamma",
    label: { it: "Festa della Mamma", en: "Mother's Day" },
  },
  { slug: "sympathy", label: { it: "Cordoglio", en: "Sympathy" } },
  { slug: "thank-you", label: { it: "Ringraziamento", en: "Thank you" } },
  { slug: "get-well", label: { it: "Pronta guarigione", en: "Get well" } },
  { slug: "christmas", label: { it: "Natale", en: "Christmas" } },
  { slug: "corporate", label: { it: "Aziende", en: "Corporate" } },
];

export function occasionLabel(slug: string | null | undefined, locale: Locale): string {
  if (!slug) return "";
  return occasions.find((o) => o.slug === slug)?.label[locale] ?? slug;
}
