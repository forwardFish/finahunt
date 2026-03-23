# Finahunt Sprint 3 Linkage And Ranking Summary

## Scope

This handoff closes `Sprint 3 关联关系与用户排序` for `finahunt`:
- `S3-001` 事件与题材时间线
- `S3-002` 观察池对象关联
- `S3-003` 用户相关度评分
- `S3-004` 排序结果流

## What Changed

- Added a new runtime relevance module at `skills/event/relevance.py`.
- Upgraded `agents/runtime/relevance_ranking/agent.py` from simple event sorting to a composite ranking stage that now emits:
  - `ranked_events`
  - `event_theme_timeline`
  - `watchlist_asset_linkage`
  - `relevance_scored_results`
  - `ranked_result_feed`
- Extended warehouse persistence and runtime audit counters to include the new Sprint 3 artifacts.
- Added schema contracts for timeline nodes, watchlist linkage records, and ranked feed items.
- Added dedicated unit coverage plus new integration assertions for the Sprint 3 outputs.

## Validation

- Full test suite: `python -m pytest -q`
  - Result: `31 passed`
- Norm gate: `python tools/gate_check/validate_norms.py`
  - Result: `passed=true`
- Deterministic runtime sample:
  - `run_id`: `run-b55ca70144d8`
  - `artifact_dir`: `workspace/artifacts/runtime/run-b55ca70144d8`
  - `timeline_entries`: `10`
  - `watchlist_hits`: `2`
  - `ranked_feed_count`: `3`
  - `top_ranked_theme`: `算力`

## Runtime Artifacts

- `workspace/artifacts/runtime/run-b55ca70144d8/event_theme_timeline.json`
- `workspace/artifacts/runtime/run-b55ca70144d8/watchlist_asset_linkage.json`
- `workspace/artifacts/runtime/run-b55ca70144d8/relevance_scored_results.json`
- `workspace/artifacts/runtime/run-b55ca70144d8/ranked_result_feed.json`

## Registry Updates

- `tasks/story_status_registry.json` now marks `S3-001` through `S3-004` as `done`.
- `tasks/story_acceptance_reviews.json` now includes formal approvals for `S3-001` through `S3-004`.
- Delivery reports were added under `docs/05_交付/sprint_3_关联关系与用户排序/`.

## Next Best Step

Sprint 4 is now the next unfinished backlog area for `finahunt`.
