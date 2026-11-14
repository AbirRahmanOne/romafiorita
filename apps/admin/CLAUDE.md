# apps/admin — Admin dashboard

Owner/staff dashboard at **admin.romafiorita.com**. **Vite + React SPA**, TypeScript strict,
Tailwind, shadcn/ui, TanStack Router (or React Router), TanStack Query + TanStack Table,
Recharts. Blue/white theme.

Behind login, **no SEO → no SSR**. Ships as a lightweight **static build** (Cloudflare).
Data comes from the API via `packages/api-client` + TanStack Query; auth is the admin JWT
httpOnly cookie set by the API (send credentials with requests; handle 401 → login route).

Read before working here: **`admin-design-system`** (layout, tables, KPI cards, status
badges) and **`admin-dashboard-features`** (what each screen needs). Order actions → also
**`order-lifecycle`**; payments → **`stripe-payments`**.

- Navy sidebar "Roma Fiorita · Admin": Dashboard, Orders, Delivery Schedule, Products,
  Customers, Payments, Analytics, Settings.
- **Role-based visibility:** roles are OWNER / MANAGER / FLORIST / RIDER. Riders and florists
  **never** see payment data.
- Real-time new-order inbox via **SSE** from the API, plus Web Push + sound.
- Mobile-first: the order inbox and schedule must be fully usable on a phone.
- Every screen needs explicit **empty / loading / error** states.
- Tables/KPIs use tabular numbers. Font: Inter everywhere.
