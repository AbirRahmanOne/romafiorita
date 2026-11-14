import { defineRouting } from "next-intl/routing";

export const routing = defineRouting({
  locales: ["it", "en"],
  defaultLocale: "it",
  // Always show the locale in the URL (/it/..., /en/...). No auto-redirect by location.
  localePrefix: "always",
  localeDetection: false,
});

export type Locale = (typeof routing.locales)[number];
