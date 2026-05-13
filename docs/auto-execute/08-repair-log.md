# 08 Repair Log - expanded acceptance pass

## Repair loop 1

Failure found by expanded smoke: route/screenshot checks detected broken hard-coded UI text that the first pass did not catch.

Actions:

- Repaired `apps/web/src/lib/webView.ts` labels and fallback text.
- Repaired `apps/web/src/components/RefreshLatestButton.tsx` action/status text.
- Repaired `apps/web/src/components/RunLowPositionButton.tsx` action/status text.
- Repaired `apps/web/src/components/FinancialUI.tsx` date control and pager text.
- Expanded `tools/full_acceptance_smoke.py` to include 12 route cases, 8 API contract cases, integration smoke, Python command smoke, and stricter screenshot/body checks.

Result:

- Full smoke: PASS.
- Next build: PASS.
- compileall: PASS.
- pytest: PASS, 33 passed.
