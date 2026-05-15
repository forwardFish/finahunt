# Full-Stack Delivery Plan

| ID | Lane | Task | Target files | Depends on | Verification | Status | Evidence |
|---|---|---|---|---|---|---|---|
| FS-000 | intake | Read repo instructions, requirement docs, UI references, and existing architecture | AGENTS.md, docs, source tree | none | project intake exists | pending | docs/auto-execute/00-project-intake.md |
| FS-010 | requirements | Convert PRD/UI into acceptance criteria and traceability | docs/auto-execute | FS-000 | matrix covers P0/P1 requirements | pending | docs/auto-execute/02-requirement-traceability-matrix.md |
| FS-020 | frontend | Implement screens/routes/components/states required by UI | frontend/app/src/components | FS-010 | frontend build/tests/visual evidence | pending | docs/auto-execute/logs |
| FS-030 | backend | Implement APIs/services/data behavior required by PRD | backend/server/api/src | FS-010 | backend build/tests/API smoke | pending | docs/auto-execute/logs |
| FS-040 | contract | Align frontend calls with backend routes, payloads, auth, and errors | frontend + backend | FS-020, FS-030 | contract/API smoke evidence | pending | docs/auto-execute/13-frontend-backend-contract-map.md |
| FS-050 | frontend-test | Run frontend-only verification | frontend | FS-020 | lint/typecheck/test/build pass or documented blocker | pending | docs/auto-execute/logs |
| FS-060 | backend-test | Run backend-only verification | backend | FS-030 | build/test/API pass or documented blocker | pending | docs/auto-execute/logs |
| FS-070 | integrated-test | Run full-flow/integrated verification | full stack | FS-040, FS-050, FS-060 | full-flow smoke/E2E evidence | pending | docs/auto-execute/FULL_FLOW_ACCEPTANCE.md |
| FS-080 | review | Review implementation against PRD/UI/evidence | changed files | FS-070 | code review recorded | pending | docs/auto-execute/09-code-review.md |

