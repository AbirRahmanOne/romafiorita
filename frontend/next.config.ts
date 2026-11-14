import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  images: {
    // ponytail: wide-open while scaffolding; tighten to the R2 host before prod.
    remotePatterns: [{ protocol: "https", hostname: "**" }],
    // Our own placeholder art is SVG served from /public.
    dangerouslyAllowSVG: true,
    contentDispositionType: "attachment",
  },
  turbopack: {
    rules: {
      "*.css": { loaders: ["@tailwindcss/turbopack"], as: "*.css" },
    },
  },
};

export default withNextIntl(nextConfig);
