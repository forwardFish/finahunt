# Story Test Matrix

Generated: 05/14/2026 15:03:32

| Test point ID | Story ID | Type | Target | Expected | Evidence | Status |
|---|---|---|---|---|---|---|
| TP-STORY-PAYMENT-007-001 | STORY-PAYMENT-007 | route | /deploy | route is reachable and supports the story goal | docs/auto-execute/results/route-smoke.generated.json | PASS |
| TP-STORY-PAYMENT-007-002 | STORY-PAYMENT-007 | functional | Stop only for hard blockers such as credentials, production data/deploy, payment, destructive operations, or repeated unrecoverable failures. | acceptance criterion is proven by test/log/screenshot/API evidence |  | PENDING |
| TP-STORY-GENERAL-010-001 | STORY-GENERAL-010 | functional | contract verification fails when a frontend `/api/...` call has no matching backend route or method; | acceptance criterion is proven by test/log/screenshot/API evidence |  | PENDING |
| TP-STORY-GENERAL-016-001 | STORY-GENERAL-016 | functional | generated story route/API/E2E tests are executed by `run-generated-story-tests.ps1` and cannot count as coverage until they run; | acceptance criterion is proven by test/log/screenshot/API evidence |  | PENDING |
