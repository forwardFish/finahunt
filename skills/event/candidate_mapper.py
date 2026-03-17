from __future__ import annotations

from typing import Any


def map_theme_clusters_to_candidates(theme_clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mapped_clusters: list[dict[str, Any]] = []

    for cluster in theme_clusters:
        mapped_candidates: list[dict[str, Any]] = []
        dropped_candidates: list[dict[str, Any]] = []

        for stock in cluster.get("candidate_stocks", []):
            mapping_level = _derive_mapping_level(stock)
            if mapping_level is None:
                dropped_candidates.append(
                    {
                        "stock_code": stock.get("stock_code", ""),
                        "stock_name": stock.get("stock_name", ""),
                        "drop_reason": "insufficient_mapping_evidence",
                    }
                )
                continue

            mapped = {
                **stock,
                "mapping_level": mapping_level,
                "mapping_reason": _build_mapping_reason(cluster["theme_name"], stock, mapping_level),
                "mapping_confidence": _derive_mapping_confidence(stock, mapping_level),
                "evidence_source_count": len(stock.get("source_refs", [])),
            }
            mapped_candidates.append(mapped)

        core_candidates = [item for item in mapped_candidates if item["mapping_level"] == "core_beneficiary"]
        direct_candidates = [item for item in mapped_candidates if item["mapping_level"] == "direct_link"]
        supply_chain_candidates = [item for item in mapped_candidates if item["mapping_level"] == "supply_chain_link"]
        peripheral_candidates = [item for item in mapped_candidates if item["mapping_level"] == "peripheral_watch"]

        prioritized_candidates = (
            core_candidates
            + direct_candidates
            + supply_chain_candidates
            + peripheral_candidates
        )

        mapped_clusters.append(
            {
                **cluster,
                "candidate_stocks": prioritized_candidates,
                "candidate_pool": prioritized_candidates,
                "core_candidates": core_candidates,
                "direct_candidates": direct_candidates,
                "supply_chain_candidates": supply_chain_candidates,
                "peripheral_candidates": peripheral_candidates,
                "dropped_candidates": dropped_candidates,
                "mapping_summary": {
                    "candidate_count": len(prioritized_candidates),
                    "core_count": len(core_candidates),
                    "direct_count": len(direct_candidates),
                    "supply_chain_count": len(supply_chain_candidates),
                    "peripheral_count": len(peripheral_candidates),
                    "dropped_count": len(dropped_candidates),
                },
            }
        )

    return sorted(
        mapped_clusters,
        key=lambda item: (
            item.get("mapping_summary", {}).get("core_count", 0),
            item.get("mapping_summary", {}).get("direct_count", 0),
            item.get("related_events_count", 0),
            item.get("source_count", 0),
        ),
        reverse=True,
    )


def _derive_mapping_level(stock: dict[str, Any]) -> str | None:
    purity = float(stock.get("candidate_purity_score", 0.0) or 0.0)
    relation = stock.get("relation", "weak")
    direct_signal_count = int(stock.get("direct_signal_count", 0) or 0)
    evidence_count = len(stock.get("evidence", []))

    if relation == "direct" and (purity >= 70 or direct_signal_count >= 1):
        return "core_beneficiary"
    if relation == "direct" and evidence_count >= 1:
        return "direct_link"
    if purity >= 64 and evidence_count >= 2:
        return "supply_chain_link"
    if purity >= 58 and evidence_count >= 1:
        return "peripheral_watch"
    return None


def _derive_mapping_confidence(stock: dict[str, Any], mapping_level: str) -> float:
    purity = float(stock.get("candidate_purity_score", 0.0) or 0.0)
    source_count = len(stock.get("source_refs", []))
    evidence_count = len(stock.get("evidence", []))
    level_bonus = {
        "core_beneficiary": 10.0,
        "direct_link": 6.0,
        "supply_chain_link": 2.0,
        "peripheral_watch": -2.0,
    }[mapping_level]
    return round(min(100.0, purity + source_count * 3 + evidence_count * 2 + level_bonus), 2)


def _build_mapping_reason(theme_name: str, stock: dict[str, Any], mapping_level: str) -> str:
    evidence = " / ".join(stock.get("evidence", [])[:2]) or theme_name
    mapping_label = {
        "core_beneficiary": "core beneficiary",
        "direct_link": "directly linked",
        "supply_chain_link": "supply-chain linked",
        "peripheral_watch": "peripheral watch",
    }[mapping_level]
    return f"{stock.get('stock_name', stock.get('stock_code', 'candidate'))} is {mapping_label} to {theme_name} through {evidence}."
