from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from packages.artifacts.store import RUNTIME_ROOT


def build_similar_theme_cases(
    low_position_opportunities: list[dict[str, Any]],
    monitored_themes: list[dict[str, Any]],
    *,
    current_run_id: str,
    runtime_root: Path | None = None,
    max_history_runs: int = 24,
    max_cases_per_theme: int = 3,
) -> list[dict[str, Any]]:
    runtime_root = runtime_root or RUNTIME_ROOT
    history_cases = _load_history_cases(runtime_root, current_run_id=current_run_id, max_history_runs=max_history_runs)
    monitored_by_candidate = {item.get("theme_candidate_id", ""): item for item in monitored_themes}

    results: list[dict[str, Any]] = []
    for opportunity in low_position_opportunities:
        theme_candidate_id = str(opportunity.get("theme_candidate_id", ""))
        monitor = monitored_by_candidate.get(theme_candidate_id, {})
        current_tokens = _extract_tokens(
            opportunity.get("theme_name", ""),
            opportunity.get("core_narrative", ""),
            " ".join(item.get("title", "") for item in opportunity.get("top_evidence", []) if item.get("title")),
        )
        matches: list[dict[str, Any]] = []
        for case in history_cases:
            similarity_score = _calculate_similarity(opportunity, monitor, current_tokens, case)
            if similarity_score < 28:
                continue
            matches.append(
                {
                    "run_id": case["run_id"],
                    "theme_name": case["theme_name"],
                    "reference_type": case["reference_type"],
                    "similarity_score": round(similarity_score, 2),
                    "similarity_reason": _build_similarity_reason(opportunity, case, current_tokens),
                    "difference_note": _build_difference_note(opportunity, case, monitor),
                    "historical_path_summary": case["historical_path_summary"],
                    "result_label": case["result_label"],
                    "theme_heat_score": case["theme_heat_score"],
                    "low_position_score": case["low_position_score"],
                    "entry_stage": case["entry_stage"],
                    "candidate_stocks": case["candidate_stocks"][:2],
                    "artifact_ref": case["artifact_ref"],
                }
            )

        matches.sort(key=lambda item: item["similarity_score"], reverse=True)
        top_matches = matches[:max_cases_per_theme]
        results.append(
            {
                "theme_name": opportunity.get("theme_name", ""),
                "cluster_id": opportunity.get("cluster_id", ""),
                "theme_candidate_id": theme_candidate_id,
                "matching_status": "matched" if top_matches else "no_match",
                "reference_type": _summarize_reference_type(top_matches),
                "similar_cases": top_matches,
            }
        )

    return results


def build_low_position_research_cards(
    low_position_opportunities: list[dict[str, Any]],
    similar_theme_cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    similar_by_candidate = {
        item.get("theme_candidate_id", ""): item for item in similar_theme_cases if item.get("theme_candidate_id")
    }
    cards: list[dict[str, Any]] = []
    for opportunity in low_position_opportunities:
        theme_candidate_id = str(opportunity.get("theme_candidate_id", ""))
        similar_payload = similar_by_candidate.get(theme_candidate_id, {})
        candidate_stocks = list(opportunity.get("candidate_stocks", []) or [])
        future_watch_signals = _build_future_watch_signals(opportunity, similar_payload)
        risk_flags = _collect_risk_flags(opportunity)
        cards.append(
            {
                "theme_name": opportunity.get("theme_name", ""),
                "cluster_id": opportunity.get("cluster_id", ""),
                "theme_candidate_id": theme_candidate_id,
                "research_priority_score": float(opportunity.get("low_position_score", 0.0) or 0.0),
                "current_stage": opportunity.get("entry_stage", "watch-only"),
                "core_narrative": opportunity.get("core_narrative", ""),
                "first_source_url": (opportunity.get("source_refs") or [""])[0],
                "latest_24h_key_catalysts": [
                    {
                        "title": item.get("title", ""),
                        "event_time": item.get("event_time", ""),
                        "summary": item.get("summary", ""),
                    }
                    for item in (opportunity.get("top_evidence") or [])[:3]
                ],
                "candidate_stocks": candidate_stocks[:5],
                "top_candidate_purity_score": float((candidate_stocks[:1] or [{}])[0].get("candidate_purity_score", 0.0) or 0.0),
                "fermentation_path": {
                    "entry_stage": opportunity.get("entry_stage", "watch-only"),
                    "theme_heat_score": float(opportunity.get("theme_heat_score", 0.0) or 0.0),
                    "fermentation_score": float(opportunity.get("fermentation_score", 0.0) or 0.0),
                    "catalyst_score": float(opportunity.get("catalyst_score", 0.0) or 0.0),
                    "continuity_score": float(opportunity.get("continuity_score", 0.0) or 0.0),
                },
                "similar_cases": similar_payload.get("similar_cases", []),
                "reference_type": similar_payload.get("reference_type", "no_reference"),
                "future_watch_signals": future_watch_signals,
                "risk_flags": risk_flags,
                "risk_notice": opportunity.get("risk_notice", ""),
                "low_position_reason": opportunity.get("low_position_reason", ""),
                "research_positioning_note": "Research priority only. This card is for observation and review, not a trading instruction.",
            }
        )
    return cards


def _load_history_cases(runtime_root: Path, *, current_run_id: str, max_history_runs: int) -> list[dict[str, Any]]:
    if not runtime_root.exists():
        return []

    run_dirs = [path for path in runtime_root.iterdir() if path.is_dir() and path.name != current_run_id]
    run_dirs.sort(key=lambda item: item.stat().st_mtime, reverse=True)

    history_cases: list[dict[str, Any]] = []
    for run_dir in run_dirs[:max_history_runs]:
        opportunities = _load_json_list(run_dir / "low_position_opportunities.json")
        if not opportunities:
            continue
        focus_names = {
            str(item.get("theme_name", ""))
            for item in (_load_json_dict(run_dir / "daily_review.json").get("today_focus_page") or [])
            if item.get("theme_name")
        }
        for item in opportunities:
            theme_name = str(item.get("theme_name", ""))
            if not theme_name:
                continue
            history_cases.append(
                {
                    "run_id": run_dir.name,
                    "theme_name": theme_name,
                    "theme_candidate_id": str(item.get("theme_candidate_id", "")),
                    "core_narrative": item.get("core_narrative", ""),
                    "entry_stage": item.get("entry_stage", "watch-only"),
                    "theme_heat_score": float(item.get("theme_heat_score", 0.0) or 0.0),
                    "low_position_score": float(item.get("low_position_score", 0.0) or 0.0),
                    "fermentation_score": float(item.get("fermentation_score", 0.0) or 0.0),
                    "candidate_stocks": list(item.get("candidate_stocks", []) or []),
                    "risk_notice": item.get("risk_notice", ""),
                    "historical_path_summary": _build_history_summary(item, focus_names, run_dir.name),
                    "result_label": "promoted_to_focus" if theme_name in focus_names else "watchlist_reference",
                    "reference_type": _infer_reference_type(item),
                    "tokens": _extract_tokens(
                        theme_name,
                        item.get("core_narrative", ""),
                        " ".join(signal.get("title", "") for signal in item.get("top_evidence", []) if signal.get("title")),
                    ),
                    "artifact_ref": f"artifact://runtime/{run_dir.name}/low_position_opportunities.json",
                }
            )
    return history_cases


def _build_history_summary(item: dict[str, Any], focus_names: set[str], run_id: str) -> str:
    theme_name = item.get("theme_name", "")
    entry_stage = item.get("entry_stage", "watch-only")
    low_position_score = float(item.get("low_position_score", 0.0) or 0.0)
    if theme_name in focus_names:
        return f"{theme_name} reached the focus page in {run_id} after entering {entry_stage} with a research score of {low_position_score:.1f}."
    return f"{theme_name} remained a watchlist reference in {run_id} with {entry_stage} status and a research score of {low_position_score:.1f}."


def _calculate_similarity(
    opportunity: dict[str, Any],
    monitor: dict[str, Any],
    current_tokens: set[str],
    case: dict[str, Any],
) -> float:
    theme_name = str(opportunity.get("theme_name", ""))
    exact_match = 1.0 if theme_name and theme_name == case.get("theme_name") else 0.0
    token_overlap = _jaccard(current_tokens, case.get("tokens", set()))
    stage_match = 1.0 if opportunity.get("entry_stage") == case.get("entry_stage") else 0.35
    phase_match = 1.0 if monitor.get("fermentation_phase") == case.get("entry_stage") else 0.0
    heat_distance = abs(float(opportunity.get("theme_heat_score", 0.0) or 0.0) - float(case.get("theme_heat_score", 0.0) or 0.0))
    heat_score = max(0.0, 1.0 - min(heat_distance / 45.0, 1.0))
    reference_bonus = 0.12 if case.get("reference_type") == "reignited_logic" else 0.0
    return (exact_match * 48 + token_overlap * 28 + stage_match * 12 + phase_match * 4 + heat_score * 8 + reference_bonus * 100)


def _build_similarity_reason(opportunity: dict[str, Any], case: dict[str, Any], current_tokens: set[str]) -> str:
    reasons: list[str] = []
    if opportunity.get("theme_name") == case.get("theme_name"):
        reasons.append("same theme name has appeared before")
    token_overlap = _jaccard(current_tokens, case.get("tokens", set()))
    if token_overlap >= 0.24:
        reasons.append("core narrative shares overlapping catalyst terms")
    if opportunity.get("entry_stage") == case.get("entry_stage"):
        reasons.append("research stage matches the historical path")
    if case.get("reference_type") == "reignited_logic":
        reasons.append("historical path looks like a reignited logic pattern")
    if not reasons:
        reasons.append("historical path provides an adjacent pattern reference")
    return "; ".join(reasons)


def _build_difference_note(opportunity: dict[str, Any], case: dict[str, Any], monitor: dict[str, Any]) -> str:
    notes: list[str] = []
    current_heat = float(opportunity.get("theme_heat_score", 0.0) or 0.0)
    history_heat = float(case.get("theme_heat_score", 0.0) or 0.0)
    if current_heat > history_heat + 10:
        notes.append("current theme is heating faster than the historical case")
    elif history_heat > current_heat + 10:
        notes.append("historical case had stronger heat expansion at the same stage")
    current_phase = monitor.get("fermentation_phase")
    if current_phase and current_phase != case.get("entry_stage"):
        notes.append(f"current phase is {current_phase}, while the historical case started from {case.get('entry_stage')}")
    if not notes:
        notes.append("current setup is close to the historical path but still needs follow-up proof")
    return "; ".join(notes)


def _summarize_reference_type(similar_cases: list[dict[str, Any]]) -> str:
    if not similar_cases:
        return "no_reference"
    if any(item.get("reference_type") == "reignited_logic" for item in similar_cases):
        return "reignited_logic"
    return "adjacent_pattern"


def _build_future_watch_signals(opportunity: dict[str, Any], similar_payload: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    source_count = int(opportunity.get("source_count", 0) or 0)
    high_strength = int(opportunity.get("high_strength_catalyst_count", 0) or 0)
    top_candidate_score = float((opportunity.get("candidate_stocks") or [{}])[0].get("candidate_purity_score", 0.0) or 0.0)
    if source_count < 2:
        signals.append("Watch for a second public source to confirm the theme.")
    if high_strength == 0:
        signals.append("Watch for a stronger catalyst such as a policy, order, or official announcement.")
    if top_candidate_score < 70:
        signals.append("Watch for a clearer core beneficiary mapping and higher purity score.")
    if float(opportunity.get("fermentation_score", 0.0) or 0.0) < 60:
        signals.append("Watch whether the narrative spreads beyond the current source set.")
    if similar_payload.get("matching_status") != "matched":
        signals.append("Watch whether the theme starts resembling a recognizable historical pattern.")
    if not signals:
        signals.append("Watch whether the current catalyst chain can keep compounding into broader market consensus.")
    return signals[:4]


def _collect_risk_flags(opportunity: dict[str, Any]) -> list[str]:
    risk_flags: list[str] = []
    for candidate in opportunity.get("candidate_stocks", []) or []:
        risk_flags.extend(candidate.get("risk_flags", []) or [])
    if opportunity.get("entry_stage") == "watch-only":
        risk_flags.append("theme still sits in watch-only stage")
    if opportunity.get("risk_notice"):
        risk_flags.append(str(opportunity["risk_notice"]))
    deduped: list[str] = []
    seen: set[str] = set()
    for item in risk_flags:
        normalized = str(item).strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped[:6]


def _infer_reference_type(item: dict[str, Any]) -> str:
    narrative = f"{item.get('core_narrative', '')} {item.get('low_position_reason', '')}"
    lowered = narrative.lower()
    if "reignite" in lowered or "re-ignite" in lowered or "re-estimate" in lowered:
        return "reignited_logic"
    if any(token in narrative for token in ("再发酵", "重估", "旧逻辑")):
        return "reignited_logic"
    return "adjacent_pattern"


def _extract_tokens(*parts: str) -> set[str]:
    normalized = " ".join(part for part in parts if part)
    ascii_tokens = re.findall(r"[A-Za-z]{2,}|\d{2,}", normalized.lower())
    chinese_tokens = re.findall(r"[\u4e00-\u9fff]{2,}", normalized)
    char_windows: set[str] = set()
    for token in chinese_tokens:
        compact = token.strip()
        if len(compact) <= 2:
            char_windows.add(compact)
            continue
        for size in (2, 3):
            for index in range(0, len(compact) - size + 1):
                char_windows.add(compact[index : index + size])
    return set(ascii_tokens + chinese_tokens) | char_windows


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def _load_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}
