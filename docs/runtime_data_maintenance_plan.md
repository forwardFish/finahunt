# Finahunt Runtime Data Maintenance Plan

## Goal

Keep JSON artifacts as immutable evidence, but build a stable association layer for cross-run and cross-day analysis.

## Current Situation

- Raw crawl data is stored per run under `workspace/artifacts/source_fetch/<run_id>/`.
- Structured runtime output is stored per run under `workspace/artifacts/runtime/<run_id>/`.
- This is good for audit and replay, but weak for long-term query and joins.

## Recommended Architecture

### 1. Immutable Raw Layer

Keep the current JSON and JSONL outputs unchanged.

- `raw_contents.jsonl`
- `raw_documents.json`
- `canonical_events.json`
- `theme_candidates.json`
- `low_position_opportunities.json`

This layer is for:

- audit
- replay
- debugging

### 2. Index And Association Layer

Add a metadata database.

Recommended path:

1. local `SQLite`
2. later move to `PostgreSQL`

Core tables:

- `runs`
- `raw_content_items`
- `raw_documents`
- `canonical_events`
- `theme_clusters`
- `assets`
- `event_theme_links`
- `event_asset_links`
- `theme_asset_links`
- `daily_theme_snapshots`

Stable relation chain:

`run -> raw_content -> raw_document -> canonical_event -> theme_cluster -> candidate_asset`

### 3. Daily Serving Layer

Add daily aggregate views for frontend.

- `daily_event_view`
- `daily_theme_view`
- `daily_low_position_view`
- `daily_source_ingest_view`

## Identity Rules

Use stable IDs instead of only relying on paths.

- `content_fingerprint = source_id + source_url + published_at + title`
- `document_id` links cleaned text back to raw content
- `canonical_key` is the stable event identity
- `cluster_id` is the stable theme identity
- stock links should use normalized code first, name second

## Retention Strategy

- keep raw JSON locally for 90-180 days
- keep database metadata for full history
- compress old raw artifacts by month
- partition daily views by month

## Next Step

1. keep current JSON artifacts as immutable evidence
2. add a small association DB
3. write one importer from `run_id` artifacts into the DB
4. switch frontend from scanning files to reading daily views

This keeps today simple and makes long-term maintenance possible.
