import type { components } from "./api-types";

export type Product = components["schemas"]["ProductRead"];
export type ProductList = components["schemas"]["ProductList"];
export type ProductCreate = components["schemas"]["ProductCreate"];
export type ProductUpdate = components["schemas"]["ProductUpdate"];

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  // no-store: always fresh, and keeps pages out of build-time API coupling.
  const res = await fetch(`${BASE}${path}`, { cache: "no-store", ...init });
  if (!res.ok) {
    let code = "http_error";
    let message = res.statusText;
    try {
      const body = await res.json();
      code = body?.error?.code ?? code;
      message = body?.error?.message ?? message;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, code, message);
  }
  return res.status === 204 ? (undefined as T) : await res.json();
}

const json = (body: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export function listProducts(params?: {
  occasion?: string;
  includeInactive?: boolean;
  limit?: number;
}): Promise<ProductList> {
  const q = new URLSearchParams();
  if (params?.occasion) q.set("occasion", params.occasion);
  if (params?.includeInactive) q.set("include_inactive", "true");
  if (params?.limit) q.set("limit", String(params.limit));
  const qs = q.toString();
  return request<ProductList>(`/products${qs ? `?${qs}` : ""}`);
}

export async function getProduct(slug: string): Promise<Product | null> {
  try {
    return await request<Product>(`/products/${slug}`);
  } catch {
    // API down or 404 → null, so pages render notFound instead of crashing.
    return null;
  }
}

export function createProduct(data: ProductCreate): Promise<Product> {
  return request<Product>("/products", json(data));
}

export function updateProduct(
  id: number,
  data: ProductUpdate,
): Promise<Product> {
  return request<Product>(`/products/id/${id}`, {
    ...json(data),
    method: "PATCH",
  });
}

export function deleteProduct(id: number): Promise<void> {
  return request<void>(`/products/id/${id}`, { method: "DELETE" });
}

/** Localize a product's name/description by locale. */
export function productName(p: Product, locale: string): string {
  return locale === "it" ? p.name_it : p.name_en;
}
export function productDescription(p: Product, locale: string): string {
  return (locale === "it" ? p.description_it : p.description_en) ?? "";
}
