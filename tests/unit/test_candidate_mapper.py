from skills.event.candidate_mapper import map_theme_clusters_to_candidates


def test_candidate_mapper_assigns_mapping_levels_and_filters_weak_candidates():
    theme_clusters = [
        {
            "cluster_id": "cluster-demo",
            "theme_name": "低空经济",
            "core_narrative": "demo",
            "first_seen_time": "2026-03-17T10:00:00+00:00",
            "latest_seen_time": "2026-03-17T10:00:00+00:00",
            "supporting_signals": [],
            "related_events_count": 2,
            "source_count": 2,
            "source_refs": ["https://a", "https://b"],
            "evidence_refs": ["evi-1"],
            "linked_assets": [],
            "linked_asset_count": 0,
            "related_stock_count": 3,
            "catalyst_types": ["industry"],
            "event_types": ["产品/技术突破"],
            "high_strength_catalyst_count": 0,
            "latest_event_time": "2026-03-17T10:00:00+00:00",
            "earliest_event_time": "2026-03-17T10:00:00+00:00",
            "anchor_terms": ["无人机配送", "eVTOL"],
            "cluster_state": "new_theme",
            "cluster_noise_level": "low",
            "candidate_stocks": [
                {
                    "stock_code": "300696.SZ",
                    "stock_name": "爱乐达",
                    "candidate_purity_score": 76.0,
                    "relation": "direct",
                    "purity_breakdown": {},
                    "mention_count": 2,
                    "direct_signal_count": 2,
                    "evidence": ["无人机配送", "eVTOL"],
                    "risk_flags": [],
                    "source_refs": ["https://a", "https://b"],
                    "evidence_event_ids": ["evt-1", "evt-2"],
                },
                {
                    "stock_code": "688070.SH",
                    "stock_name": "纵横股份",
                    "candidate_purity_score": 65.0,
                    "relation": "weak",
                    "purity_breakdown": {},
                    "mention_count": 1,
                    "direct_signal_count": 0,
                    "evidence": ["无人机配送", "产业链配套"],
                    "risk_flags": [],
                    "source_refs": ["https://a"],
                    "evidence_event_ids": ["evt-1"],
                },
                {
                    "stock_code": "600000.SH",
                    "stock_name": "边缘样本",
                    "candidate_purity_score": 50.0,
                    "relation": "weak",
                    "purity_breakdown": {},
                    "mention_count": 1,
                    "direct_signal_count": 0,
                    "evidence": [],
                    "risk_flags": [],
                    "source_refs": [],
                    "evidence_event_ids": [],
                },
            ],
        }
    ]

    mapped = map_theme_clusters_to_candidates(theme_clusters)

    assert len(mapped) == 1
    cluster = mapped[0]
    assert cluster["mapping_summary"]["candidate_count"] == 2
    assert cluster["mapping_summary"]["dropped_count"] == 1
    assert cluster["core_candidates"][0]["mapping_level"] == "core_beneficiary"
    assert cluster["supply_chain_candidates"][0]["mapping_level"] == "supply_chain_link"
    assert cluster["core_candidates"][0]["mapping_reason"]
