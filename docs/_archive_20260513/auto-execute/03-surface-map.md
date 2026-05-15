# Surface Map

Generated: 2026-05-13 19:31:02 +0800

## Pages

| Route | File | Responsibility | Status |
|---|---|---|---|
| `/` | `apps/web/src/app/page.tsx` | Today guide: overview, mainline summary, low-position preview, key events, risk boundary | PASS |
| `/fermentation` | `apps/web/src/app/fermentation/page.tsx` | Topic fermentation column: stage, heat, catalyst, continuity, evidence | PASS |
| `/research` | `apps/web/src/app/research/page.tsx` | Low-position research dossier/sample page with candidates and validation state | PASS |
| `/workbench` | `apps/web/src/app/workbench/page.tsx` | Full aggregate workbench with search, events/evidence, matrices | PASS |
| `/low-position` | `apps/web/src/app/low-position/page.tsx` | Independent compatibility low-position board | PRODUCT_DECISION_REQUIRED |
| `/sprint-2` | `apps/web/src/app/sprint-2/page.tsx` | Independent compatibility/acceptance page | PRODUCT_DECISION_REQUIRED |

## APIs

| Method | Route | File | Status |
|---|---|---|---|
| GET | `/api/daily-snapshot` | `apps/web/src/app/api/daily-snapshot/route.ts` | PASS |
| POST | `/api/refresh-latest` | `apps/web/src/app/api/refresh-latest/route.ts` | PASS; acceptance-smoke seed mode for local harness |
| POST | `/api/run-low-position` | `apps/web/src/app/api/run-low-position/route.ts` | PASS; acceptance-smoke seed mode for local harness |

No undocumented Sprint 6/6B API was invented. Existing readers `dailySnapshot.ts` and `lowPositionWorkbench.ts` remain the data contract boundary.

Evidence: `surface-inventory.json`, `integration-smoke.json`, `api-smoke.json`.
