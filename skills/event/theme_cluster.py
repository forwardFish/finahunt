from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from skills.event.fermentation import (
    _build_candidate_stocks,
    _build_core_narrative,
    _calculate_catalyst_score,
    _calculate_continuity_score,
    _calculate_heat_score,
    _strength_rank,
)


def build_theme_clusters(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}

    for event in events:
        theme_names = list(dict.fromkeys(event.get("theme_tags", []) or event.get("related_themes", [])))
        if not theme_names:
            continue

        for theme_name in theme_names:
            anchor_terms = _extract_cluster_anchor_terms(event, theme_name)
            cluster = _find_matching_cluster(grouped.get(theme_name, []), event, anchor_terms)
            if cluster is None:
                cluster = _new_theme_cluster(theme_name)
                grouped.setdefault(theme_name, []).append(cluster)
            _merge_event_into_cluster(cluster, event, theme_name, anchor_terms)

    results: list[dict[str, Any]] = []
    for theme_name, clusters in grouped.items():
        for cluster in clusters:
            supporting_signals = sorted(
                cluster["supporting_signals"],
                key=lambda item: (item.get("event_time", ""), _strength_rank(item.get("catalyst_strength", "unknown"))),
                reverse=True,
            )
            candidate_stocks = _build_candidate_stocks(cluster["candidate_stocks"])
            related_stock_count = max(
                len(candidate_stocks),
                sum(1 for item in cluster["linked_assets"].values() if item.get("asset_type") == "stock"),
            )
            signal_count = len(supporting_signals)
            source_count = len(cluster["source_refs"])
            anchor_terms = [term for term, _ in cluster["anchor_terms"].most_common(6)]
            cluster_hash = hashlib.sha256(
                f"{theme_name}|{'|'.join(anchor_terms[:4])}|{cluster['earliest_event_time']}".encode("utf-8")
            ).hexdigest()[:10]

            results.append(
                {
                    "cluster_id": f"cluster-{cluster_hash}",
                    "theme_name": theme_name,
                    "core_narrative": _build_core_narrative(theme_name, supporting_signals, list(cluster["narrative_terms"])),
                    "first_seen_time": cluster["earliest_event_time"],
                    "latest_seen_time": cluster["latest_event_time"],
                    "supporting_signals": supporting_signals,
                    "related_events_count": signal_count,
                    "source_count": source_count,
                    "source_refs": sorted(cluster["source_refs"]),
                    "evidence_refs": sorted(cluster["evidence_refs"]),
                    "linked_assets": list(cluster["linked_assets"].values()),
                    "linked_asset_count": len(cluster["linked_assets"]),
                    "related_stock_count": related_stock_count,
                    "catalyst_types": sorted(cluster["catalyst_types"]),
                    "event_types": sorted(cluster["event_types"]),
                    "high_strength_catalyst_count": cluster["high_strength_catalyst_count"],
                    "candidate_stocks": candidate_stocks,
                    "latest_event_time": cluster["latest_event_time"],
                    "earliest_event_time": cluster["earliest_event_time"],
                    "anchor_terms": anchor_terms,
                    "cluster_state": _derive_cluster_state(cluster, signal_count, source_count),
                    "cluster_noise_level": _derive_cluster_noise_level(cluster, signal_count, source_count),
                }
            )

    return sorted(
        results,
        key=lambda item: (
            item["cluster_state"] == "new_theme",
            item["source_count"],
            item["related_events_count"],
            item["latest_seen_time"],
        ),
        reverse=True,
    )


def build_theme_candidates_from_clusters(theme_clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for cluster in theme_clusters:
        signal_count = int(cluster.get("related_events_count", 0) or 0)
        source_count = int(cluster.get("source_count", 0) or 0)
        related_stock_count = int(cluster.get("related_stock_count", 0) or 0)
        high_strength_count = int(cluster.get("high_strength_catalyst_count", 0) or 0)
        latest_event_time = cluster.get("latest_event_time", "")
        earliest_event_time = cluster.get("earliest_event_time", "")
        supporting_signals = cluster.get("supporting_signals", [])

        heat_score = _calculate_heat_score(signal_count, source_count, related_stock_count, latest_event_time)
        catalyst_score = _calculate_catalyst_score(supporting_signals, high_strength_count, source_count)
        continuity_score = _calculate_continuity_score(
            signal_count,
            source_count,
            len(cluster.get("event_types", [])),
            earliest_event_time,
            latest_event_time,
        )

        if cluster.get("cluster_state") == "reignited_theme":
            continuity_score = min(100.0, continuity_score + 6)
        if cluster.get("cluster_noise_level") == "high":
            heat_score = max(0.0, heat_score - 8)
            catalyst_score = max(0.0, catalyst_score - 6)

        results.append(
            {
                "cluster_id": cluster["cluster_id"],
                "theme_candidate_id": f"theme-{cluster['cluster_id'].removeprefix('cluster-')}",
                "theme_name": cluster["theme_name"],
                "core_narrative": cluster.get("core_narrative", ""),
                "first_seen_time": cluster.get("first_seen_time", earliest_event_time),
                "latest_seen_time": cluster.get("latest_seen_time", latest_event_time),
                "supporting_signals": supporting_signals,
                "signal_count": signal_count,
                "related_events_count": signal_count,
                "source_count": source_count,
                "source_refs": cluster.get("source_refs", []),
                "evidence_refs": cluster.get("evidence_refs", []),
                "linked_assets": cluster.get("linked_assets", []),
                "linked_asset_count": int(cluster.get("linked_asset_count", 0) or 0),
                "related_stock_count": related_stock_count,
                "catalyst_types": cluster.get("catalyst_types", []),
                "high_strength_catalyst_count": high_strength_count,
                "heat_score": round(heat_score, 2),
                "catalyst_score": round(catalyst_score, 2),
                "continuity_score": round(continuity_score, 2),
                "fermentation_score": round(heat_score * 0.38 + catalyst_score * 0.34 + continuity_score * 0.28, 2),
                "candidate_stocks": cluster.get("candidate_stocks", []),
                "latest_event_time": latest_event_time,
                "earliest_event_time": earliest_event_time,
                "cluster_state": cluster.get("cluster_state", "new_theme"),
                "cluster_noise_level": cluster.get("cluster_noise_level", "medium"),
                "anchor_terms": cluster.get("anchor_terms", []),
            }
        )

    return sorted(results, key=lambda item: (item["fermentation_score"], item["signal_count"]), reverse=True)


def _new_theme_cluster(theme_name: str) -> dict[str, Any]:
    return {
        "theme_name": theme_name,
        "supporting_signals": [],
        "source_refs": set(),
        "evidence_refs": set(),
        "linked_assets": {},
        "catalyst_types": set(),
        "event_types": set(),
        "continuity_hints": Counter(),
        "source_priorities": Counter(),
        "high_strength_catalyst_count": 0,
        "latest_event_time": "",
        "earliest_event_time": "",
        "candidate_stocks": {},
        "narrative_terms": [],
        "anchor_terms": Counter(),
    }


def _extract_cluster_anchor_terms(event: dict[str, Any], theme_name: str) -> list[str]:
    values: list[str] = []
    values.extend(event.get("related_industries", []))
    values.extend(event.get("involved_products", []))
    values.extend(event.get("involved_technologies", []))
    values.extend(event.get("involved_policies", []))
    values.extend(item for item in event.get("related_themes", []) if item != theme_name)
    if event.get("event_subject"):
        values.append(event["event_subject"])
    for asset in event.get("linked_assets", []):
        asset_name = str(asset.get("asset_name", "") or "").strip()
        asset_type = asset.get("asset_type", "")
        if asset_name and asset_name != theme_name and asset_type in {"stock", "theme", "industry"}:
            values.append(asset_name)
    normalized = []
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned or cleaned == theme_name or cleaned == "unknown":
            continue
        normalized.append(cleaned)
    return list(dict.fromkeys(normalized))[:8]


def _find_matching_cluster(
    clusters: list[dict[str, Any]],
    event: dict[str, Any],
    anchor_terms: list[str],
) -> dict[str, Any] | None:
    best_cluster: dict[str, Any] | None = None
    best_score = 0
    event_subject = str(event.get("event_subject", "") or "").strip()
    event_type = str(event.get("event_type", "") or "")
    catalyst_type = str(event.get("catalyst_type", "") or "")
    continuity_hint = str(event.get("continuity_hint", "") or "")

    for cluster in clusters:
        overlap = len(set(anchor_terms) & set(cluster["anchor_terms"].keys()))
        same_subject = bool(event_subject and event_subject in cluster["narrative_terms"])
        same_event_type = bool(event_type and event_type in cluster["event_types"])
        same_catalyst = bool(catalyst_type and catalyst_type in cluster["catalyst_types"])
        same_continuity = bool(continuity_hint and cluster["continuity_hints"].get(continuity_hint, 0))
        score = overlap * 3 + int(same_subject) * 2 + int(same_event_type) + int(same_catalyst) + int(same_continuity)
        if overlap == 0 and not same_subject:
            continue
        if score > best_score:
            best_score = score
            best_cluster = cluster

    if best_score >= 3:
        return best_cluster
    return None


def _merge_event_into_cluster(
    cluster: dict[str, Any],
    event: dict[str, Any],
    theme_name: str,
    anchor_terms: list[str],
) -> None:
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
        "source_priority": event.get("source_priority", "unknown"),
        "continuity_hint": event.get("continuity_hint", "unknown"),
    }
    cluster["supporting_signals"].append(signal)
    cluster["source_refs"].update(event.get("source_refs", []))
    cluster["evidence_refs"].update(event.get("evidence_refs", []))
    cluster["catalyst_types"].add(event.get("catalyst_type", "unknown"))
    cluster["event_types"].add(event.get("event_type", "information_update"))
    cluster["continuity_hints"][event.get("continuity_hint", "unknown")] += 1
    cluster["source_priorities"][event.get("source_priority", "unknown")] += 1
    cluster["anchor_terms"].update(anchor_terms)
    cluster["narrative_terms"].extend(
        anchor_terms
        + event.get("related_themes", [])
        + event.get("related_industries", [])
        + event.get("involved_products", [])
        + event.get("involved_technologies", [])
        + event.get("involved_policies", [])
    )

    if event.get("event_subject"):
        cluster["narrative_terms"].append(str(event.get("event_subject")))
    if event.get("catalyst_strength") == "high":
        cluster["high_strength_catalyst_count"] += 1

    for asset in event.get("linked_assets", []):
        key = f"{asset.get('asset_type')}::{asset.get('asset_id')}"
        cluster["linked_assets"][key] = asset

    for stock_link in event.get("candidate_stock_links", []):
        if stock_link.get("theme_name") != theme_name:
            continue
        key = stock_link.get("stock_code", "")
        if not key:
            continue
        entry = cluster["candidate_stocks"].setdefault(
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
        if not cluster["latest_event_time"] or event_time > cluster["latest_event_time"]:
            cluster["latest_event_time"] = event_time
        if not cluster["earliest_event_time"] or event_time < cluster["earliest_event_time"]:
            cluster["earliest_event_time"] = event_time


def _derive_cluster_state(cluster: dict[str, Any], signal_count: int, source_count: int) -> str:
    if cluster["continuity_hints"].get("reignited", 0) >= max(1, signal_count // 2):
        return "reignited_theme"
    if signal_count == 1 and source_count == 1 and cluster["high_strength_catalyst_count"] == 0:
        return "single_signal_noise"
    return "new_theme"


def _derive_cluster_noise_level(cluster: dict[str, Any], signal_count: int, source_count: int) -> str:
    anchor_count = len(cluster["anchor_terms"])
    if signal_count == 1 and source_count == 1 and anchor_count <= 1:
        return "high"
    if source_count == 1 or anchor_count <= 2:
        return "medium"
    return "low"
