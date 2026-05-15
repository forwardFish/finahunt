# Admin Crawler Audit Plan

## Current Capabilities

- `packages/storage/models.py` already has SQLAlchemy models for `RawContent`, `NormalizedContent`, `Event`, `Theme`, runtime artifacts, daily snapshots, and low-position workbench data.
- `packages/storage/repositories.py` already provides `PostgresRepository`, `bootstrap()`, `save_runtime_projection()`, and `_merge_raw_contents()` as the canonical runtime-to-PostgreSQL write path.
- `docker/docker-compose.yml` already defines a local PostgreSQL 16 service on `127.0.0.1:54329` using database/user/password `finahunt`.
- `apps/web/package.json` already uses Next.js App Router with React 19 and TypeScript; admin PostgreSQL access only needs `pg` and `@types/pg`.
- `apps/web/src/app` already has colocated pages and `apps/web/src/app/api` already uses Node runtime API routes that can call Python scripts.

## Missing Pieces

- `RawContent` did not store source hash, HTTP status, content length, license status, truth score, authenticity status, review status, or reviewer note.
- There were no admin-specific tables for crawl runs, crawler settings, or review logs.
- Repository methods existed for runtime projection, but not for admin raw-data listing, review updates, crawler settings, or crawl-run status.
- There was no seed crawler that writes raw crawl data into PostgreSQL and proves duplicate handling.
- The frontend had no `/admin` page, no admin APIs, and no direct PostgreSQL reader for raw crawl data.
- The previous validation path did not prove visual parity with `docs/UI/后台管理页面.png` or prove crawler-to-PostgreSQL persistence.

## Minimal Implementation Plan

- Extend the existing SQLAlchemy storage layer without replacing `RawContent`, `RuntimeRepository`, or `save_runtime_projection()`.
- Add admin audit helpers for source hash, garbled text detection, truth score, and authenticity status.
- Add a seed crawler at `scripts/run_admin_crawler.py` that creates a crawl run, writes 10 seed financial-news rows, skips duplicates, and updates run counts.
- Add `pg`-backed Next.js API routes under `/api/admin/*` for crawler status, settings, runs, raw content list/detail, and review updates.
- Add a single `/admin` page matching the reference image: simple top bar, left menu, crawler controls, crawl-run table, raw-data table, and detail/review panel.
- Validate with Python compile/tests, PostgreSQL crawler writes, `npm run build`, live `/admin` browser screenshot, and visual comparison artifacts.
