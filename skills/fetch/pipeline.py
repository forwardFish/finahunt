from __future__ import annotations

import asyncio
from typing import Any

from packages.utils import load_yaml, now_iso
from skills.fetch.adapters import ADAPTERS
from skills.fetch.models import RawContent
from skills.fetch.playwright_runtime import PlaywrightFetcher
from skills.fetch.storage import RawContentRepository


async def crawl_public_page_sources(
    sources: list[dict[str, Any]],
    *,
    max_items_per_source: int,
    timeout: int,
    run_id: str,
) -> dict[str, Any]:
    fetch_profiles = load_yaml("config/rules/source_fetch_profiles.yaml")
    defaults = fetch_profiles.get("defaults", {})
    headless = bool(defaults.get("headless", True))
    timeout_ms = int(defaults.get("timeout_ms", timeout * 1000))
    repository = RawContentRepository()
    all_raw_contents: list[RawContent] = []
    execution_log: list[dict[str, Any]] = []

    async with PlaywrightFetcher(headless=headless, timeout_ms=timeout_ms) as fetcher:
        for source in sources:
            parser_key = source.get("field_contract", {}).get("parser_key", "")
            adapter_cls = ADAPTERS.get(parser_key)
            profile = fetch_profiles.get("sources", {}).get(source["source_id"], {})
            if adapter_cls is None or not profile:
                execution_log.append(
                    {
                        "source_id": source["source_id"],
                        "status": "skipped",
                        "reason": f"unsupported_adapter:{parser_key}",
                    }
                )
                continue

            adapter = adapter_cls(source, profile)
            rate_limit_seconds = float(profile.get("rate_limit_seconds", defaults.get("rate_limit_seconds", 1.0)))
            retry_count = int(profile.get("retry_count", defaults.get("retry_count", 2)))
            detail_retry_count = int(profile.get("detail_retry_count", defaults.get("detail_retry_count", 1)))
            wait_until = str(profile.get("wait_until", defaults.get("wait_until", "networkidle")))

            try:
                list_snapshot = await fetcher.fetch_with_retry(
                    lambda: fetcher.fetch_snapshot(
                        adapter.list_url,
                        wait_until=wait_until,
                        rate_limit_seconds=rate_limit_seconds,
                    ),
                    retry_count=retry_count,
                )
                discovered = adapter.parse_list(list_snapshot, max_items=max_items_per_source)
                raw_contents: list[RawContent] = []
                for item in discovered:
                    detail_mode = profile.get("detail_mode", "detail_page")
                    detail_snapshot = None
                    if detail_mode != "inline_fallback":
                        try:
                            detail_snapshot = await fetcher.fetch_with_retry(
                                lambda url=item.detail_url: fetcher.fetch_snapshot(
                                    url,
                                    wait_until=wait_until,
                                    rate_limit_seconds=rate_limit_seconds,
                                ),
                                retry_count=detail_retry_count,
                            )
                        except Exception:
                            detail_snapshot = None
                    raw_contents.append(await adapter.build_raw_content(item, detail_snapshot))

                fresh_contents, skipped_count = repository.filter_incremental(source["source_id"], raw_contents)
                all_raw_contents.extend(fresh_contents)
                execution_log.append(
                    {
                        "source_id": source["source_id"],
                        "status": "success",
                        "discovered_count": len(discovered),
                        "stored_count": len(fresh_contents),
                        "skipped_duplicates": skipped_count,
                    }
                )
            except Exception as exc:  # pragma: no cover - network/runtime variability
                execution_log.append({"source_id": source["source_id"], "status": "failed", "reason": str(exc)})

    storage_summary = repository.store_batch(run_id, all_raw_contents)
    return {
        "raw_contents": [item.model_dump(mode="json") for item in all_raw_contents],
        "execution_log": execution_log,
        "storage_summary": storage_summary,
        "fetched_at": now_iso(),
    }


def crawl_public_page_sources_sync(
    sources: list[dict[str, Any]],
    *,
    max_items_per_source: int,
    timeout: int,
    run_id: str,
) -> dict[str, Any]:
    return asyncio.run(
        crawl_public_page_sources(
            sources,
            max_items_per_source=max_items_per_source,
            timeout=timeout,
            run_id=run_id,
        )
    )
