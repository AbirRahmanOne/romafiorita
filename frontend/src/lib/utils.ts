import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format integer cents as an EUR price string for the given locale. */
export function formatPrice(cents: number, locale: string) {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: "EUR",
  }).format(cents / 100);
}
