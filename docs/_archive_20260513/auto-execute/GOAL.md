# Acceptance Goal Brief

- Generated: 2026-05-13 10:25:45 +08:00
- Project root: D:\lyh\agent\agent-frame\finahunt
- Execution mode: solo auto-execute acceptance-first (skill invoked by user; no approval stops except hard safety blockers).
- Final report: docs/FULL_ACCEPTANCE_DELIVERY_REPORT.md
- Evidence root: docs/qa/full-acceptance

## Required outcomes

1. Preserve routes /, /fermentation, /research, /workbench, /low-position, and /sprint-2 when present.
2. Preserve API routes GET /api/daily-snapshot, POST /api/refresh-latest, POST /api/run-low-position.
3. Establish acceptance mapping before code implementation.
4. Repair blocking frontend build/UI/API and Python contract failures, including S6B-001 story_inputs.
5. Run build, compileall, pytest, route smoke, API smoke, screenshot capture, visual QA, and self review.

## Non-goals and safety boundaries

- No production deployment, real payment, force push, git reset, git clean, destructive cleanup, package-manager migration, or broad architecture rewrite.
- Do not delete .omx, workspace, 	asks, docs, docs/UI, reference images, historical reports, or valid tests.
- Do not weaken tests to manufacture a pass.

## Initial git status

`	ext
On branch agent/parallel-dev-20260318-102914
Your branch is up to date with 'origin/agent/parallel-dev-20260318-102914'.

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	.omx/
	AGENTS.md
	agents/AGENTS.md
	apps/AGENTS.md
	config/AGENTS.md
	docker/AGENTS.md
	docs/AGENTS.md
	docs/UI/
	graphs/AGENTS.md
	packages/AGENTS.md
	skills/AGENTS.md
	tasks/AGENTS.md
	tests/AGENTS.md
	tools/AGENTS.md
	workflows/AGENTS.md
	workspace/

nothing added to commit but untracked files present (use "git add" to track)
`

## Hard stop conditions

Only credentials, captcha/OTP, secrets, payment, production deployment, database/user-data deletion, irreversible destructive operation, or critical missing files would stop execution.
