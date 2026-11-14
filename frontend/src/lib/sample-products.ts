import type { Locale } from "@/i18n/routing";

export interface SampleProduct {
  slug: string;
  name: Record<Locale, string>;
  priceCents: number;
  occasion: Record<Locale, string>;
}

// Placeholder catalogue for the scaffold. Real data comes from the API later.
export const sampleProducts: SampleProduct[] = [
  {
    slug: "rose-di-roma",
    name: { it: "Rose di Roma", en: "Roses of Rome" },
    priceCents: 4900,
    occasion: { it: "Amore", en: "Love" },
  },
  {
    slug: "primavera-romana",
    name: { it: "Primavera Romana", en: "Roman Spring" },
    priceCents: 3900,
    occasion: { it: "Compleanno", en: "Birthday" },
  },
  {
    slug: "mimosa-8-marzo",
    name: { it: "Mimosa 8 Marzo", en: "Mimosa for 8 March" },
    priceCents: 2900,
    occasion: { it: "Festa della Donna", en: "Women's Day" },
  },
];
