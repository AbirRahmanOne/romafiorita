export type DeliveryZoneResult = "ROME" | "ITALY" | "UNSUPPORTED";

/**
 * Classify a recipient CAP (Italian postcode) into a delivery zone.
 * Rome (CAP 001xx) = same-day own riders; other 5-digit CAP = national courier.
 *
 * ponytail: frontend convenience stub — the backend is the source of truth and
 * validates against real CAP ranges / capacity (see checkout-and-delivery-rules).
 */
export function classifyCap(capRaw: string): DeliveryZoneResult {
  const cap = capRaw.trim();
  if (!/^\d{5}$/.test(cap)) return "UNSUPPORTED";
  if (cap.startsWith("001")) return "ROME";
  return "ITALY";
}
