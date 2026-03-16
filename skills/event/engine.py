from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any


EVENT_TYPE_RULES = {
    "policy": ["政策", "征求意见", "发改委", "证监会", "工信部", "国务院"],
    "earnings": ["业绩", "预增", "净利润", "快报", "扭亏"],
    "industry": ["中标", "订单", "量产", "合作", "新品", "签约"],
    "capital": ["龙虎榜", "回购", "增持", "减持", "资金流入"],
    "market_movement": ["涨停", "跌停", "异动", "大涨", "大跌"],
}


def detect_event_type(text: str) -> str:
    for event_type, keywords in EVENT_TYPE_RULES.items():
        if any(keyword in text for keyword in keywords):
            return event_type
    return "information_update"


def detect_themes(text: str, theme_rules: dict[str, list[str]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for theme_name, keywords in theme_rules.items():
        hit_keywords = [keyword for keyword in keywords if keyword in text]
        if hit_keywords:
            matches.append(
                {
                    "theme": theme_name,
                    "evidence": hit_keywords[:3],
                }
            )
    return matches


def classify_catalyst(text: str, catalyst_rules: dict[str, Any], source_name: str) -> dict[str, str]:
    for catalyst_type, payload in catalyst_rules.items():
        keywords = payload.get("keywords", [])
        if any(keyword in text for keyword in keywords):
            strength_keywords = payload.get("strength_keywords", {})
            if any(keyword in text for keyword in strength_keywords.get("high", [])):
                strength = "high"
            elif any(keyword in text for keyword in strength_keywords.get("medium", [])):
                strength = "medium"
            else:
                strength = "low"
            return {
                "type": catalyst_type,
                "strength": strength,
                "reason": f"{source_name} 命中 {catalyst_type} 规则",
            }
    return {
        "type": "unknown",
        "strength": "unknown",
        "reason": "未命中明确催化规则",
    }


def extract_symbol_candidates(text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
    linked_assets: list[dict[str, Any]] = []
    seen: set[str] = set()

    for item in metadata.get("stock_list", []) or []:
        code = item.get("secu_code") or item.get("code") or item.get("symbol")
        name = item.get("secu_name") or item.get("name") or code
        if code and code not in seen:
            seen.add(code)
            linked_assets.append({"asset_type": "stock", "asset_id": code, "asset_name": name, "relation": "direct"})

    for item in metadata.get("plate_list", []) or []:
        name = item.get("plate_name") or item.get("name")
        if name and name not in seen:
            seen.add(name)
            linked_assets.append({"asset_type": "sector", "asset_id": name, "asset_name": name, "relation": "direct"})

    for code in re.findall(r"\b\d{6}\.(?:SH|SZ)\b", text):
        if code not in seen:
            seen.add(code)
            linked_assets.append({"asset_type": "stock", "asset_id": code, "asset_name": code, "relation": "weak"})

    return linked_assets


def unify_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for event in events:
        event_time = event.get("event_time", "")[:10]
        fingerprint = f"{event.get('event_type','')}|{event.get('title','')[:30]}|{event_time}"
        canonical_key = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()[:16]
        if canonical_key not in grouped:
            grouped[canonical_key] = {
                **event,
                "canonical_key": canonical_key,
                "source_refs": list(event.get("source_refs", [])),
                "evidence_refs": list(event.get("evidence_refs", [])),
                "linked_assets": list(event.get("linked_assets", [])),
            }
            continue

        current = grouped[canonical_key]
        current["source_refs"] = sorted(set(current["source_refs"] + list(event.get("source_refs", []))))
        current["evidence_refs"] = sorted(set(current["evidence_refs"] + list(event.get("evidence_refs", []))))
        current["linked_assets"] = _merge_assets(current["linked_assets"], event.get("linked_assets", []))
        current["metadata"] = {
            **current.get("metadata", {}),
            "merged_count": current.get("metadata", {}).get("merged_count", 1) + 1,
        }
        current["status"] = "VERIFIED" if len(current["source_refs"]) > 1 else current.get("status", "NEW")
    return list(grouped.values())


def rank_events_for_user(events: list[dict[str, Any]], user_profile: dict[str, Any]) -> list[dict[str, Any]]:
    watchlist_symbols = set(user_profile.get("watchlist_symbols", []))
    watchlist_themes = set(user_profile.get("watchlist_themes", []))
    ranked: list[dict[str, Any]] = []

    for event in events:
        score = 50.0
        reasons: list[str] = []
        if event.get("catalyst_strength") == "high":
            score += 25
            reasons.append("高强度催化")
        elif event.get("catalyst_strength") == "medium":
            score += 15
            reasons.append("中强度催化")
        elif event.get("catalyst_strength") == "low":
            score += 5
            reasons.append("弱催化")
        else:
            score -= 10

        source_count = len(event.get("source_refs", []))
        score += min(source_count * 5, 15)
        if source_count > 1:
            reasons.append("多来源交叉出现")

        linked_ids = {item.get("asset_id") for item in event.get("linked_assets", [])}
        if watchlist_symbols & linked_ids:
            score += 20
            reasons.append("命中自选股")

        theme_tags = set(event.get("theme_tags", []))
        if watchlist_themes & theme_tags:
            score += 10
            reasons.append("命中关注题材")
        elif theme_tags:
            score += 4
            reasons.append("存在题材线索")
        else:
            score -= 5

        if event.get("linked_assets"):
            score += 6
            reasons.append("存在个股/板块关联")
        else:
            score -= 5

        freshness_bonus = _freshness_bonus(event.get("event_time", ""))
        score += freshness_bonus
        if freshness_bonus > 0:
            reasons.append("时效性较高")

        ranked.append(
            {
                **event,
                "relevance_score": round(score, 2),
                "relevance_reason": "；".join(reasons) or "默认排序",
            }
        )

    return sorted(ranked, key=lambda item: item.get("relevance_score", 0.0), reverse=True)


def build_daily_review(ranked_events: list[dict[str, Any]]) -> dict[str, Any]:
    prioritized = [
        item
        for item in ranked_events
        if item.get("catalyst_type") != "unknown" or item.get("theme_tags") or item.get("linked_assets")
    ]
    top_events = (prioritized or ranked_events)[:5]
    focus_cards = [
        {
            "event_id": item["event_id"],
            "title": item["title"],
            "themes": item.get("theme_tags", []),
            "catalyst_type": item.get("catalyst_type", ""),
            "catalyst_strength": item.get("catalyst_strength", ""),
            "relevance_score": item.get("relevance_score", 0.0),
            "source_refs": item.get("source_refs", []),
            "risk_notice": "仅供研究，不构成投资建议。",
        }
        for item in top_events
    ]

    return {
        "today_focus_page": focus_cards,
        "watchlist_event_page": [
            {
                "event_id": item["event_id"],
                "title": item["title"],
                "linked_assets": item.get("linked_assets", []),
                "relevance_reason": item.get("relevance_reason", ""),
            }
            for item in ranked_events[:10]
        ],
        "daily_review_report": {
            "generated_at": datetime.now(UTC).isoformat(),
            "highlight_count": len(top_events),
            "summary": [item["title"] for item in top_events],
            "risk_notice": "风险提示：以上结果基于公开信息的客观抽取和规则排序，不构成投资建议。",
        },
    }


def _merge_assets(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = {(item.get("asset_type"), item.get("asset_id")): item for item in existing}
    for item in incoming:
        key = (item.get("asset_type"), item.get("asset_id"))
        if key not in merged:
            merged[key] = item
    return list(merged.values())


def _freshness_bonus(event_time: str) -> float:
    if not event_time:
        return 0.0
    try:
        dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
        age_hours = (datetime.now(UTC) - dt.astimezone(UTC)).total_seconds() / 3600
        if age_hours <= 6:
            return 10
        if age_hours <= 24:
            return 5
    except ValueError:
        return 0.0
    return 0.0
