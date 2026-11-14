import { defineCloudflareConfig } from "@opennextjs/cloudflare";

// Default OpenNext → Cloudflare Workers config. Add R2/KV incremental cache
// here later if needed (see @opennextjs/cloudflare docs).
const config = {
  ...defineCloudflareConfig(),
  // `npm run build` is the OpenNext build itself — pin the inner Next build
  // so OpenNext doesn't recurse into `npm run build`.
  buildCommand: "npx next build",
};

export default config;
