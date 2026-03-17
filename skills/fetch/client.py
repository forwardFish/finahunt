from __future__ import annotations

from typing import Any

from skills.fetch.html import decode_js_string, extract_js_object_by_assignment, extract_json_array_by_key
from skills.fetch.pipeline import crawl_public_page_sources_sync


def build_fetch_plan(source_registry: dict) -> dict:
    return {
        "enabled_sources": [
            source["source_id"]
            for source in source_registry.get("sources", [])
            if source.get("status") == "active"
        ],
        "schedule": source_registry.get("default_schedule", "0 */1 * * *"),
    }


def fetch_documents(
    sources: list[dict[str, Any]],
    *,
    max_items_per_source: int = 10,
    timeout: int = 20,
    run_id: str = "manual-run",
) -> dict[str, Any]:
    pipeline_result = crawl_public_page_sources_sync(
        sources,
        max_items_per_source=max_items_per_source,
        timeout=timeout,
        run_id=run_id,
    )
    raw_contents = pipeline_result["raw_contents"]
    return {
        "raw_documents": [_raw_content_to_raw_news_item(item) for item in raw_contents],
        "execution_log": pipeline_result["execution_log"],
        "storage_summary": pipeline_result["storage_summary"],
    }


def _raw_content_to_raw_news_item(item: dict[str, Any]) -> dict[str, Any]:
    body = str(item.get("body") or "").strip()
    tags = list(item.get("tags") or [])
    metadata = dict(item.get("metadata") or {})
    stocks = metadata.get("stocks") or metadata.get("stock_list") or []
    plates = metadata.get("plate_list") or []
    return {
        "document_id": item["content_id"],
        "source_id": item["source_id"],
        "title": item["title"],
        "summary": body[:140],
        "published_at": item.get("published_at") or item["fetched_at"],
        "url": item["source_url"],
        "source_name": item["site_name"],
        "content_text": body,
        "evidence_snippet": body[:160],
        "source_type": "public_site",
        "tags": tags,
        "metadata": {
            **metadata,
            "stock_list": stocks,
            "plate_list": plates,
            "author": item.get("author", ""),
            "origin_url": item["source_url"],
            "list_url": item["list_url"],
            "fetched_at": item["fetched_at"],
        },
    }


__all__ = [
    "build_fetch_plan",
    "decode_js_string",
    "extract_js_object_by_assignment",
    "extract_json_array_by_key",
    "fetch_documents",
]
