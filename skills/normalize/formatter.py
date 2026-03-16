from __future__ import annotations

import hashlib
import re
from typing import Any


def normalize_document(raw_document: dict[str, Any], quality_policy: dict[str, Any]) -> dict[str, Any]:
    title = _clean_text(raw_document.get("title", ""))
    summary = _clean_text(raw_document.get("summary", ""))
    content = _clean_text(raw_document.get("content_text", ""))
    combined = f"{title} {summary} {content}".strip()

    mentioned_symbols = sorted(set(re.findall(r"\b\d{6}\.(?:SH|SZ)\b", combined)))
    theme_keywords = _match_keywords(
        combined,
        [
            "算力",
            "人工智能",
            "机器人",
            "低空",
            "半导体",
            "新能源",
            "并购",
            "增持",
            "减持",
            "业绩",
            "中标",
            "订单",
        ],
    )

    finance_hits = _match_keywords(combined, quality_policy.get("finance_keywords", []))
    low_signal_hits = _match_keywords(combined, quality_policy.get("low_signal_phrases", []))
    reasons: list[str] = []
    is_effective = True

    if len(title) < quality_policy.get("minimum_title_length", 0):
        reasons.append("title_too_short")
        is_effective = False
    if len(summary or content) < quality_policy.get("minimum_summary_length", 0):
        reasons.append("summary_too_short")
        is_effective = False
    if low_signal_hits:
        reasons.append("low_signal_phrase")
        is_effective = False
    if not (finance_hits or mentioned_symbols or theme_keywords):
        reasons.append("missing_finance_signal")
        is_effective = False

    dedup_basis = _clean_text(f"{title} {summary}") or combined
    dedup_key = hashlib.sha256(dedup_basis.encode("utf-8")).hexdigest()[:16]
    quality_score = _compute_quality_score(finance_hits, mentioned_symbols, theme_keywords, low_signal_hits)

    return {
        "document_id": raw_document.get("document_id", ""),
        "title": title,
        "summary": summary or content[:140],
        "published_at": raw_document.get("published_at", ""),
        "source_name": raw_document.get("source_name", ""),
        "source_url": raw_document.get("url") or raw_document.get("source_url", ""),
        "content_text": content,
        "is_effective": is_effective,
        "filter_reasons": reasons,
        "dedup_key": dedup_key,
        "quality_score": quality_score,
        "mentioned_symbols": mentioned_symbols,
        "theme_hints": theme_keywords,
        "finance_keyword_hits": finance_hits,
        "metadata": raw_document.get("metadata", {}),
    }


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _match_keywords(text: str, keywords: list[str]) -> list[str]:
    return [keyword for keyword in keywords if keyword and keyword in text]


def _compute_quality_score(
    finance_hits: list[str],
    mentioned_symbols: list[str],
    theme_keywords: list[str],
    low_signal_hits: list[str],
) -> float:
    score = 0.4
    score += min(len(finance_hits) * 0.08, 0.24)
    score += min(len(mentioned_symbols) * 0.1, 0.2)
    score += min(len(theme_keywords) * 0.05, 0.15)
    score -= min(len(low_signal_hits) * 0.2, 0.4)
    return max(0.0, min(score, 1.0))
