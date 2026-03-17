from workflows.runtime_schedule import run_runtime_cycle


def test_event_cognition_runtime_produces_ranked_outputs(monkeypatch):
    def fake_pipeline(sources, *, max_items_per_source, timeout, run_id):
        return {
            "raw_contents": [
                {
                    "content_id": "rawc-001",
                    "source_id": "cls-telegraph",
                    "site_name": "财联社快讯",
                    "list_url": "https://www.cls.cn/telegraph",
                    "source_url": "https://www.cls.cn/detail/1",
                    "fetched_at": "2026-03-16T10:05:00+00:00",
                    "published_at": "2026-03-16T10:00:00+00:00",
                    "title": "工信部发文支持机器人产业创新",
                    "body": "工信部发文支持机器人产业创新发展，机器人板块关注度提升，300024.SZ受到关注。",
                    "author": "财联社",
                    "tags": ["telegraph", "fast_feed"],
                    "metadata": {
                        "stock_list": [{"secu_code": "300024.SZ", "secu_name": "机器人样本"}],
                        "plate_list": [{"plate_name": "机器人"}],
                    },
                },
                {
                    "content_id": "rawc-002",
                    "source_id": "jiuyangongshe-live",
                    "site_name": "韭研公社",
                    "list_url": "https://www.jiuyangongshe.com/live",
                    "source_url": "https://www.jiuyangongshe.com/live#abc123",
                    "fetched_at": "2026-03-16T09:10:00+00:00",
                    "published_at": "2026-03-16T09:00:00+00:00",
                    "title": "算力链景气上修",
                    "body": "算力服务器需求上修，板块热度提升，000063.SZ被反复提及。",
                    "author": "韭研公社",
                    "tags": ["community", "live"],
                    "metadata": {
                        "stock_list": [{"secu_code": "000063.SZ", "secu_name": "中兴通讯"}],
                        "plate_list": [{"plate_name": "算力"}],
                    },
                },
                {
                    "content_id": "rawc-003",
                    "source_id": "xueqiu-hot-spot",
                    "site_name": "雪球热点",
                    "list_url": "https://xueqiu.com/hot/spot",
                    "source_url": "https://xueqiu.com/hashtag/demo",
                    "fetched_at": "2026-03-16T09:20:00+00:00",
                    "published_at": "2026-03-16T09:18:00+00:00",
                    "title": "低空物流试点推进",
                    "body": "低空物流试点推进，无人机配送与eVTOL商业化叙事升温，300696.SZ进入高频讨论。",
                    "author": "雪球编辑",
                    "tags": ["community", "hot_spot"],
                    "metadata": {
                        "stocks": [{"code": "300696.SZ", "name": "爱乐达"}],
                    },
                },
            ],
            "execution_log": [
                {"source_id": "cls-telegraph", "status": "success", "stored_count": 1},
                {"source_id": "jiuyangongshe-live", "status": "success", "stored_count": 1},
                {"source_id": "xueqiu-hot-spot", "status": "success", "stored_count": 1},
            ],
            "storage_summary": {"batch_dir": "workspace/artifacts/source_fetch/run-test", "manifest": {"content_count": 3}},
        }

    monkeypatch.setattr("skills.fetch.client.crawl_public_page_sources_sync", fake_pipeline)

    result = run_runtime_cycle(
        "event-cognition-test",
        rule_version="v2",
        requested_sources=["cls-telegraph", "jiuyangongshe-live", "xueqiu-hot-spot"],
        live_fetch=True,
        user_profile={"watchlist_symbols": ["300024.SZ"], "watchlist_themes": ["机器人", "算力", "低空经济"]},
        max_items_per_source=5,
    )

    runtime = result["results"]["source_runtime"]["content"]
    normalize = result["results"]["normalize"]["content"]
    scout = result["results"]["source_scout"]["content"]
    extract = result["results"]["event_extract"]["content"]
    theme = result["results"]["theme_detection"]["content"]
    catalyst = result["results"]["catalyst_classification"]["content"]
    linkage = result["results"]["stock_linkage"]["content"]
    theme_cluster = result["results"]["theme_cluster"]["content"]
    candidate_mapper = result["results"]["candidate_mapper"]["content"]
    purity_judge = result["results"]["purity_judge"]["content"]
    theme_candidates = result["results"]["theme_candidate_aggregation"]["content"]
    fermentation_monitor = result["results"]["fermentation_monitor"]["content"]
    result_cards = result["results"]["structured_result_cards"]["content"]
    theme_heat = result["results"]["theme_heat_snapshot"]["content"]
    low_position = result["results"]["low_position_discovery"]["content"]
    feed = result["results"]["fermenting_theme_feed"]["content"]
    ranking = result["results"]["relevance_ranking"]["content"]
    review = result["results"]["daily_review"]["content"]
    warehouse = result["results"]["result_warehouse"]["content"]

    assert runtime["fetch_status_report"]["live_fetch"] is True
    assert len(runtime["raw_documents"]) == 3
    assert runtime["raw_content_storage"]["manifest"]["content_count"] == 3
    assert len(scout["scouted_documents"]) == 3
    assert any(item["metadata"]["source_priority"] == "P0" for item in scout["scouted_documents"])
    assert len(normalize["normalized_documents"]) == 3
    assert len(extract["candidate_events"]) == 3
    assert all(event["event_id"] for event in extract["candidate_events"])
    assert any(event["event_subject"] for event in extract["candidate_events"])
    assert any(event["related_industries"] for event in extract["candidate_events"])
    assert any(event["source_priority"] in {"P0", "P1"} for event in extract["candidate_events"])
    assert any(event["catalyst_boundary"] in {"stock", "theme"} for event in extract["candidate_events"])
    assert any(event["continuity_hint"] in {"developing", "reignited", "one_off"} for event in extract["candidate_events"])
    assert any(event["theme_tags"] for event in theme["theme_enriched_events"])
    assert any(event["catalyst_type"] != "unknown" for event in catalyst["catalyst_events"])
    assert any(event["linked_assets"] for event in linkage["linked_events"])
    assert any(event["candidate_stock_links"] for event in linkage["linked_events"])
    assert any(item["theme_name"] for item in theme_cluster["theme_clusters"])
    assert any(item["cluster_state"] in {"new_theme", "reignited_theme", "single_signal_noise"} for item in theme_cluster["theme_clusters"])
    assert any(item["mapping_summary"]["candidate_count"] >= 1 for item in candidate_mapper["mapped_theme_clusters"])
    assert any(
        candidate["mapping_level"] in {"core_beneficiary", "direct_link", "supply_chain_link", "peripheral_watch"}
        for item in candidate_mapper["mapped_theme_clusters"]
        for candidate in item.get("candidate_pool", [])
    )
    assert any(
        candidate["judge_status"] in {"accepted", "watch"}
        for item in purity_judge["judged_theme_clusters"]
        for candidate in item.get("candidate_pool", [])
    )
    assert any(
        "judge_breakdown" in candidate
        for item in purity_judge["judged_theme_clusters"]
        for candidate in item.get("candidate_pool", [])
    )
    assert any(item["theme_name"] for item in theme_candidates["theme_candidates"])
    assert any(item["fermentation_phase"] in {"early", "spreading", "crowded"} for item in fermentation_monitor["monitored_themes"])
    assert any(item["cluster_id"] for item in theme_candidates["theme_candidates"])
    assert any(item["candidate_stocks"] for item in theme_candidates["theme_candidates"])
    assert any(item["theme_name"] for item in result_cards["structured_result_cards"])
    assert any(item["core_narrative"] for item in result_cards["structured_result_cards"])
    assert warehouse["artifact_batch_dir"]
    assert any(item["theme_heat_score"] >= 0 for item in theme_heat["theme_heat_snapshots"])
    assert any(item["low_position_score"] >= 35 for item in low_position["low_position_opportunities"])
    assert any(item["candidate_stocks"] for item in low_position["low_position_opportunities"])
    assert any(item["theme_name"] for item in feed["fermenting_theme_feed"])
    assert any(item["fermentation_phase"] in {"early", "spreading", "crowded"} for item in feed["fermenting_theme_feed"])
    assert ranking["ranked_events"][0]["relevance_score"] >= ranking["ranked_events"][-1]["relevance_score"]
    assert review["today_focus_page"]
    assert review["low_position_candidates"]
    assert "research" in review["daily_review_report"]["risk_notice"].lower()
