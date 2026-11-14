import type { Locale } from "@/i18n/routing";

export interface SampleProduct {
  slug: string;
  name: Record<Locale, string>;
  description: Record<Locale, string>;
  priceCents: number;
  occasion: string; // occasion slug (see `occasions` below)
}

export interface Occasion {
  slug: string;
  label: Record<Locale, string>;
}

// Occasions from the brief. Bilingual data (same pattern as product names).
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

export function occasionLabel(slug: string, locale: Locale): string {
  return occasions.find((o) => o.slug === slug)?.label[locale] ?? slug;
}

// Placeholder catalogue for the scaffold. Real data comes from the API later.
export const sampleProducts: SampleProduct[] = [
  {
    slug: "rose-di-roma",
    name: { it: "Rose di Roma", en: "Roses of Rome" },
    description: {
      it: "Un classico mazzo di rose rosse fresche, creato a mano nel nostro studio a Roma.",
      en: "A classic bouquet of fresh red roses, hand-made in our Rome studio.",
    },
    priceCents: 4900,
    occasion: "love",
  },
  {
    slug: "primavera-romana",
    name: { it: "Primavera Romana", en: "Roman Spring" },
    description: {
      it: "Composizione colorata di fiori di stagione, come una mattina di primavera a Roma.",
      en: "A colourful seasonal arrangement, like a spring morning in Rome.",
    },
    priceCents: 3900,
    occasion: "birthday",
  },
  {
    slug: "mimosa-8-marzo",
    name: { it: "Mimosa 8 Marzo", en: "Mimosa for 8 March" },
    description: {
      it: "Rami di mimosa profumata per la Festa della Donna.",
      en: "Fragrant mimosa branches for Women's Day.",
    },
    priceCents: 2900,
    occasion: "festa-della-donna",
  },
  {
    slug: "cuore-di-roma",
    name: { it: "Cuore di Roma", en: "Heart of Rome" },
    description: {
      it: "Rose rosse e peonie in una composizione romantica per San Valentino.",
      en: "Red roses and peonies in a romantic arrangement for Valentine's Day.",
    },
    priceCents: 5900,
    occasion: "valentines",
  },
  {
    slug: "grazie-di-cuore",
    name: { it: "Grazie di Cuore", en: "Heartfelt Thanks" },
    description: {
      it: "Un bouquet luminoso di fiori misti per dire grazie.",
      en: "A bright bouquet of mixed flowers to say thank you.",
    },
    priceCents: 3400,
    occasion: "thank-you",
  },
  {
    slug: "candida-memoria",
    name: { it: "Candida Memoria", en: "White Remembrance" },
    description: {
      it: "Fiori bianchi eleganti e sobri per esprimere cordoglio.",
      en: "Elegant, understated white flowers to express sympathy.",
    },
    priceCents: 4500,
    occasion: "sympathy",
  },
];

export function getProductBySlug(slug: string): SampleProduct | undefined {
  return sampleProducts.find((p) => p.slug === slug);
}

export function getProductsByOccasion(occasion?: string): SampleProduct[] {
  if (!occasion) return sampleProducts;
  return sampleProducts.filter((p) => p.occasion === occasion);
}
