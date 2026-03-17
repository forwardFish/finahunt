from __future__ import annotations

import hashlib
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from skills.event.engine import most_common_terms


def aggregate_theme_candidates(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for event in events:
        theme_names = list(dict.fromkeys(event.get("theme_tags", []) or event.get("related_themes", [])))
        if not theme_names:
            continue

        for theme_name in theme_names:
            candidate = grouped.setdefault(
                theme_name,
                {
                    "cluster_id": f"cluster-{hashlib.sha256(theme_name.encode('utf-8')).hexdigest()[:10]}",
                    "theme_candidate_id": f"theme-{hashlib.sha256(theme_name.encode('utf-8')).hexdigest()[:10]}",
                    "theme_name": theme_name,
                    "supporting_signals": [],
                    "source_refs": set(),
                    "evidence_refs": set(),
                    "linked_assets": {},
                    "catalyst_types": set(),
                    "event_types": set(),
                    "high_strength_catalyst_count": 0,
                    "latest_event_time": "",
                    "earliest_event_time": "",
                    "candidate_stocks": {},
                    "narrative_terms": [],
                },
            )

            signal = {
                "event_id": event.get("event_id", ""),
                "title": event.get("title", ""),
                "summary": event.get("summary", ""),
                "event_subject": event.get("event_subject", ""),
                "event_type": event.get("event_type", ""),
                "event_time": event.get("event_time", ""),
                "impact_scope": event.get("impact_scope", "unknown"),
                "impact_direction": event.get("impact_direction", "neutral"),
                "catalyst_type": event.get("catalyst_type", "unknown"),
                "catalyst_strength": event.get("catalyst_strength", "unknown"),
                "source_refs": list(event.get("source_refs", [])),
                "evidence_refs": list(event.get("evidence_refs", [])),
            }
            candidate["supporting_signals"].append(signal)
            candidate["source_refs"].update(event.get("source_refs", []))
            candidate["evidence_refs"].update(event.get("evidence_refs", []))
            candidate["catalyst_types"].add(event.get("catalyst_type", "unknown"))
            candidate["event_types"].add(event.get("event_type", "信息更新"))
            candidate["narrative_terms"].extend(
                event.get("related_themes", [])
                + event.get("related_industries", [])
                + event.get("involved_products", [])
                + event.get("involved_technologies", [])
                + event.get("involved_policies", [])
            )
            if event.get("catalyst_strength") == "high":
                candidate["high_strength_catalyst_count"] += 1

            for asset in event.get("linked_assets", []):
                key = f"{asset.get('asset_type')}::{asset.get('asset_id')}"
                candidate["linked_assets"][key] = asset

            for stock_link in event.get("candidate_stock_links", []):
                if stock_link.get("theme_name") != theme_name:
                    continue
                key = stock_link.get("stock_code", "")
                if not key:
                    continue
                entry = candidate["candidate_stocks"].setdefault(
                    key,
                    {
                        "stock_code": key,
                        "stock_name": stock_link.get("stock_name", key),
                        "scores": [],
                        "breakdowns": [],
                        "evidence": [],
                        "risk_flags": set(),
                        "event_ids": set(),
                        "direct_signal_count": 0,
                    },
                )
                entry["scores"].append(float(stock_link.get("candidate_purity_score", 0.0) or 0.0))
                entry["breakdowns"].append(stock_link.get("purity_breakdown", {}))
                entry["evidence"].extend(stock_link.get("evidence", []))
                entry["risk_flags"].update(stock_link.get("risk_flags", []))
                entry["event_ids"].add(stock_link.get("event_id", ""))
                if stock_link.get("relation") == "direct":
                    entry["direct_signal_count"] += 1

            event_time = event.get("event_time", "")
            if event_time:
                if not candidate["latest_event_time"] or event_time > candidate["latest_event_time"]:
                    candidate["latest_event_time"] = event_time
                if not candidate["earliest_event_time"] or event_time < candidate["earliest_event_time"]:
                    candidate["earliest_event_time"] = event_time

    results: list[dict[str, Any]] = []
    for _, candidate in grouped.items():
        supporting_signals = sorted(
            candidate["supporting_signals"],
            key=lambda item: (item.get("event_time", ""), _strength_rank(item.get("catalyst_strength", "unknown"))),
            reverse=True,
        )
        candidate_stocks = _build_candidate_stocks(candidate["candidate_stocks"])
        related_stock_count = len(candidate_stocks)
        signal_count = len(supporting_signals)
        source_count = len(candidate["source_refs"])
        heat_score = _calculate_heat_score(signal_count, source_count, related_stock_count, candidate["latest_event_time"])
        catalyst_score = _calculate_catalyst_score(
            supporting_signals,
            candidate["high_strength_catalyst_count"],
            source_count,
        )
        continuity_score = _calculate_continuity_score(
            signal_count,
            source_count,
            len(candidate["event_types"]),
            candidate["earliest_event_time"],
            candidate["latest_event_time"],
        )
        fermentation_score = round(heat_score * 0.38 + catalyst_score * 0.34 + continuity_score * 0.28, 2)
        core_narrative = _build_core_narrative(candidate["theme_name"], supporting_signals, candidate["narrative_terms"])

        results.append(
            {
                "cluster_id": candidate["cluster_id"],
                "theme_candidate_id": candidate["theme_candidate_id"],
                "theme_name": candidate["theme_name"],
                "core_narrative": core_narrative,
                "first_seen_time": candidate["earliest_event_time"],
                "latest_seen_time": candidate["latest_event_time"],
                "supporting_signals": supporting_signals,
                "signal_count": signal_count,
                "related_events_count": signal_count,
                "source_count": source_count,
                "source_refs": sorted(candidate["source_refs"]),
                "evidence_refs": sorted(candidate["evidence_refs"]),
                "linked_assets": list(candidate["linked_assets"].values()),
                "linked_asset_count": len(candidate["linked_assets"]),
                "related_stock_count": related_stock_count,
                "catalyst_types": sorted(candidate["catalyst_types"]),
                "high_strength_catalyst_count": candidate["high_strength_catalyst_count"],
                "heat_score": heat_score,
                "catalyst_score": catalyst_score,
                "continuity_score": continuity_score,
                "fermentation_score": fermentation_score,
                "candidate_stocks": candidate_stocks,
                "latest_event_time": candidate["latest_event_time"],
                "earliest_event_time": candidate["earliest_event_time"],
            }
        )

    return sorted(results, key=lambda item: (item["fermentation_score"], item["signal_count"]), reverse=True)


def build_structured_result_cards(theme_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for candidate in theme_candidates:
        top_signals = candidate.get("supporting_signals", [])[:3]
        cards.append(
            {
                "card_id": f"card-{candidate['theme_candidate_id']}",
                "cluster_id": candidate["cluster_id"],
                "theme_name": candidate["theme_name"],
                "core_narrative": candidate.get("core_narrative", ""),
                "catalyst_summary": _build_catalyst_summary(candidate),
                "strength_level": _derive_strength_level(candidate),
                "timeliness_level": _derive_timeliness_level(candidate.get("latest_event_time", "")),
                "heat_score": candidate.get("heat_score", 0.0),
                "catalyst_score": candidate.get("catalyst_score", 0.0),
                "continuity_score": candidate.get("continuity_score", 0.0),
                "fermentation_score": candidate.get("fermentation_score", 0.0),
                "top_evidence": [
                    {
                        "event_id": signal.get("event_id", ""),
                        "title": signal.get("title", ""),
                        "summary": signal.get("summary", ""),
                        "event_subject": signal.get("event_subject", ""),
                        "event_time": signal.get("event_time", ""),
                    }
                    for signal in top_signals
                ],
                "candidate_stocks": candidate.get("candidate_stocks", [])[:5],
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

        velocity_score = min(100.0, candidate.get("heat_score", 0.0) * 0.55 + recent_6h * 10 + recent_24h * 5)
        acceleration_raw = recent_6h - max(recent_24h - recent_6h, 0)
        acceleration_score = max(0.0, min(100.0, 35 + acceleration_raw * 18 + high_strength * 10))
        breadth_score = min(100.0, linked_asset_count * 12 + source_count * 10)
        theme_heat_score = round(
            velocity_score * 0.45 + acceleration_score * 0.25 + breadth_score * 0.15 + candidate.get("fermentation_score", 0.0) * 0.15,
            2,
        )

        snapshots.append(
            {
                "theme_name": candidate["theme_name"],
                "cluster_id": candidate["cluster_id"],
                "theme_candidate_id": candidate["theme_candidate_id"],
                "window": {"hours": 24},
                "mention_count": len(signals),
                "source_count": source_count,
                "high_strength_catalyst_count": high_strength,
                "linked_asset_count": linked_asset_count,
                "velocity_score": round(velocity_score, 2),
                "acceleration_score": round(acceleration_score, 2),
                "theme_heat_score": theme_heat_score,
                "heat_score": candidate.get("heat_score", 0.0),
                "catalyst_score": candidate.get("catalyst_score", 0.0),
                "continuity_score": candidate.get("continuity_score", 0.0),
                "fermentation_score": candidate.get("fermentation_score", 0.0),
                "fermentation_stage": _classify_fermentation_stage(
                    theme_heat_score,
                    source_count,
                    high_strength,
                    candidate.get("continuity_score", 0.0),
                ),
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
                "cluster_id": snapshot["cluster_id"],
                "theme_candidate_id": snapshot["theme_candidate_id"],
                "theme_heat_score": snapshot["theme_heat_score"],
                "fermentation_stage": snapshot["fermentation_stage"],
                "watch_only": watch_only,
                "core_narrative": card.get("core_narrative", ""),
                "catalyst_summary": card["catalyst_summary"],
                "top_evidence": card["top_evidence"],
                "candidate_stocks": card.get("candidate_stocks", []),
                "linked_assets": card["linked_assets"],
                "risk_notice": card["risk_notice"] if not watch_only else f"{card['risk_notice']} Keep as watch-only for now.",
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


def build_low_position_opportunities(
    theme_heat_snapshots: list[dict[str, Any]],
    structured_result_cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    card_by_theme = {card["theme_name"]: card for card in structured_result_cards}
    opportunities: list[dict[str, Any]] = []

    for snapshot in theme_heat_snapshots:
        card = card_by_theme.get(snapshot["theme_name"])
        if not card:
            continue

        score = 0.0
        reasons: list[str] = []
        heat_score = float(snapshot.get("theme_heat_score", 0.0) or 0.0)
        source_count = int(snapshot.get("source_count", 0) or 0)
        high_strength = int(snapshot.get("high_strength_catalyst_count", 0) or 0)
        linked_asset_count = int(snapshot.get("linked_asset_count", 0) or 0)
        continuity_score = float(snapshot.get("continuity_score", 0.0) or 0.0)
        stage = snapshot.get("fermentation_stage", "")
        timeliness = _derive_timeliness_level(snapshot.get("latest_event_time", ""))
        top_candidate_score = float((card.get("candidate_stocks") or [{}])[0].get("candidate_purity_score", 0.0) or 0.0)

        if 35 <= heat_score <= 70:
            score += 22
            reasons.append("theme still sits in early recognition zone")
        elif heat_score < 35:
            score += 10
            reasons.append("theme is early but still lacks enough consensus")
        elif heat_score <= 82:
            score += 6
            reasons.append("theme has started to lift but is not fully crowded")
        else:
            continue

        if stage == "emerging":
            score += 18
            reasons.append("theme is in early fermentation stage")
        elif stage == "watch-only" and (source_count >= 2 or high_strength >= 1):
            score += 9
            reasons.append("theme is still early but has first proofs")
        elif stage == "fermenting" and heat_score <= 68:
            score += 11
            reasons.append("theme just entered active fermentation")

        if timeliness == "high":
            score += 20
            reasons.append("fresh catalyst window")
        elif timeliness == "medium":
            score += 12
            reasons.append("catalyst is still timely")

        if high_strength >= 1:
            score += min(18, 10 + high_strength * 4)
            reasons.append("high-strength catalyst exists")
        elif source_count >= 2:
            score += 8
            reasons.append("cross-source discussion has started")

        if continuity_score >= 55:
            score += 10
            reasons.append("theme has follow-up catalyst continuity")

        if top_candidate_score >= 70:
            score += 14
            reasons.append("candidate mapping already identifies a pure stock")
        elif top_candidate_score >= 60:
            score += 8
            reasons.append("candidate mapping is available")

        if linked_asset_count >= 2:
            score += min(10, linked_asset_count * 3)
        elif linked_asset_count == 1:
            score += 3

        if score < 35:
            continue

        opportunities.append(
            {
                "theme_name": snapshot["theme_name"],
                "cluster_id": snapshot["cluster_id"],
                "theme_candidate_id": snapshot["theme_candidate_id"],
                "low_position_score": round(score, 2),
                "entry_stage": stage or "watch-only",
                "theme_heat_score": heat_score,
                "heat_score": snapshot.get("heat_score", 0.0),
                "catalyst_score": snapshot.get("catalyst_score", 0.0),
                "continuity_score": continuity_score,
                "fermentation_score": snapshot.get("fermentation_score", 0.0),
                "timeliness_level": timeliness,
                "source_count": source_count,
                "high_strength_catalyst_count": high_strength,
                "linked_asset_count": linked_asset_count,
                "low_position_reason": "; ".join(dict.fromkeys(reasons)),
                "core_narrative": card.get("core_narrative", ""),
                "catalyst_summary": card["catalyst_summary"],
                "top_evidence": card["top_evidence"][:2],
                "candidate_stocks": card.get("candidate_stocks", [])[:5],
                "linked_assets": card["linked_assets"],
                "risk_notice": card["risk_notice"],
                "source_refs": card["source_refs"],
            }
        )

    return sorted(opportunities, key=lambda item: item["low_position_score"], reverse=True)


def build_daily_review_from_theme_feed(theme_feed: list[dict[str, Any]]) -> dict[str, Any]:
    top_feed = theme_feed[:5]
    return {
        "today_focus_page": [
            {
                "theme_name": item["theme_name"],
                "theme_heat_score": item["theme_heat_score"],
                "fermentation_stage": item["fermentation_stage"],
                "core_narrative": item.get("core_narrative", ""),
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
            "risk_notice": "Structured results are built from public information clustering and scoring for research use only.",
        },
    }


def _build_candidate_stocks(candidate_stocks: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in candidate_stocks.values():
        breakdown = _average_breakdowns(item["breakdowns"])
        results.append(
            {
                "stock_code": item["stock_code"],
                "stock_name": item["stock_name"],
                "candidate_purity_score": round(sum(item["scores"]) / max(len(item["scores"]), 1), 2),
                "purity_breakdown": breakdown,
                "mention_count": len(item["scores"]),
                "direct_signal_count": item["direct_signal_count"],
                "evidence": list(dict.fromkeys(item["evidence"]))[:6],
                "risk_flags": sorted(item["risk_flags"]),
                "evidence_event_ids": sorted(event_id for event_id in item["event_ids"] if event_id),
            }
        )
    return sorted(
        results,
        key=lambda item: (item["candidate_purity_score"], item["direct_signal_count"], item["mention_count"]),
        reverse=True,
    )


def _average_breakdowns(items: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for item in items:
        for key, value in item.items():
            totals[key] = totals.get(key, 0.0) + float(value or 0.0)
            counts[key] = counts.get(key, 0) + 1
    return {key: round(totals[key] / counts[key], 2) for key in totals}


def _build_core_narrative(theme_name: str, signals: list[dict[str, Any]], narrative_terms: list[str]) -> str:
    subject_terms = [item.get("event_subject", "") for item in signals if item.get("event_subject")]
    leading_subject = most_common_terms(subject_terms, limit=1)
    leading_terms = most_common_terms(narrative_terms, limit=3)
    if leading_subject and leading_terms:
        return f"{theme_name} is clustering around {leading_subject[0]}, with narrative anchors in {' / '.join(leading_terms)}."
    if leading_terms:
        return f"{theme_name} is clustering around {' / '.join(leading_terms)}."
    if signals:
        return f"{theme_name} is clustering around {signals[0].get('title', theme_name)}."
    return f"{theme_name} has formed an early theme cluster."


def _build_catalyst_summary(candidate: dict[str, Any]) -> str:
    catalyst_types = [item for item in candidate.get("catalyst_types", []) if item and item != "unknown"]
    if not catalyst_types:
        return f"{candidate['theme_name']} has early clues, but catalyst type still needs follow-up."
    return f"{candidate['theme_name']} is mainly driven by {' / '.join(catalyst_types[:3])} catalysts."


def _build_risk_notice(candidate: dict[str, Any]) -> str:
    if candidate.get("source_count", 0) < 2:
        return "Evidence still comes from limited sources. Guard against single-source noise."
    if candidate.get("high_strength_catalyst_count", 0) == 0:
        return "There is no high-strength catalyst yet. Keep the theme in observation mode."
    top_stock = (candidate.get("candidate_stocks") or [{}])[0]
    if top_stock.get("risk_flags"):
        return "Candidate mapping is available, but risk flags exist and should be filtered manually."
    return "This is a structured research cluster. Continue tracking follow-up proof and diffusion."


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


def _classify_fermentation_stage(
    theme_heat_score: float,
    source_count: int,
    high_strength: int,
    continuity_score: float,
) -> str:
    if theme_heat_score >= 78 and source_count >= 2 and high_strength >= 1:
        return "hot"
    if theme_heat_score >= 60 or continuity_score >= 65:
        return "fermenting"
    if theme_heat_score >= 45:
        return "emerging"
    return "watch-only"


def _calculate_heat_score(
    signal_count: int,
    source_count: int,
    related_stock_count: int,
    latest_event_time: str,
) -> float:
    recency_bonus = 0.0
    if _derive_timeliness_level(latest_event_time) == "high":
        recency_bonus = 18.0
    elif _derive_timeliness_level(latest_event_time) == "medium":
        recency_bonus = 10.0
    return round(min(100.0, signal_count * 14 + source_count * 12 + related_stock_count * 6 + recency_bonus), 2)


def _calculate_catalyst_score(
    signals: list[dict[str, Any]],
    high_strength_count: int,
    source_count: int,
) -> float:
    medium_strength_count = sum(1 for item in signals if item.get("catalyst_strength") == "medium")
    return round(min(100.0, high_strength_count * 28 + medium_strength_count * 14 + source_count * 8 + 20), 2)


def _calculate_continuity_score(
    signal_count: int,
    source_count: int,
    event_type_count: int,
    earliest_event_time: str,
    latest_event_time: str,
) -> float:
    span_bonus = 0.0
    earliest = _parse_dt(earliest_event_time)
    latest = _parse_dt(latest_event_time)
    if earliest and latest:
        span_hours = max((latest - earliest).total_seconds() / 3600, 0.0)
        if span_hours >= 24:
            span_bonus = 20.0
        elif span_hours >= 6:
            span_bonus = 12.0
        else:
            span_bonus = 6.0
    return round(min(100.0, 20 + signal_count * 8 + source_count * 10 + event_type_count * 7 + span_bonus), 2)


def _strength_rank(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1, "unknown": 0}.get(value, 0)


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None
