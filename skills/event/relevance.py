from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any


def build_event_theme_timeline(
    linked_events: list[dict[str, Any]],
    theme_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    timeline_entries: list[dict[str, Any]] = []

    for event in linked_events:
        timestamp = _select_timestamp(event)
        if not timestamp:
            continue

        theme_names = _theme_names_from_payload(event)
        linked_assets = list(event.get("linked_assets", []))
        source_refs = list(event.get("source_refs", []))
        evidence_refs = list(event.get("evidence_refs", []))
        base_entry = {
            "timestamp": timestamp,
            "theme_name": theme_names[0] if theme_names else "",
            "theme_names": theme_names,
            "event_id": event.get("event_id", ""),
            "cluster_id": "",
            "title": event.get("title", ""),
            "summary": event.get("summary", ""),
            "event_subject": event.get("event_subject", ""),
            "source_refs": source_refs,
            "evidence_refs": evidence_refs,
            "linked_assets": linked_assets,
        }
        timeline_entries.append(
            {
                **base_entry,
                "timeline_id": _timeline_id("event", event.get("event_id", ""), timestamp),
                "node_type": "event",
                "stage": "stock_linkage",
                "node_title": event.get("title", "") or event.get("event_subject", "") or "event",
                "node_summary": event.get("summary", ""),
                "catalyst_type": event.get("catalyst_type", "unknown"),
                "catalyst_strength": event.get("catalyst_strength", "unknown"),
            }
        )

        if event.get("catalyst_type") and event.get("catalyst_type") != "unknown":
            timeline_entries.append(
                {
                    **base_entry,
                    "timeline_id": _timeline_id("catalyst", event.get("event_id", ""), timestamp),
                    "node_type": "catalyst",
                    "stage": "catalyst_classification",
                    "node_title": event.get("title", "") or event.get("event_subject", "") or "catalyst",
                    "node_summary": event.get("relevance_reason", "") or event.get("summary", ""),
                    "catalyst_type": event.get("catalyst_type", "unknown"),
                    "catalyst_strength": event.get("catalyst_strength", "unknown"),
                }
            )

    for candidate in theme_candidates:
        timestamp = candidate.get("latest_seen_time") or candidate.get("latest_event_time") or candidate.get("first_seen_time")
        if not timestamp:
            continue

        theme_name = str(candidate.get("theme_name", "") or "")
        top_signal = (candidate.get("supporting_signals") or [{}])[0]
        timeline_entries.append(
            {
                "timeline_id": _timeline_id("theme_candidate", candidate.get("theme_candidate_id", theme_name), timestamp),
                "node_type": "theme_candidate",
                "stage": "theme_candidate_aggregation",
                "timestamp": timestamp,
                "theme_name": theme_name,
                "theme_names": [theme_name] if theme_name else [],
                "event_id": top_signal.get("event_id", ""),
                "cluster_id": candidate.get("cluster_id", ""),
                "title": candidate.get("theme_name", ""),
                "summary": candidate.get("core_narrative", ""),
                "event_subject": top_signal.get("event_subject", ""),
                "node_title": candidate.get("theme_name", "") or "theme_candidate",
                "node_summary": candidate.get("core_narrative", ""),
                "catalyst_type": next(
                    (
                        signal.get("catalyst_type", "unknown")
                        for signal in candidate.get("supporting_signals", [])
                        if signal.get("catalyst_type") and signal.get("catalyst_type") != "unknown"
                    ),
                    "unknown",
                ),
                "catalyst_strength": _derive_candidate_strength(candidate),
                "source_refs": list(candidate.get("source_refs", [])),
                "evidence_refs": list(candidate.get("evidence_refs", [])),
                "linked_assets": list(candidate.get("linked_assets", [])),
            }
        )

    sorted_entries = sorted(
        timeline_entries,
        key=lambda item: (item.get("timestamp", ""), _timeline_node_rank(item.get("node_type", "event"))),
    )
    theme_timelines = _build_theme_timelines(sorted_entries)
    return {
        "timeline_entries": sorted_entries,
        "theme_timelines": theme_timelines,
        "timeline_summary": {
            "entry_count": len(sorted_entries),
            "theme_count": len(theme_timelines),
            "event_node_count": sum(1 for item in sorted_entries if item.get("node_type") == "event"),
            "candidate_node_count": sum(1 for item in sorted_entries if item.get("node_type") == "theme_candidate"),
        },
    }


def build_watchlist_asset_linkage(
    feed_items: list[dict[str, Any]],
    user_profile: dict[str, Any],
) -> dict[str, Any]:
    watchlist_symbols = {_normalize_stock_code(value) for value in user_profile.get("watchlist_symbols", []) if value}
    watchlist_themes = {str(value).strip() for value in user_profile.get("watchlist_themes", []) if str(value).strip()}
    watchlist_sectors = {str(value).strip() for value in user_profile.get("watchlist_sectors", []) if str(value).strip()}

    linked_results: list[dict[str, Any]] = []
    for item in feed_items:
        matches: list[dict[str, Any]] = []
        theme_name = str(item.get("theme_name", "") or "")
        if theme_name and theme_name in watchlist_themes:
            matches.append(
                {
                    "watch_item_type": "theme",
                    "watch_item_id": theme_name,
                    "watch_item_name": theme_name,
                    "match_target": "theme_name",
                    "match_reason": "theme preference hit",
                }
            )

        for stock in item.get("candidate_stocks", []):
            stock_code = _normalize_stock_code(stock.get("stock_code"))
            if stock_code and stock_code in watchlist_symbols:
                matches.append(
                    {
                        "watch_item_type": "symbol",
                        "watch_item_id": stock_code,
                        "watch_item_name": stock.get("stock_name", stock_code),
                        "match_target": "candidate_stock",
                        "match_reason": "watchlist symbol hit",
                    }
                )

        for asset in item.get("linked_assets", []):
            asset_type = asset.get("asset_type", "")
            asset_id = str(asset.get("asset_id", "") or "")
            asset_name = str(asset.get("asset_name", asset_id) or asset_id)
            if asset_type == "sector" and asset_name in watchlist_sectors:
                matches.append(
                    {
                        "watch_item_type": "sector",
                        "watch_item_id": asset_id or asset_name,
                        "watch_item_name": asset_name,
                        "match_target": "linked_asset",
                        "match_reason": "watchlist sector hit",
                    }
                )
            if asset_type == "theme" and asset_name in watchlist_themes:
                matches.append(
                    {
                        "watch_item_type": "theme",
                        "watch_item_id": asset_id or asset_name,
                        "watch_item_name": asset_name,
                        "match_target": "linked_asset",
                        "match_reason": "theme-linked asset hit",
                    }
                )

        if not matches:
            continue

        deduped_matches = _dedupe_watch_matches(matches)
        linked_results.append(
            {
                "linkage_id": _timeline_id("watch", item.get("theme_candidate_id", theme_name), theme_name or "watch"),
                "theme_candidate_id": item.get("theme_candidate_id", ""),
                "theme_name": theme_name,
                "cluster_id": item.get("cluster_id", ""),
                "watchlist_hits": deduped_matches,
                "watchlist_hit_count": len(deduped_matches),
                "watchlist_match_summary": "; ".join(match["match_reason"] for match in deduped_matches),
                "source_refs": list(item.get("source_refs", [])),
                "top_evidence": list(item.get("top_evidence", []))[:2],
                "candidate_stocks": list(item.get("candidate_stocks", []))[:5],
                "linked_assets": list(item.get("linked_assets", [])),
            }
        )

    return {
        "watchlist_enabled": bool(watchlist_symbols or watchlist_themes or watchlist_sectors),
        "watchlist_symbols": sorted(watchlist_symbols),
        "watchlist_themes": sorted(watchlist_themes),
        "watchlist_sectors": sorted(watchlist_sectors),
        "linked_results": linked_results,
        "summary": {
            "hit_count": len(linked_results),
            "watch_symbol_count": len(watchlist_symbols),
            "watch_theme_count": len(watchlist_themes),
            "watch_sector_count": len(watchlist_sectors),
        },
    }


def build_relevance_scored_results(
    feed_items: list[dict[str, Any]],
    watchlist_asset_linkage: dict[str, Any],
    user_profile: dict[str, Any],
    theme_heat_snapshots: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    linkage_by_candidate = {
        item.get("theme_candidate_id", ""): item for item in watchlist_asset_linkage.get("linked_results", [])
    }
    snapshot_by_candidate = {
        item.get("theme_candidate_id", ""): item for item in theme_heat_snapshots if item.get("theme_candidate_id")
    }
    watchlist_themes = {str(value).strip() for value in user_profile.get("watchlist_themes", []) if str(value).strip()}

    scored_results: list[dict[str, Any]] = []
    for item in feed_items:
        theme_candidate_id = item.get("theme_candidate_id", "")
        snapshot = snapshot_by_candidate.get(theme_candidate_id, {})
        linkage = linkage_by_candidate.get(theme_candidate_id, {})
        top_stock = (item.get("candidate_stocks") or [{}])[0]
        source_count = int(snapshot.get("source_count", len(item.get("source_refs", []))) or 0)
        high_strength = int(snapshot.get("high_strength_catalyst_count", 0) or 0)
        theme_heat_score = float(snapshot.get("theme_heat_score", item.get("theme_heat_score", 0.0)) or 0.0)
        fermentation_score = float(snapshot.get("fermentation_score", 0.0) or 0.0)
        top_purity_score = float(top_stock.get("candidate_purity_score", 0.0) or 0.0)
        timeliness_level = _timeliness_level(snapshot.get("latest_event_time", ""))

        breakdown = {
            "base_score": 20.0,
            "watchlist_score": _watchlist_score(linkage),
            "theme_preference_score": 8.0 if item.get("theme_name", "") in watchlist_themes else 0.0,
            "catalyst_score": min(18.0, high_strength * 8.0 + (8.0 if item.get("fermentation_stage") in {"emerging", "fermenting"} else 4.0)),
            "timeliness_score": {"high": 15.0, "medium": 9.0, "low": 3.0, "unknown": 0.0}[timeliness_level],
            "heat_score": round(min(14.0, theme_heat_score * 0.16), 2),
            "evidence_score": float(min(12, source_count * 4)),
            "asset_fit_score": round(min(10.0, top_purity_score * 0.12), 2),
            "fermentation_score": round(min(8.0, fermentation_score * 0.08), 2),
        }

        relevance_score = round(sum(breakdown.values()), 2)
        reasons: list[str] = []
        if breakdown["watchlist_score"] > 0:
            reasons.append("watchlist hit")
        if breakdown["theme_preference_score"] > 0:
            reasons.append("theme preference hit")
        if high_strength > 0:
            reasons.append("high strength catalyst present")
        if timeliness_level == "high":
            reasons.append("fresh catalyst window")
        if source_count >= 2:
            reasons.append("multi-source confirmation")
        if top_purity_score >= 65:
            reasons.append("clear asset mapping")

        scored_results.append(
            {
                **item,
                "relevance_score": relevance_score,
                "score_breakdown": breakdown,
                "watchlist_hits": list(linkage.get("watchlist_hits", [])),
                "watchlist_hit_count": int(linkage.get("watchlist_hit_count", 0) or 0),
                "timeliness_level": timeliness_level,
                "source_count": source_count,
                "high_strength_catalyst_count": high_strength,
                "top_asset_purity_score": round(top_purity_score, 2),
                "relevance_reason": "; ".join(reasons) or "default ranking",
            }
        )

    return scored_results


def build_ranked_result_feed(
    relevance_scored_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    valid_results = [
        item
        for item in relevance_scored_results
        if item.get("theme_name") and item.get("relevance_score") is not None
    ]
    if relevance_scored_results and not valid_results:
        raise ValueError("ranked result feed requires scorable items with theme_name and relevance_score")

    ranked_items = sorted(
        valid_results,
        key=lambda item: (
            float(item.get("relevance_score", 0.0) or 0.0),
            float(item.get("theme_heat_score", 0.0) or 0.0),
            float(item.get("top_asset_purity_score", 0.0) or 0.0),
        ),
        reverse=True,
    )

    feed: list[dict[str, Any]] = []
    seen_themes: set[str] = set()
    for item in ranked_items:
        theme_name = str(item.get("theme_name", "") or "")
        if not theme_name or theme_name in seen_themes:
            continue
        seen_themes.add(theme_name)
        feed.append(
            {
                "rank_position": len(feed) + 1,
                "theme_candidate_id": item.get("theme_candidate_id", ""),
                "cluster_id": item.get("cluster_id", ""),
                "theme_name": theme_name,
                "relevance_score": item.get("relevance_score", 0.0),
                "relevance_reason": item.get("relevance_reason", ""),
                "score_breakdown": item.get("score_breakdown", {}),
                "core_narrative": item.get("core_narrative", ""),
                "catalyst_summary": item.get("catalyst_summary", ""),
                "fermentation_stage": item.get("fermentation_stage", ""),
                "fermentation_phase": item.get("fermentation_phase", ""),
                "theme_heat_score": item.get("theme_heat_score", 0.0),
                "timeliness_level": item.get("timeliness_level", "unknown"),
                "watchlist_hit_count": item.get("watchlist_hit_count", 0),
                "watchlist_hits": item.get("watchlist_hits", []),
                "top_evidence": list(item.get("top_evidence", []))[:3],
                "candidate_stocks": list(item.get("candidate_stocks", []))[:5],
                "linked_assets": list(item.get("linked_assets", [])),
                "source_refs": list(item.get("source_refs", [])),
                "risk_notice": item.get("risk_notice", ""),
            }
        )

    return feed


def _build_theme_timelines(timeline_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for entry in timeline_entries:
        for theme_name in entry.get("theme_names", []) or ([entry.get("theme_name", "")] if entry.get("theme_name") else []):
            grouped.setdefault(theme_name, []).append(entry)

    theme_timelines: list[dict[str, Any]] = []
    for theme_name, entries in grouped.items():
        sorted_entries = sorted(entries, key=lambda item: item.get("timestamp", ""))
        theme_timelines.append(
            {
                "theme_name": theme_name,
                "entry_count": len(sorted_entries),
                "first_seen_time": sorted_entries[0].get("timestamp", ""),
                "latest_seen_time": sorted_entries[-1].get("timestamp", ""),
                "key_nodes": [
                    {
                        "timeline_id": item.get("timeline_id", ""),
                        "node_type": item.get("node_type", ""),
                        "timestamp": item.get("timestamp", ""),
                        "node_title": item.get("node_title", ""),
                    }
                    for item in sorted_entries[:8]
                ],
            }
        )
    return sorted(theme_timelines, key=lambda item: (item.get("latest_seen_time", ""), item.get("entry_count", 0)), reverse=True)


def _theme_names_from_payload(payload: dict[str, Any]) -> list[str]:
    return list(
        dict.fromkeys(
            [str(item).strip() for item in payload.get("theme_tags", []) + payload.get("related_themes", []) if str(item).strip()]
        )
    )


def _select_timestamp(payload: dict[str, Any]) -> str:
    return str(
        payload.get("event_time")
        or payload.get("occurred_at")
        or payload.get("first_disclosed_at")
        or ""
    ).strip()


def _derive_candidate_strength(candidate: dict[str, Any]) -> str:
    high_strength = int(candidate.get("high_strength_catalyst_count", 0) or 0)
    signal_count = len(candidate.get("supporting_signals", []))
    if high_strength >= 2 or (high_strength >= 1 and signal_count >= 3):
        return "high"
    if high_strength >= 1 or signal_count >= 2:
        return "medium"
    return "low"


def _watchlist_score(linkage: dict[str, Any]) -> float:
    score = 0.0
    for match in linkage.get("watchlist_hits", []):
        match_type = match.get("watch_item_type", "")
        if match_type == "symbol":
            score += 16.0
        elif match_type == "theme":
            score += 10.0
        elif match_type == "sector":
            score += 8.0
        else:
            score += 4.0
    return min(28.0, score)


def _timeline_node_rank(node_type: str) -> int:
    return {"event": 0, "catalyst": 1, "theme_candidate": 2}.get(node_type, 9)


def _timeline_id(prefix: str, entity_id: str, anchor: str) -> str:
    seed = f"{prefix}:{entity_id}:{anchor}"
    return f"{prefix}-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _normalize_stock_code(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return ""
    if len(text) == 9 and "." in text:
        return text
    if len(text) == 8 and text[:2] in {"SH", "SZ"}:
        return f"{text[2:]}.{text[:2]}"
    if text.isdigit() and len(text) == 6:
        return f"{text}.SH" if text.startswith("6") else f"{text}.SZ"
    return text


def _timeliness_level(value: str) -> str:
    if not value:
        return "unknown"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return "unknown"
    hours = (datetime.now(UTC) - dt).total_seconds() / 3600
    if hours <= 6:
        return "high"
    if hours <= 24:
        return "medium"
    return "low"


def _dedupe_watch_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for match in matches:
        key = (
            str(match.get("watch_item_type", "")),
            str(match.get("watch_item_id", "")),
            str(match.get("match_target", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(match)
    return deduped
