from skills.event.purity_judge import judge_theme_candidate_pools


def test_purity_judge_filters_hard_risk_and_preserves_ranked_candidates():
    clusters = [
        {
            "cluster_id": "cluster-demo",
            "theme_name": "机器人",
            "candidate_pool": [
                {
                    "stock_code": "300024.SZ",
                    "stock_name": "机器人样本",
                    "candidate_purity_score": 74.0,
                    "mapping_level": "core_beneficiary",
                    "mapping_confidence": 82.0,
                    "direct_signal_count": 1,
                    "source_refs": ["https://a", "https://b"],
                    "risk_flags": [],
                },
                {
                    "stock_code": "603248.SH",
                    "stock_name": "*ST样本",
                    "candidate_purity_score": 69.0,
                    "mapping_level": "supply_chain_link",
                    "mapping_confidence": 72.0,
                    "direct_signal_count": 0,
                    "source_refs": ["https://a"],
                    "risk_flags": ["*ST"],
                },
                {
                    "stock_code": "600821.SH",
                    "stock_name": "减持样本",
                    "candidate_purity_score": 68.0,
                    "mapping_level": "supply_chain_link",
                    "mapping_confidence": 70.0,
                    "direct_signal_count": 0,
                    "source_refs": ["https://a"],
                    "risk_flags": ["减持"],
                },
            ],
        }
    ]
    rules = {
        "hard_filter_risk_flags": ["*ST", "ST", "退市"],
        "penalty_risk_flags": {"减持": 12},
        "mapping_level_bonus": {
            "core_beneficiary": 10,
            "direct_link": 6,
            "supply_chain_link": 2,
            "peripheral_watch": -2,
        },
        "min_accept_score": 60,
        "min_watch_score": 52,
        "direct_signal_bonus": 4,
        "multi_source_bonus": 4,
    }

    judged = judge_theme_candidate_pools(clusters, rules)

    cluster = judged[0]
    assert len(cluster["accepted_candidates"]) == 1
    assert cluster["accepted_candidates"][0]["stock_code"] == "300024.SZ"
    assert any(item["drop_reason"] == "hard_risk_filter" for item in cluster["filtered_candidates"])
    assert any(item["judge_status"] == "watch" for item in cluster["watch_candidates"])
    assert cluster["accepted_candidates"][0]["candidate_purity_score"] > 74.0
