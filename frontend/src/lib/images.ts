// Real photography extracted from the design template (designStorefront.html),
// served statically from /public/design. Swap for R2 photography later; the
// mapping keeps a stable, real photo for every product.

export const HERO_IMAGE = "/design/60f8180d-bea5-44b5-b32e-50a3763eadf2.jpg";

// Pool of bouquet/florist photos (everything except the hero shot).
const POOL = [
  "/design/237a6560-d097-481c-ba4e-f0b99633fc50.jpg",
  "/design/eb98fda6-447c-4b50-85d7-08d39d816972.jpg",
  "/design/dd126005-0cac-45d2-9ecf-3f921659375a.jpg",
  "/design/fe7db2b2-6781-4ba7-b744-5c0a447df71b.jpg",
  "/design/082d52de-a7df-48b0-a642-426ae9885761.jpg",
  "/design/407982cf-57b8-4186-87f1-dc2eaa0b5af7.jpg",
  "/design/9bbd13a5-3c96-41b4-8799-9ba778bffc72.jpg",
  "/design/8a8981ba-fd6b-483e-87f1-02a94a106b41.jpg",
  "/design/93414a1a-1a1c-4045-b2d4-2afa9407a808.jpg",
  "/design/7bcfbcbe-508b-4f0c-ae9f-432e9e11f980.jpg",
  "/design/6cbb56e4-bd9b-4b64-9a72-23e9b5b8c54d.jpg",
  "/design/806a99cb-e21a-461c-b826-635da4268510.jpg",
  "/design/656e0c4b-0f6d-4030-b429-cca3585d6c07.jpg",
  "/design/c31069da-04da-4811-9e84-5549a6dc2859.jpg",
];

/** Stable photo for a product, chosen from the pool by its slug. */
export function productImage(key: string): string {
  let hash = 0;
  for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
  return POOL[hash % POOL.length];
}
