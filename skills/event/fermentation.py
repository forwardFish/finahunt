from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any


def aggregate_theme_candidates(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for event in events:
        theme_names = list(dict.fromkeys(event.get("theme_tags", [])))
        if not theme_names:
            continue

        for theme_name in theme_names:
            candidate = grouped.setdefault(
                theme_name,
                {
                    "theme_candidate_id": f"theme-{hashlib.sha256(theme_name.encode('utf-8')).hexdigest()[:10]}",
                    "theme_name": theme_name,
                    "supporting_signals": [],
                    "source_refs": set(),
                    "evidence_refs": set(),
                    "linked_assets": {},
                    "catalyst_types": set(),
                    "high_strength_catalyst_count": 0,
                    "latest_event_time": "",
                    "earliest_event_time": "",
                },
            )

            signal = {
                "event_id": event.get("event_id", ""),
                "title": event.get("title", ""),
                "summary": event.get("summary", ""),
                "event_time": event.get("event_time", ""),
                "catalyst_type": event.get("catalyst_type", "unknown"),
                "catalyst_strength": event.get("catalyst_strength", "unknown"),
                "source_refs": list(event.get("source_refs", [])),
                "evidence_refs": list(event.get("evidence_refs", [])),
            }
            candidate["supporting_signals"].append(signal)
            candidate["source_refs"].update(event.get("source_refs", []))
            candidate["evidence_refs"].update(event.get("evidence_refs", []))
            candidate["catalyst_types"].add(event.get("catalyst_type", "unknown"))
            if event.get("catalyst_strength") == "high":
                candidate["high_strength_catalyst_count"] += 1

            for asset in event.get("linked_assets", []):
                key = f"{asset.get('asset_type')}::{asset.get('asset_id')}"
                candidate["linked_assets"][key] = asset

            event_time = event.get("event_time", "")
            if event_time:
                if not candidate["latest_event_time"] or event_time > candidate["latest_event_time"]:
                    candidate["latest_event_time"] = event_time
                if not candidate["earliest_event_time"] or event_time < candidate["earliest_event_time"]:
                    candidate["earliest_event_time"] = event_time

    results: list[dict[str, Any]] = []
    for theme_name, candidate in grouped.items():
        supporting_signals = sorted(
            candidate["supporting_signals"],
            key=lambda item: (item.get("event_time", ""), _strength_rank(item.get("catalyst_strength", "unknown"))),
            reverse=True,
        )
        results.append(
            {
                "theme_candidate_id": candidate["theme_candidate_id"],
                "theme_name": theme_name,
                "supporting_signals": supporting_signals,
                "signal_count": len(supporting_signals),
                "source_count": len(candidate["source_refs"]),
                "source_refs": sorted(candidate["source_refs"]),
                "evidence_refs": sorted(candidate["evidence_refs"]),
                "linked_assets": list(candidate["linked_assets"].values()),
                "linked_asset_count": len(candidate["linked_assets"]),
                "catalyst_types": sorted(candidate["catalyst_types"]),
                "high_strength_catalyst_count": candidate["high_strength_catalyst_count"],
                "latest_event_time": candidate["latest_event_time"],
                "earliest_event_time": candidate["earliest_event_time"],
            }
        )

    return sorted(results, key=lambda item: (item["signal_count"], item["source_count"]), reverse=True)


def build_structured_result_cards(theme_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for candidate in theme_candidates:
        top_signals = candidate.get("supporting_signals", [])[:3]
        cards.append(
            {
                "card_id": f"card-{candidate['theme_candidate_id']}",
                "theme_name": candidate["theme_name"],
                "catalyst_summary": _build_catalyst_summary(candidate),
                "strength_level": _derive_strength_level(candidate),
                "timeliness_level": _derive_timeliness_level(candidate.get("latest_event_time", "")),
                "top_evidence": [
                    {
                        "event_id": signal.get("event_id", ""),
                        "title": signal.get("title", ""),
                        "summary": signal.get("summary", ""),
                        "event_time": signal.get("event_time", ""),
                    }
                    for signal in top_signals
                ],
                "evidence_refs": candidate.get("evidence_refs", []),
                "source_refs": candidate.get("source_refs", []),
                "linked_assets": candidate.get("linked_assets", []),
                "risk_notice": _build_risk_notice(candidate),
                "theme_candidate_id": candidate["theme_candidate_id"],
            }
        )
    return cards


def build_theme_heat_snapshots(theme_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    now = datetime.now(UTC)

    for candidate in theme_candidates:
        signals = candidate.get("supporting_signals", [])
        signal_times = [_parse_dt(signal.get("event_time", "")) for signal in signals]
        recent_6h = sum(1 for dt in signal_times if dt and (now - dt).total_seconds() <= 6 * 3600)
        recent_24h = sum(1 for dt in signal_times if dt and (now - dt).total_seconds() <= 24 * 3600)
        source_count = candidate.get("source_count", 0)
        high_strength = candidate.get("high_strength_catalyst_count", 0)
        linked_asset_count = candidate.get("linked_asset_count", 0)

        velocity_score = min(100.0, recent_6h * 22 + recent_24h * 8 + source_count * 8 + high_strength * 14)
        acceleration_raw = recent_6h - max(recent_24h - recent_6h, 0)
        acceleration_score = max(0.0, min(100.0, 35 + acceleration_raw * 18 + high_strength * 10))
        breadth_score = min(100.0, linked_asset_count * 12 + source_count * 10)
        theme_heat_score = round(velocity_score * 0.45 + acceleration_score * 0.35 + breadth_score * 0.20, 2)

        snapshots.append(
            {
                "theme_name": candidate["theme_name"],
                "theme_candidate_id": candidate["theme_candidate_id"],
                "window": {"hours": 24},
                "mention_count": len(signals),
                "source_count": source_count,
                "high_strength_catalyst_count": high_strength,
                "linked_asset_count": linked_asset_count,
                "velocity_score": round(velocity_score, 2),
                "acceleration_score": round(acceleration_score, 2),
                "theme_heat_score": theme_heat_score,
                "fermentation_stage": _classify_fermentation_stage(theme_heat_score, source_count, high_strength),
                "score_breakdown": {
                    "recent_6h_signals": recent_6h,
                    "recent_24h_signals": recent_24h,
                    "source_count": source_count,
                    "high_strength_catalyst_count": high_strength,
                    "linked_asset_count": linked_asset_count,
                },
                "latest_event_time": candidate.get("latest_event_time", ""),
            }
        )

    return sorted(snapshots, key=lambda item: item["theme_heat_score"], reverse=True)


def build_fermenting_theme_feed(
    theme_heat_snapshots: list[dict[str, Any]],
    structured_result_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    card_by_theme = {card["theme_name"]: card for card in structured_result_cards}
    feed: list[dict[str, Any]] = []

    for snapshot in theme_heat_snapshots:
        card = card_by_theme.get(snapshot["theme_name"])
        if not card:
            continue
        watch_only = snapshot["theme_heat_score"] < 55 or snapshot["source_count"] < 2
        feed.append(
            {
                "theme_name": snapshot["theme_name"],
                "theme_candidate_id": snapshot["theme_candidate_id"],
                "theme_heat_score": snapshot["theme_heat_score"],
                "fermentation_stage": snapshot["fermentation_stage"],
                "watch_only": watch_only,
                "catalyst_summary": card["catalyst_summary"],
                "top_evidence": card["top_evidence"],
                "linked_assets": card["linked_assets"],
                "risk_notice": card["risk_notice"] if not watch_only else f"{card['risk_notice']} 当前仅建议观察，不构成方向确认。",
                "source_refs": card["source_refs"],
            }
        )

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for item in sorted(feed, key=lambda entry: entry["theme_heat_score"], reverse=True):
        if item["theme_name"] in seen:
            continue
        seen.add(item["theme_name"])
        deduped.append(item)
    return deduped


def build_daily_review_from_theme_feed(theme_feed: list[dict[str, Any]]) -> dict[str, Any]:
    top_feed = theme_feed[:5]
    return {
        "today_focus_page": [
            {
                "theme_name": item["theme_name"],
                "theme_heat_score": item["theme_heat_score"],
                "fermentation_stage": item["fermentation_stage"],
                "catalyst_summary": item["catalyst_summary"],
                "risk_notice": item["risk_notice"],
                "linked_assets": item["linked_assets"][:5],
            }
            for item in top_feed
        ],
        "watchlist_event_page": [
            {
                "theme_name": item["theme_name"],
                "top_evidence": item["top_evidence"][:2],
                "watch_only": item["watch_only"],
            }
            for item in theme_feed[:10]
        ],
        "daily_review_report": {
            "generated_at": datetime.now(UTC).isoformat(),
            "highlight_count": len(top_feed),
            "summary": [item["theme_name"] for item in top_feed],
            "risk_notice": "风险提示：结果基于公开信息抽取、聚合与规则评分，仅用于研究和观察，不构成投资建议。",
        },
    }


def _build_catalyst_summary(candidate: dict[str, Any]) -> str:
    catalyst_types = [item for item in candidate.get("catalyst_types", []) if item and item != "unknown"]
    if not catalyst_types:
        return f"{candidate['theme_name']} 当前存在主题线索，但催化类型仍需继续观察。"
    return f"{candidate['theme_name']} 当前主要由 {'、'.join(catalyst_types[:3])} 类型催化驱动。"


def _build_risk_notice(candidate: dict[str, Any]) -> str:
    if candidate.get("source_count", 0) < 2:
        return "当前证据来源较少，需警惕单一来源噪声。"
    if candidate.get("high_strength_catalyst_count", 0) == 0:
        return "当前缺少高强度催化，主题可能仍停留在早期观察阶段。"
    return "当前为结构化研究结果，仍需持续跟踪后续证据和扩散情况。"


def _derive_strength_level(candidate: dict[str, Any]) -> str:
    high_strength = candidate.get("high_strength_catalyst_count", 0)
    signal_count = candidate.get("signal_count", 0)
    if high_strength >= 2 or (high_strength >= 1 and signal_count >= 3):
        return "high"
    if high_strength >= 1 or signal_count >= 2:
        return "medium"
    return "low"


def _derive_timeliness_level(latest_event_time: str) -> str:
    dt = _parse_dt(latest_event_time)
    if not dt:
        return "unknown"
    age_hours = (datetime.now(UTC) - dt).total_seconds() / 3600
    if age_hours <= 6:
        return "high"
    if age_hours <= 24:
        return "medium"
    return "low"


def _classify_fermentation_stage(theme_heat_score: float, source_count: int, high_strength: int) -> str:
    if theme_heat_score >= 75 and source_count >= 2 and high_strength >= 1:
        return "hot"
    if theme_heat_score >= 60:
        return "fermenting"
    if theme_heat_score >= 45:
        return "emerging"
    return "watch-only"


def _strength_rank(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1, "unknown": 0}.get(value, 0)


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None
