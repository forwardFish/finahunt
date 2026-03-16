from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Any

import requests


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
    )
}


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
) -> dict[str, Any]:
    raw_documents: list[dict[str, Any]] = []
    execution_log: list[dict[str, Any]] = []

    for source in sources:
        parser_key = source.get("field_contract", {}).get("parser_key", "")
        try:
            if parser_key == "cls_telegraph_html":
                documents = _fetch_cls_telegraph(source, max_items=max_items_per_source, timeout=timeout)
            elif parser_key == "jiuyangongshe_live_html":
                documents = _fetch_jiuyangongshe_live(source, max_items=max_items_per_source, timeout=timeout)
            else:
                execution_log.append(
                    {
                        "source_id": source["source_id"],
                        "status": "skipped",
                        "reason": f"unsupported_connector:{parser_key}",
                    }
                )
                continue

            raw_documents.extend(documents)
            execution_log.append(
                {
                    "source_id": source["source_id"],
                    "status": "success",
                    "count": len(documents),
                }
            )
        except Exception as exc:
            execution_log.append(
                {
                    "source_id": source["source_id"],
                    "status": "failed",
                    "reason": str(exc),
                }
            )

    return {
        "raw_documents": raw_documents,
        "execution_log": execution_log,
    }


def _fetch_text(url: str, *, timeout: int) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def _extract_json_array_by_key(html: str, key: str) -> list[dict[str, Any]]:
    marker = f'{key}":['
    idx = html.find(marker)
    if idx == -1:
        raise ValueError(f"marker_not_found:{key}")
    start = idx + len(marker) - 1
    depth = 0
    end = None
    for index in range(start, len(html)):
        char = html[index]
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise ValueError(f"array_not_closed:{key}")
    return json.loads(html[start:end])


def _cls_item_to_raw(source: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    content = str(item.get("content") or item.get("brief") or "").strip()
    title = str(item.get("title") or content[:40] or "财联社电报").strip()
    published_at = _normalize_timestamp(str(item.get("ctime") or item.get("modified_time") or ""))
    share_url = item.get("shareurl") or source["base_url"]
    stock_list = item.get("stock_list") or []
    plate_list = item.get("plate_list") or []
    doc_seed = f"cls-{item.get('id') or title}-{published_at}"

    return {
        "document_id": _hash_id(doc_seed, prefix="raw"),
        "source_id": source["source_id"],
        "title": title,
        "summary": _summarize(content),
        "published_at": published_at,
        "url": share_url,
        "source_name": source["source_name"],
        "content_text": content,
        "evidence_snippet": content[:160],
        "source_type": source["channel_type"],
        "tags": ["telegraph", "fast_feed"],
        "metadata": {
            "brief": item.get("brief", ""),
            "stock_list": stock_list,
            "plate_list": plate_list,
            "reading_num": item.get("reading_num", 0),
            "parser_key": source.get("field_contract", {}).get("parser_key", ""),
        },
    }


def _fetch_cls_telegraph(source: dict[str, Any], *, max_items: int, timeout: int) -> list[dict[str, Any]]:
    html = _fetch_text(source["base_url"], timeout=timeout)
    items = _extract_json_array_by_key(html, "telegraphList")
    documents = [_cls_item_to_raw(source, item) for item in items[:max_items]]
    return documents


def _decode_js_string(value: str) -> str:
    return (
        value.replace("\\u002F", "/")
        .replace("\\n", " ")
        .replace("\\t", " ")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .strip()
    )


def _fetch_jiuyangongshe_live(source: dict[str, Any], *, max_items: int, timeout: int) -> list[dict[str, Any]]:
    html = _fetch_text(source["base_url"], timeout=timeout)
    pattern = re.compile(
        r'article_id:"(?P<article_id>[^"]+)".*?'
        r'title:"(?P<title>[^"]*)".*?'
        r'create_time:"(?P<create_time>[^"]+)".*?'
        r'content:"(?P<content>.*?)",user:\{',
        re.S,
    )
    documents: list[dict[str, Any]] = []
    for match in pattern.finditer(html):
        article_id = match.group("article_id")
        title = _decode_js_string(match.group("title"))
        content = _decode_js_string(match.group("content"))
        published_at = _normalize_timestamp(match.group("create_time"))
        documents.append(
            {
                "document_id": _hash_id(f"jygs-{article_id}-{published_at}", prefix="raw"),
                "source_id": source["source_id"],
                "title": title or content[:40] or "韭研公社短文",
                "summary": _summarize(content),
                "published_at": published_at,
                "url": f"{source['base_url']}#{article_id}",
                "source_name": source["source_name"],
                "content_text": content,
                "evidence_snippet": content[:160],
                "source_type": source["channel_type"],
                "tags": ["community", "live"],
                "metadata": {
                    "article_id": article_id,
                    "parser_key": source.get("field_contract", {}).get("parser_key", ""),
                },
            }
        )
        if len(documents) >= max_items:
            break
    return documents


def _normalize_timestamp(value: str) -> str:
    value = value.strip()
    if not value:
        return datetime.now(UTC).isoformat()
    if value.isdigit():
        if len(value) >= 13:
            return datetime.fromtimestamp(int(value) / 1000, tz=UTC).isoformat()
        return datetime.fromtimestamp(int(value), tz=UTC).isoformat()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=UTC).isoformat()
        except ValueError:
            continue
    return value


def _hash_id(seed: str, *, prefix: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _summarize(content: str, limit: int = 140) -> str:
    compact = re.sub(r"\s+", " ", content).strip()
    return compact[:limit]
