# ADR 0001 — Reconcile OrderStatus enum by rewriting the initial migration

**Status:** Accepted · **Date:** 2026-11-20 · **Phase:** 2 (critical fixes)

## Context

The `OrderStatus` enum in the code disagreed with the target spec (§4D): the code
had `PREPARING` and was missing `AWAITING_PHOTO`, `APPROVED`, `PARTIALLY_REFUNDED`,
`PAYMENT_REQUESTED`, `EXPIRED`. The audit (risk #7) flagged fixing this *before* any
order logic is written, while it is still free.

The working rules forbid rewriting migrations and require two-step (expand→migrate→
contract) changes for drops/renames. But:

- There is **no deployed database** yet (audit risk #1: no environment has ever run a
  migration). Nothing to preserve.
- The enum change is in the **initial** migration, one commit old, never shipped.
- A proper `ALTER TYPE` enum migration is painful and dialect-specific (Postgres
  `ALTER TYPE … ADD VALUE` can't run in a transaction and can't remove values;
  SQLite needs a table rebuild).

## Decision

Rewrite the single initial migration (`f9713e4b5412_initial_schema`) to reflect the
corrected enum and the Phase-2 `Staff` auth columns (`refresh_jti`,
`failed_login_count`, `locked_until`), rather than stacking a convoluted enum-alter
migration on top. The migration's `downgrade` explicitly drops the native Postgres
enum types (no-op on SQLite) so it fully reverses.

## Consequences

- Clean, single source-of-truth schema; CI verifies `upgrade→downgrade→upgrade` on
  real Postgres.
- **This is a one-time exception** justified only by "no deployment exists." Once the
  schema is deployed anywhere, the normal two-step rule applies and migrations are
  append-only.
