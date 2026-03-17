from __future__ import annotations

from typing import Any


def judge_theme_candidate_pools(
    mapped_theme_clusters: list[dict[str, Any]],
    purity_rules: dict[str, Any],
) -> list[dict[str, Any]]:
    hard_filters = set(purity_rules.get("hard_filter_risk_flags", []))
    penalty_rules = purity_rules.get("penalty_risk_flags", {})
    mapping_level_bonus = purity_rules.get("mapping_level_bonus", {})
    min_accept_score = float(purity_rules.get("min_accept_score", 60))
    min_watch_score = float(purity_rules.get("min_watch_score", 52))
    direct_signal_bonus = float(purity_rules.get("direct_signal_bonus", 4))
    multi_source_bonus = float(purity_rules.get("multi_source_bonus", 4))

    judged_clusters: list[dict[str, Any]] = []

    for cluster in mapped_theme_clusters:
        judged_candidates: list[dict[str, Any]] = []
        filtered_candidates: list[dict[str, Any]] = []

        for candidate in cluster.get("candidate_pool", []):
            risk_flags = set(candidate.get("risk_flags", []))
            if risk_flags & hard_filters:
                filtered_candidates.append(
                    {
                        **candidate,
                        "judge_status": "filtered",
                        "drop_reason": "hard_risk_filter",
                        "judge_explanation": f"Filtered by hard risk flags: {', '.join(sorted(risk_flags & hard_filters))}.",
                    }
                )
                continue

            base_score = float(candidate.get("candidate_purity_score", 0.0) or 0.0)
            mapping_level = str(candidate.get("mapping_level", "peripheral_watch"))
            mapping_bonus = float(mapping_level_bonus.get(mapping_level, 0.0))
            source_bonus = multi_source_bonus if len(candidate.get("source_refs", [])) >= 2 else 0.0
            direct_bonus = direct_signal_bonus if int(candidate.get("direct_signal_count", 0) or 0) >= 1 else 0.0
            risk_penalty = float(sum(float(penalty_rules.get(flag, 0.0)) for flag in risk_flags))

            final_score = max(0.0, min(100.0, base_score + mapping_bonus + source_bonus + direct_bonus - risk_penalty))
            judge_status = "accepted" if final_score >= min_accept_score else "watch"
            if final_score < min_watch_score:
                filtered_candidates.append(
                    {
                        **candidate,
                        "judge_status": "filtered",
                        "drop_reason": "score_below_watch_threshold",
                        "judge_breakdown": {
                            "base_purity_score": round(base_score, 2),
                            "mapping_bonus": round(mapping_bonus, 2),
                            "source_bonus": round(source_bonus, 2),
                            "direct_signal_bonus": round(direct_bonus, 2),
                            "risk_penalty": round(risk_penalty, 2),
                            "final_purity_score": round(final_score, 2),
                        },
                        "judge_explanation": "Filtered because final purity score stayed below the watch threshold.",
                    }
                )
                continue

            judged_candidates.append(
                {
                    **candidate,
                    "raw_candidate_purity_score": round(base_score, 2),
                    "candidate_purity_score": round(final_score, 2),
                    "judge_status": judge_status,
                    "judge_breakdown": {
                        "base_purity_score": round(base_score, 2),
                        "mapping_bonus": round(mapping_bonus, 2),
                        "source_bonus": round(source_bonus, 2),
                        "direct_signal_bonus": round(direct_bonus, 2),
                        "risk_penalty": round(risk_penalty, 2),
                        "final_purity_score": round(final_score, 2),
                    },
                    "judge_explanation": _build_judge_explanation(candidate, final_score, judge_status, risk_flags),
                }
            )

        judged_candidates.sort(
            key=lambda item: (
                item.get("judge_status") == "accepted",
                item.get("candidate_purity_score", 0.0),
                item.get("mapping_confidence", 0.0),
            ),
            reverse=True,
        )

        judged_clusters.append(
            {
                **cluster,
                "candidate_stocks": judged_candidates,
                "candidate_pool": judged_candidates,
                "accepted_candidates": [item for item in judged_candidates if item.get("judge_status") == "accepted"],
                "watch_candidates": [item for item in judged_candidates if item.get("judge_status") == "watch"],
                "filtered_candidates": filtered_candidates,
                "purity_summary": {
                    "accepted_count": sum(1 for item in judged_candidates if item.get("judge_status") == "accepted"),
                    "watch_count": sum(1 for item in judged_candidates if item.get("judge_status") == "watch"),
                    "filtered_count": len(filtered_candidates),
                    "top_purity_score": judged_candidates[0]["candidate_purity_score"] if judged_candidates else 0.0,
                },
            }
        )

    return judged_clusters


def _build_judge_explanation(
    candidate: dict[str, Any],
    final_score: float,
    judge_status: str,
    risk_flags: set[str],
) -> str:
    level = candidate.get("mapping_level", "peripheral_watch")
    risk_text = f" Risks: {', '.join(sorted(risk_flags))}." if risk_flags else ""
    return (
        f"{candidate.get('stock_name', candidate.get('stock_code', 'candidate'))} is kept as {judge_status} "
        f"with final purity score {round(final_score, 2)} under {level} mapping.{risk_text}"
    )
