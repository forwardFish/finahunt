import json
from pathlib import Path

from skills.event.similar_case import build_low_position_research_cards, build_similar_theme_cases


def test_similar_case_matches_history_without_fabrication(tmp_path: Path):
    history_run = tmp_path / "run-history"
    history_run.mkdir()
    (history_run / "low_position_opportunities.json").write_text(
        json.dumps(
            [
                {
                    "theme_name": "低空经济",
                    "theme_candidate_id": "theme-history",
                    "entry_stage": "emerging",
                    "theme_heat_score": 58,
                    "low_position_score": 74,
                    "fermentation_score": 62,
                    "core_narrative": "低空物流试点推动 eVTOL 和无人机配送再发酵。",
                    "top_evidence": [{"title": "低空物流试点推进"}],
                    "candidate_stocks": [{"stock_code": "300696.SZ", "candidate_purity_score": 82}],
                    "low_position_reason": "旧逻辑重估",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (history_run / "daily_review.json").write_text(
        json.dumps({"today_focus_page": [{"theme_name": "低空经济"}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    current_opportunities = [
        {
            "theme_name": "低空经济",
            "cluster_id": "cluster-current",
            "theme_candidate_id": "theme-current",
            "entry_stage": "emerging",
            "theme_heat_score": 61,
            "low_position_score": 79,
            "fermentation_score": 65,
            "catalyst_score": 58,
            "continuity_score": 71,
            "source_count": 2,
            "high_strength_catalyst_count": 1,
            "core_narrative": "低空物流与 eVTOL 商业化开始形成共识。",
            "top_evidence": [{"title": "低空物流商业化推进", "event_time": "2026-03-17T09:00:00+00:00"}],
            "candidate_stocks": [{"stock_code": "300696.SZ", "candidate_purity_score": 84, "risk_flags": []}],
            "source_refs": ["https://xueqiu.com/demo"],
            "risk_notice": "Continue tracking follow-up proof and diffusion.",
            "low_position_reason": "theme is in early fermentation stage",
        }
    ]
    monitored = [
        {
            "theme_name": "低空经济",
            "theme_candidate_id": "theme-current",
            "fermentation_phase": "spreading",
        }
    ]

    similar_cases = build_similar_theme_cases(
        current_opportunities,
        monitored,
        current_run_id="run-current",
        runtime_root=tmp_path,
    )

    assert similar_cases[0]["matching_status"] == "matched"
    assert similar_cases[0]["reference_type"] == "reignited_logic"
    assert similar_cases[0]["similar_cases"][0]["result_label"] == "promoted_to_focus"

    research_cards = build_low_position_research_cards(current_opportunities, similar_cases)
    assert research_cards[0]["similar_cases"]
    assert research_cards[0]["future_watch_signals"]
    assert "priority" in research_cards[0]["research_positioning_note"].lower()


def test_similar_case_returns_no_match_when_history_is_irrelevant(tmp_path: Path):
    other_run = tmp_path / "run-history"
    other_run.mkdir()
    (other_run / "low_position_opportunities.json").write_text(
        json.dumps(
            [
                {
                    "theme_name": "医药",
                    "theme_candidate_id": "theme-other",
                    "entry_stage": "watch-only",
                    "theme_heat_score": 32,
                    "low_position_score": 41,
                    "core_narrative": "创新药审批进展。",
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    similar_cases = build_similar_theme_cases(
        [
            {
                "theme_name": "算力",
                "cluster_id": "cluster-compute",
                "theme_candidate_id": "theme-compute",
                "entry_stage": "emerging",
                "theme_heat_score": 66,
                "core_narrative": "算力服务器需求上修。",
                "candidate_stocks": [],
                "top_evidence": [],
            }
        ],
        [{"theme_name": "算力", "theme_candidate_id": "theme-compute", "fermentation_phase": "early"}],
        current_run_id="run-current",
        runtime_root=tmp_path,
    )

    assert similar_cases[0]["matching_status"] == "no_match"
    assert similar_cases[0]["similar_cases"] == []
