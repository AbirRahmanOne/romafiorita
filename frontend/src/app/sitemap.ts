import type { MetadataRoute } from "next";
import { routing } from "@/i18n/routing";

const SITE = "https://romafiorita.com";

// Public, indexable paths (without locale prefix). Product/occasion pages get
// added here from the API in a later phase.
const paths = ["", "/bouquets", "/plants", "/occasions", "/about"];

export default function sitemap(): MetadataRoute.Sitemap {
  return paths.flatMap((path) =>
    routing.locales.map((locale) => ({
      url: `${SITE}/${locale}${path}`,
      alternates: {
        languages: Object.fromEntries(
          routing.locales.map((l) => [l, `${SITE}/${l}${path}`]),
        ),
      },
    })),
  );
}
