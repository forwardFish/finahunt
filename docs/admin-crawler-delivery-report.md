# Admin Crawler Delivery Report

## Modified Files

- Storage: `packages/storage/models.py`, `packages/storage/repositories.py`, `packages/storage/admin_audit.py`, `packages/storage/__init__.py`
- Crawler: `scripts/run_admin_crawler.py`
- Web/API: `apps/web/src/app/admin/page.tsx`, `apps/web/src/lib/admin-db.ts`, `apps/web/src/lib/admin-scheduler.ts`, `apps/web/src/app/api/admin/**/route.ts`
- Styling: `apps/web/src/app/globals.css`
- Dependencies: `apps/web/package.json`, `apps/web/package-lock.json`
- Tests/docs/evidence: `tests/unit/test_storage_repository.py`, `docs/admin-crawler-audit-plan.md`, `docs/admin-crawler-visual/*`

## Tables and Fields

- `raw_contents` extended with `source_hash`, `http_status`, `content_length`, `license_status`, `truth_score`, `authenticity_status`, `review_status`, `reviewer_note`.
- New `crawl_runs` table tracks source, status, start/finish time, fetched/inserted/duplicate/failed counts, error message, and payload.
- New `admin_crawler_settings` table stores enabled flag, schedule time, source id, and updated time.
- New `admin_review_logs` table stores raw-content review actions and notes.
- `PostgresRepository.bootstrap()` now performs idempotent raw-content column/index backfill for existing local PostgreSQL volumes.

## APIs

- `GET /api/admin/crawler/status`
- `POST /api/admin/crawler/run`
- `GET /api/admin/crawler/settings`
- `POST /api/admin/crawler/settings`
- `GET /api/admin/crawl-runs`
- `GET /api/admin/raw-contents`
- `GET /api/admin/raw-contents/[documentId]`
- `POST /api/admin/raw-contents/[documentId]/review`

## How to Run

Start PostgreSQL:

```powershell
docker compose -f docker/docker-compose.yml up -d postgres
$env:DATABASE_URL="postgresql+psycopg://finahunt:finahunt_local@127.0.0.1:54329/finahunt"
```

Run the crawler:

```powershell
python scripts/run_admin_crawler.py --source all
```

Open the backend:

```powershell
cd apps/web
npm run dev
```

Then visit `http://127.0.0.1:3000/admin`.

## Data Authenticity Checks

- `source_hash` is generated from source id, URL, title, publish time, and content text.
- `truth_score` uses the required 100-point rules: URL, HTTP 2xx, source name, title length, content length, publish time, hash, and no garbled text.
- `authenticity_status` maps score to `trusted`, `likely_trusted`, `needs_review`, or `blocked`.
- Human review actions update `review_status` and `authenticity_status`, then append `admin_review_logs`.

## Verification Evidence

- `python -m compileall -q agents packages graphs workflows tools skills tests scripts`: PASS
- `python -m pytest -q`: PASS, 38 passed
- `cd apps/web; npm run build`: PASS
- Sequential crawler smoke with SQLite fallback: first run inserted 10 rows, second run inserted 0 and counted 10 duplicates. This proves crawler/repository write and duplicate logic, but it is not a substitute for PostgreSQL acceptance.
- Browser screenshot: `docs/admin-crawler-visual/admin-page.png`
- Visual diff report: `docs/admin-crawler-visual/visual-compare.json`
- Visual diff image: `docs/admin-crawler-visual/admin-page-diff.png`

## Known Issues

- PostgreSQL hard acceptance is blocked on this machine because Docker Desktop is not running. `docker compose -f docker/docker-compose.yml up -d postgres` failed to connect to `dockerDesktopLinuxEngine`, and `127.0.0.1:54329` is not listening.
- Because PostgreSQL is unavailable, live `/admin` screenshot shows the designed page structure but no real database rows. Re-run the PostgreSQL acceptance steps after Docker is available.
- Visual comparison currently reports `MANUAL_REVIEW_REQUIRED` because the screenshot has no database rows while the reference image includes populated tables, and because pixel-perfect matching is intentionally stricter than the structural layout check.
- The scheduler is a local self-use lightweight interval inside the Next.js process; it is not a production-grade durable scheduler.
