from skills.event.theme_cluster import build_theme_candidates_from_clusters, build_theme_clusters


def _linked_event(
    event_id: str,
    theme_name: str,
    subject: str,
    *,
    product: str,
    technology: str,
    source_url: str,
    stock_code: str,
) -> dict:
    return {
        "event_id": event_id,
        "title": subject,
        "summary": f"{subject} summary",
        "event_subject": subject,
        "event_type": "产品/技术突破",
        "event_time": "2026-03-17T10:00:00+00:00",
        "impact_scope": "theme",
        "impact_direction": "positive",
        "catalyst_type": "technology_breakthrough",
        "catalyst_strength": "medium",
        "source_refs": [source_url],
        "evidence_refs": [f"evi-{event_id}"],
        "theme_tags": [theme_name],
        "related_themes": [theme_name],
        "related_industries": [theme_name],
        "involved_products": [product],
        "involved_technologies": [technology],
        "involved_policies": [],
        "linked_assets": [
            {"asset_type": "stock", "asset_id": stock_code, "asset_name": subject, "relation": "direct"},
            {"asset_type": "theme", "asset_id": theme_name, "asset_name": theme_name, "relation": "direct"},
        ],
        "candidate_stock_links": [
            {
                "theme_name": theme_name,
                "stock_code": stock_code,
                "stock_name": subject,
                "candidate_purity_score": 74.0,
                "purity_breakdown": {
                    "theme_purity": 85.0,
                    "uniqueness": 70.0,
                    "business_elasticity": 65.0,
                    "market_cap_fit": 55.0,
                    "financial_health": 80.0,
                    "theme_memory": 58.0,
                },
                "evidence": [product, technology],
                "risk_flags": [],
                "event_id": event_id,
                "relation": "direct",
            }
        ],
        "continuity_hint": "developing",
        "source_priority": "P1",
    }


def test_theme_cluster_merges_related_events_and_separates_unrelated_noise():
    related_a = _linked_event(
        "evt-001",
        "低空经济",
        "爱乐达",
        product="无人机配送",
        technology="eVTOL",
        source_url="https://xueqiu.com/a",
        stock_code="300696.SZ",
    )
    related_b = _linked_event(
        "evt-002",
        "低空经济",
        "纵横股份",
        product="无人机配送",
        technology="eVTOL",
        source_url="https://jiuyangongshe.com/b",
        stock_code="688070.SH",
    )
    noisy = _linked_event(
        "evt-003",
        "低空经济",
        "油运样本",
        product="港口航运",
        technology="油运调度",
        source_url="https://cls.cn/c",
        stock_code="600026.SH",
    )

    clusters = build_theme_clusters([related_a, related_b, noisy])

    assert len(clusters) == 2
    assert any(item["related_events_count"] == 2 for item in clusters)
    assert any(item["cluster_state"] == "single_signal_noise" for item in clusters)

    candidates = build_theme_candidates_from_clusters(clusters)
    assert len(candidates) == 2
    assert any(item["candidate_stocks"] for item in candidates)
