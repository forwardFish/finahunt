from skills.event.message_workbench import (
    build_daily_message_workbench,
    build_message_company_candidates,
    build_message_fermentation_judgements,
    build_message_impact_analysis,
    build_message_reasoning,
    build_message_scores,
    build_message_validation_feedback,
    build_valuable_messages,
)


class DummyQuoteAdapter:
    def fetch_validation_snapshot(self, *, codes, event_time, benchmark_code="000300.SH"):
        if not codes:
            return {"status": "unverifiable", "validation_window": "T1_CLOSE", "company_moves": [], "basket_move": {}, "benchmark_move": {}}
        return {
            "status": "ok",
            "validation_window": "T1_CLOSE",
            "company_moves": [{"company_code": codes[0], "windows": {"T0_CLOSE": 2.5, "T1_CLOSE": 4.2, "T3_CLOSE": 5.0}, "latest_return": 4.2}],
            "basket_move": {"T0_CLOSE": 2.5, "T1_CLOSE": 4.2, "T3_CLOSE": 5.0},
            "benchmark_move": {"T0_CLOSE": 0.3, "T1_CLOSE": 0.6, "T3_CLOSE": 0.8},
        }


def test_message_workbench_builders_produce_validated_chain():
    canonical_events = [
        {
            "event_id": "evt-001",
            "canonical_key": "solar-procurement",
            "title": "海外采购商计划在中国加大光伏采购",
            "summary": "消息提到将扩大在中国国内的光伏采购规模。",
            "event_subject": "光伏采购",
            "event_type": "order_catalyst",
            "event_time": "2026-03-21T09:00:00+00:00",
            "source_priority": "P0",
            "catalyst_type": "order",
            "catalyst_strength": "high",
            "impact_direction": "positive",
            "impact_scope": "sector",
            "continuity_hint": "developing",
            "related_themes": ["新能源"],
            "theme_tags": ["光伏"],
            "related_industries": ["电力设备"],
            "linked_assets": [{"asset_code": "603693.SH", "asset_name": "江苏新能"}],
            "source_refs": ["https://example.com/solar"],
            "evidence_refs": ["evi-001"],
        }
    ]
    normalized_documents = [
        {
            "title": "海外采购商计划在中国加大光伏采购",
            "summary": "消息提到将扩大在中国国内的光伏采购规模。",
            "url": "https://example.com/solar",
            "source_name": "测试来源",
            "metadata": {"content_text": "海外采购商计划在中国加大光伏采购，江苏新能被反复提及。"},
        }
    ]
    theme_clusters = [{"cluster_id": "cluster-1", "theme_name": "新能源", "core_narrative": "光伏采购扩张"}]
    theme_heat = [{"theme_name": "新能源", "theme_heat_score": 72.0, "fermentation_stage": "early"}]
    low_position = [
        {
            "theme_name": "新能源",
            "low_position_score": 81.0,
            "low_position_reason": "题材仍处于低位研究区间。",
            "candidate_stocks": [
                {
                    "stock_name": "江苏新能",
                    "stock_code": "603693.SH",
                    "mapping_level": "core_beneficiary",
                    "candidate_purity_score": 82.0,
                    "mapping_reason": "主营与新能源主题直接相关。",
                    "source_refs": ["https://example.com/solar"],
                    "evidence": ["https://example.com/solar"],
                }
            ],
        }
    ]
    mapped_clusters = [{"theme_name": "新能源", "candidate_pool": low_position[0]["candidate_stocks"]}]
    judged_clusters = [{"theme_name": "新能源", "candidate_pool": low_position[0]["candidate_stocks"]}]

    messages = build_valuable_messages(canonical_events, normalized_documents)
    fermentation = build_message_fermentation_judgements(messages)
    impact = build_message_impact_analysis(messages, fermentation, theme_clusters, theme_heat, low_position)
    companies = build_message_company_candidates(messages, impact, mapped_clusters, judged_clusters, low_position)
    reasoning = build_message_reasoning(companies, impact)
    validation = build_message_validation_feedback(
        messages,
        fermentation,
        impact,
        companies,
        reasoning,
        quote_adapter=DummyQuoteAdapter(),
    )
    scores = build_message_scores(messages, fermentation, impact, companies, reasoning, validation)
    workbench = build_daily_message_workbench(messages, fermentation, impact, reasoning, validation, scores, run_id="run-test")

    assert len(messages) == 1
    assert fermentation[0]["fermentation_verdict"] in {"high", "medium"}
    assert impact[0]["primary_theme"] == "新能源"
    assert companies[0]["companies"][0]["company_name"] == "江苏新能"
    assert reasoning[0]["companies"][0]["source_reason"] != "pending_source_evidence"
    assert validation[0]["validation_status"] == "confirmed"
    assert scores[0]["recalibrated_actionability_score"] >= scores[0]["initial_actionability_score"]
    assert workbench["messages"][0]["validation"]["validation_status"] == "confirmed"


def test_message_workbench_filters_theme_mismatch_and_rebuilds_company_pool():
    canonical_events = [
        {
            "event_id": "evt-plate",
            "canonical_key": "shanghai-plate-auction",
            "title": "3月份沪牌拍牌下周六举行 警示价92900元",
            "summary": "上海国拍公司发布3月份个人车牌拍卖安排。",
            "event_subject": "沪牌拍牌",
            "event_type": "announcement_catalyst",
            "event_time": "2026-03-21T03:12:10+00:00",
            "source_priority": "P0",
            "catalyst_type": "policy",
            "catalyst_strength": "medium",
            "impact_direction": "neutral",
            "impact_scope": "stock",
            "continuity_hint": "one_off",
            "related_themes": ["算力"],
            "theme_tags": ["算力"],
            "related_industries": ["汽车"],
            "linked_assets": [],
            "source_refs": ["https://example.com/plate"],
            "evidence_refs": ["evi-plate"],
        }
    ]
    normalized_documents = [
        {
            "title": "3月份沪牌拍牌下周六举行 警示价92900元",
            "summary": "上海国拍公司发布3月份个人车牌拍卖安排。",
            "url": "https://example.com/plate",
            "source_name": "财联社快讯",
            "metadata": {"content_text": "上海国拍公司发布3月份个人车牌拍卖安排。"},
        }
    ]

    messages = build_valuable_messages(canonical_events, normalized_documents)
    assert messages == []
