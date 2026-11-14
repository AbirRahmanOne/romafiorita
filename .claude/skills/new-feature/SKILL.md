---
name: new-feature
description: Use at the start of ANY new feature, phase, or change in the Roma Fiorita monorepo — it sets the non-negotiable working rules and points to the area-specific skill to read next.
---

# Starting work on Roma Fiorita

Roma Fiorita (romafiorita.com) is a Rome-based flower & gift shop: customers order from
anywhere, delivery is Italy-only (own riders in Rome, courier for the rest). Monorepo:
`apps/web` (pink storefront), `apps/admin` (blue/white dashboard), `apps/api` (FastAPI),
`packages/ui-tokens`, `packages/api-client`.

## Before you touch code

1. **Read the area skill first.** Every area has a skill in `.claude/skills/`. Read it
   before working in that area, and update it if a convention changes.

   | Working on… | Read |
   |---|---|
   | Storefront UI / components | `storefront-design-system` |
   | Admin UI / dashboard screens | `admin-design-system`, `admin-dashboard-features` |
   | Translations, routing, metadata, SEO | `i18n-seo` |
   | Delivery zones, slots, cut-offs, fees | `checkout-and-delivery-rules` |
   | Payments, refunds, webhooks | `stripe-payments` |
   | Order states & transitions | `order-lifecycle` |
   | FastAPI, models, migrations | `backend-api-conventions` |
   | Emails, push, reminders | `notifications-and-reminders` |
   | Tests / CI | `testing-and-quality` |
   | render.yaml, DNS, deploy | `deployment-render` |
   | Footer identity, GDPR, terms | `legal-and-compliance-italy` |

2. **Respect phase gating.** Do not build business features until Phase 0 (this skill +
   the skills above + `CLAUDE.md`) and Phase 1 (monorepo scaffold) are done and reviewed.
   Before each phase, show a short plan; ask only if a decision is truly blocking.

## Hard rules (never skip)

- **No hard-coded user-facing text.** Every string goes through i18n in both `it` and `en`.
- **Money = integer cents, EUR only.** Never floats. Never trust client amounts — recompute
  server-side.
- **Time:** store UTC, do business logic in `Europe/Rome`, also show the sender's local time.
- **No secrets in git.** Use `.env`; keep `.env.example` current for every app.
- **Placeholders stay until real values arrive:** legal company name, Rome address, Partita
  IVA, PEC, phone/WhatsApp, same-day cut-off `[14:00]`, exact-time min notice `[3h]`,
  window fee `€[X]`, exact-time fee `€[Y]`. Mark them clearly; never invent real values.

## Definition of done

- Passes lint + typecheck (ESLint/Prettier, Ruff/mypy) and tests (Vitest/Playwright, pytest).
- Ships with the tests its area skill requires (e.g. delivery-rule units, webhook fixtures,
  state-machine tests).
- WCAG AA, 44px tap targets, visible focus, colour never the only signal.
- Small, focused commits with Conventional Commit messages (`feat:`, `fix:`, `chore:` …);
  small PRs.
- Relevant skill updated if a convention changed.
