from skills.event.fermentation import build_fermentation_monitors, build_theme_heat_snapshots


def test_fermentation_monitor_builds_phase_and_monitor_scores():
    monitored = build_fermentation_monitors(
        [
            {
                "theme_name": "低空经济",
                "cluster_id": "cluster-demo",
                "theme_candidate_id": "theme-demo",
                "heat_score": 44.0,
                "catalyst_score": 32.0,
                "continuity_score": 72.0,
                "signal_count": 2,
                "source_count": 2,
                "linked_asset_count": 3,
                "high_strength_catalyst_count": 0,
                "cluster_state": "reignited_theme",
                "cluster_noise_level": "low",
                "anchor_terms": ["无人机配送", "eVTOL", "低空物流"],
                "source_refs": ["https://xueqiu.com/a", "https://www.cls.cn/b"],
                "latest_event_time": "2026-03-17T11:00:00+00:00",
                "supporting_signals": [
                    {
                        "event_time": "2026-03-17T11:00:00+00:00",
                        "source_refs": ["https://xueqiu.com/a"],
                    },
                    {
                        "event_time": "2026-03-17T10:30:00+00:00",
                        "source_refs": ["https://www.cls.cn/b"],
                    },
                ],
                "candidate_stocks": [
                    {
                        "stock_code": "300696.SZ",
                        "candidate_purity_score": 82.0,
                        "judge_status": "accepted",
                        "mapping_level": "core_beneficiary",
                    }
                ],
            }
        ]
    )

    assert len(monitored) == 1
    item = monitored[0]
    assert item["fermentation_phase"] in {"spreading", "crowded", "early"}
    assert item["platform_source_count"] == 2
    assert item["reignition_detected"] is True

    snapshots = build_theme_heat_snapshots(monitored)
    assert snapshots[0]["fermentation_phase"] == item["fermentation_phase"]
    assert snapshots[0]["refire_intensity_score"] >= 65
