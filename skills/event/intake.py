from __future__ import annotations

from typing import Any


SOURCE_PRIORITY_BASE = {"P0": 34.0, "P1": 22.0, "P2": 10.0}

CATALYST_KEYWORD_GROUPS = {
    "policy": ["政策", "规划", "征求意见", "试点", "专项行动", "指导意见", "工信部", "证监会", "发改委"],
    "announcement": ["公告", "披露", "公告称", "提示性公告"],
    "order": ["订单", "中标", "签约", "合作", "量产", "落地"],
    "product": ["发布", "新品", "突破", "首创", "商用", "验证"],
    "domestic_substitution": ["国产替代", "自主可控", "进口替代", "本土供应"],
    "reignited_theme": ["再度活跃", "重新发酵", "重估", "二波", "再提"],
    "industry_cycle": ["涨价", "景气", "供需改善", "渗透率", "扩产"],
}

NOISE_KEYWORDS = ["情绪", "热议", "段子", "吹票", "抄底", "冲鸭", "看图", "闲聊", "唠嗑"]

FOLLOW_UP_HINTS = ["持续", "继续", "推进", "落地", "扩产", "试点", "排产", "窗口期"]


def scout_early_catalyst_inputs(
    documents: list[dict[str, Any]],
    registry_map: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []

    for document in documents:
        score, clue_types, reasons = _score_document(document, registry_map.get(str(document.get("source_id", "")), {}))
        priority = str(registry_map.get(str(document.get("source_id", "")), {}).get("discovery_priority", "P1"))
        role = str(registry_map.get(str(document.get("source_id", "")), {}).get("discovery_role", "general_signal"))

        enriched = {
            **document,
            "metadata": {
                **dict(document.get("metadata", {})),
                "source_priority": priority,
                "discovery_role": role,
                "catalyst_clue_score": round(score, 2),
                "catalyst_clue_types": clue_types,
                "scout_reason": reasons,
                "is_early_catalyst_candidate": score >= 26,
            },
        }

        if score >= 26:
            candidates.append(enriched)
        else:
            dropped.append(
                {
                    "document_id": document.get("document_id", ""),
                    "source_id": document.get("source_id", ""),
                    "title": document.get("title", ""),
                    "source_priority": priority,
                    "catalyst_clue_score": round(score, 2),
                    "scout_reason": reasons or ["insufficient_catalyst_clues"],
                }
            )

    candidates.sort(
        key=lambda item: (
            float(item.get("metadata", {}).get("catalyst_clue_score", 0.0) or 0.0),
            str(item.get("published_at", "")),
        ),
        reverse=True,
    )
    return {"candidates": candidates, "dropped": dropped}


def derive_catalyst_boundary(
    related_themes: list[str],
    related_industries: list[str],
    linked_assets: list[dict[str, Any]],
    impact_scope: str,
) -> str:
    if impact_scope == "market":
        return "market"
    if related_themes:
        return "theme"
    if related_industries:
        return "industry"
    stock_assets = [item for item in linked_assets if item.get("asset_type") == "stock"]
    if stock_assets:
        return "stock"
    return "unknown"


def derive_continuity_hint(text: str, event_type: str, source_priority: str) -> str:
    lowered = text.lower()
    if event_type == "老题材重新激活" or any(keyword in text for keyword in CATALYST_KEYWORD_GROUPS["reignited_theme"]):
        return "reignited"
    if source_priority == "P0" or any(keyword in text for keyword in FOLLOW_UP_HINTS):
        return "developing"
    if lowered:
        return "one_off"
    return "unknown"


def _score_document(document: dict[str, Any], source_entry: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    text = " ".join(
        str(document.get(field, "") or "")
        for field in ("title", "summary", "content_text")
    ).strip()
    metadata = dict(document.get("metadata", {}))
    priority = str(source_entry.get("discovery_priority", "P1"))
    score = SOURCE_PRIORITY_BASE.get(priority, 16.0)
    clue_types: list[str] = []
    reasons: list[str] = [f"priority_{priority.lower()}"]

    for clue_type, keywords in CATALYST_KEYWORD_GROUPS.items():
        hit_count = sum(1 for keyword in keywords if keyword in text)
        if hit_count <= 0:
            continue
        clue_types.append(clue_type)
        score += min(18.0, 8.0 + hit_count * 3.0)
        reasons.append(f"{clue_type}_hit")

    if metadata.get("stock_list") or metadata.get("stocks"):
        score += 8.0
        reasons.append("stock_reference")
    if metadata.get("plate_list"):
        score += 6.0
        reasons.append("theme_reference")
    if document.get("published_at"):
        score += 4.0
        reasons.append("timed_signal")

    noise_hits = sum(1 for keyword in NOISE_KEYWORDS if keyword in text)
    if noise_hits:
        score -= min(20.0, noise_hits * 6.0)
        reasons.append("discussion_noise")

    if not clue_types and priority != "P0":
        score -= 8.0
        reasons.append("no_hard_catalyst")

    return score, clue_types, reasons
