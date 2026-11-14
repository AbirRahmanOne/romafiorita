import {
  LayoutDashboard,
  ShoppingCart,
  CalendarClock,
  Flower2,
  Users,
  CreditCard,
  BarChart3,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface AdminNavItem {
  href: string;
  key: string;
  icon: LucideIcon;
  /** Roles that may NOT see this item (payment data hidden from florists/riders). */
  hideFrom?: string[];
}

// href is relative to /admin (locale-aware Link adds the locale prefix).
export const adminNav: AdminNavItem[] = [
  { href: "/admin", key: "dashboard", icon: LayoutDashboard },
  { href: "/admin/orders", key: "orders", icon: ShoppingCart },
  { href: "/admin/delivery-schedule", key: "schedule", icon: CalendarClock },
  { href: "/admin/products", key: "products", icon: Flower2 },
  { href: "/admin/customers", key: "customers", icon: Users, hideFrom: ["FLORIST", "RIDER"] },
  { href: "/admin/payments", key: "payments", icon: CreditCard, hideFrom: ["FLORIST", "RIDER"] },
  { href: "/admin/analytics", key: "analytics", icon: BarChart3, hideFrom: ["FLORIST", "RIDER"] },
  { href: "/admin/settings", key: "settings", icon: Settings, hideFrom: ["FLORIST", "RIDER"] },
];
