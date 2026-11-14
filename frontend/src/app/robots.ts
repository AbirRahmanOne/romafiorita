import type { MetadataRoute } from "next";

const SITE = "https://romafiorita.com";

// Explicitly welcome search + AI crawlers; keep admin/api out of the index.
const allowedBots = [
  "OAI-SearchBot",
  "ChatGPT-User",
  "Claude-SearchBot",
  "Claude-User",
  "PerplexityBot",
  "Googlebot",
  "Bingbot",
];

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      ...allowedBots.map((userAgent) => ({ userAgent, allow: "/" })),
      { userAgent: "*", allow: "/", disallow: ["/it/admin", "/en/admin", "/api"] },
    ],
    sitemap: `${SITE}/sitemap.xml`,
    host: SITE,
  };
}
