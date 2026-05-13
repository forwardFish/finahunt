# 05 Known Gaps and Assumptions - expanded acceptance pass

## Clarified API coverage

The repository currently exposes exactly 3 Next API route files. The first report's raw count was technically true but too weak as acceptance evidence. This pass expands coverage to 8 API contract cases and adds Python workflow command smoke so frontend/backend coupling is represented more honestly.

## Remaining non-blocking unfinished items

- `skills/fetch/adapters/base.py` contains abstract `raise NotImplementedError` methods. This is expected for an abstract adapter base class and is not a delivery blocker.
- `packages/llm/router.py` contains environment placeholder resolution helpers. The marker scan caught the word `placeholder`; this is implemented behavior, not an unfinished TODO.
- Broader product/API expansion is a next product decision: if external consumers need granular endpoints, add domain APIs such as themes/events/workbench/search. Do not invent them only to inflate route count.
- Mobile viewport visual QA is not fully automated in this pass; desktop screenshot evidence is complete.

## Conservative decisions

- No package manager change and no new dependency were introduced.
- Existing data loaders under `apps/web/src/lib` were preserved.
- No docs/UI, workspace, tasks, or historical reports were deleted.
