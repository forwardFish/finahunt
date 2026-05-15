from __future__ import annotations

import hashlib
import re
from typing import Any


GARBLE_PATTERNS = (
    re.compile(r"[锟�]{2,}"),
    re.compile(r"(?:涓|绱|鏄|浠|寮|€|™|©|‰|œ|€\?)"),
    re.compile(r"[A-Za-z0-9+/]{30,}={0,2}"),
)


def create_source_hash(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("source_id") or ""),
        str(item.get("url") or ""),
        str(item.get("title") or ""),
        str(item.get("published_at") or ""),
        str(item.get("content_text") or "")[:500],
    ]
    text = "|".join(parts).strip()
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def has_garbled_text(text: str) -> bool:
    if not text:
        return False
    if text.count("\ufffd") >= 2:
        return True
    if sum(1 for char in text if ord(char) < 32 and char not in "\n\r\t") > 0:
        return True
    return any(pattern.search(text) for pattern in GARBLE_PATTERNS)


def calculate_truth_score(item: dict[str, Any]) -> int:
    score = 0
    url = str(item.get("url") or "")
    source_name = str(item.get("source_name") or "")
    title = str(item.get("title") or "")
    content_text = str(item.get("content_text") or "")
    published_at = str(item.get("published_at") or "")
    source_hash = str(item.get("source_hash") or create_source_hash(item))
    http_status = item.get("http_status")

    if url:
        score += 15
    if isinstance(http_status, int) and 200 <= http_status < 300:
        score += 15
    if source_name:
        score += 10
    if len(title) >= 8:
        score += 10
    if len(content_text) >= 80:
        score += 20
    if published_at:
        score += 10
    if source_hash:
        score += 10
    if not has_garbled_text(" ".join([title, content_text])):
        score += 10
    return min(score, 100)


def authenticity_status_for_score(score: int) -> str:
    if score >= 90:
        return "trusted"
    if score >= 70:
        return "likely_trusted"
    if score >= 50:
        return "needs_review"
    return "blocked"
