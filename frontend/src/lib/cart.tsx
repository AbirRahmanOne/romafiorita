"use client";

import { useSyncExternalStore } from "react";

export interface CartItem {
  slug: string;
  name: string;
  priceCents: number;
  image: string;
  qty: number;
}

const KEY = "rf-cart";
const EMPTY: CartItem[] = [];

// Module-level store (one cart per tab). Read via useSyncExternalStore so it's
// SSR-safe and avoids setState-in-effect.
let items: CartItem[] = EMPTY;
let loaded = false;
const listeners = new Set<() => void>();

function load() {
  if (loaded) return;
  loaded = true;
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : null;
    if (Array.isArray(parsed)) items = parsed;
  } catch {
    /* ignore malformed storage */
  }
}

function commit(next: CartItem[]) {
  items = next;
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    /* storage unavailable */
  }
  for (const l of listeners) l();
}

function subscribe(cb: () => void) {
  load();
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

export function cartAdd(item: Omit<CartItem, "qty">, qty = 1) {
  const existing = items.find((i) => i.slug === item.slug);
  commit(
    existing
      ? items.map((i) =>
          i.slug === item.slug ? { ...i, qty: i.qty + qty } : i,
        )
      : [...items, { ...item, qty }],
  );
}

export function cartSetQty(slug: string, qty: number) {
  commit(
    qty <= 0
      ? items.filter((i) => i.slug !== slug)
      : items.map((i) => (i.slug === slug ? { ...i, qty } : i)),
  );
}

export function cartRemove(slug: string) {
  commit(items.filter((i) => i.slug !== slug));
}

export function cartClear() {
  commit([]);
}

/** Current cart items (read-only snapshot) — handy for tests. */
export function getCartItems(): readonly CartItem[] {
  return items;
}

export function useCart() {
  const list = useSyncExternalStore(
    subscribe,
    () => items,
    () => EMPTY,
  );
  const ready = useSyncExternalStore(
    subscribe,
    () => loaded,
    () => false,
  );
  const count = list.reduce((n, i) => n + i.qty, 0);
  const totalCents = list.reduce((n, i) => n + i.priceCents * i.qty, 0);
  return {
    items: list,
    count,
    totalCents,
    ready,
    add: cartAdd,
    setQty: cartSetQty,
    remove: cartRemove,
    clear: cartClear,
  };
}
