from skills.event.candidate_mapper import map_theme_clusters_to_candidates


class _FakeLLMEnhancer:
    def enrich_cluster(self, cluster):
        return {
            "tracking_verdict": "keep",
            "tracking_reason": "题材已有明确候选股，建议继续跟踪。",
            "candidate_stocks": [
                {
                    "stock_name": "中源协和",
                    "stock_code": "600645.SH",
                    "mapping_level": "core_beneficiary",
                    "purity_score": 82,
                    "confidence": 0.88,
                    "mapping_reason": "干细胞与创新药叙事直接相关。",
                    "llm_reason": "模型判断该股与干细胞创新药主线直接相关，适合继续跟踪。",
                    "scarcity_note": "细分方向辨识度较高。",
                    "risk_flags": [],
                    "should_track": True,
                }
            ],
        }


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
    assert "核心跟踪候选" in cluster["core_candidates"][0]["mapping_reason"]
    assert cluster["core_candidates"][0]["source_reason"]


def test_candidate_mapper_merges_llm_candidates_and_sets_tracking_verdict():
    theme_clusters = [
        {
            "cluster_id": "cluster-med",
            "theme_name": "医药",
            "core_narrative": "创新药与干细胞方向升温。",
            "first_seen_time": "2026-03-18T09:00:00+00:00",
            "latest_seen_time": "2026-03-18T09:00:00+00:00",
            "supporting_signals": [
                {
                    "title": "创新药概念活跃，中源协和涨停",
                    "summary": "干细胞方向领涨。",
                    "event_subject": "中源协和",
                    "catalyst_type": "industry",
                    "catalyst_strength": "medium",
                    "event_time": "2026-03-18T09:00:00+00:00",
                }
            ],
            "related_events_count": 1,
            "source_count": 1,
            "source_refs": ["https://xueqiu.com/demo"],
            "evidence_refs": [],
            "linked_assets": [],
            "linked_asset_count": 0,
            "related_stock_count": 0,
            "catalyst_types": ["industry"],
            "event_types": ["产品/技术突破"],
            "high_strength_catalyst_count": 0,
            "latest_event_time": "2026-03-18T09:00:00+00:00",
            "earliest_event_time": "2026-03-18T09:00:00+00:00",
            "anchor_terms": ["创新药", "干细胞"],
            "cluster_state": "new_theme",
            "cluster_noise_level": "medium",
            "candidate_stocks": [],
        }
    ]

    mapped = map_theme_clusters_to_candidates(theme_clusters, llm_enhancer=_FakeLLMEnhancer())
    cluster = mapped[0]

    assert cluster["tracking_verdict"] == "keep"
    assert cluster["tracking_reason"]
    assert cluster["candidate_pool"][0]["stock_name"] == "中源协和"
    assert cluster["candidate_pool"][0]["stock_code"] == "600645.SH"
    assert cluster["candidate_pool"][0]["mapping_level"] == "core_beneficiary"
    assert cluster["candidate_pool"][0]["llm_reason"]
    assert cluster["llm_mapping_used"] is True
