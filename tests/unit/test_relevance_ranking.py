from skills.event.relevance import (
    build_event_theme_timeline,
    build_ranked_result_feed,
    build_relevance_scored_results,
    build_watchlist_asset_linkage,
)


def test_build_event_theme_timeline_skips_missing_timestamp_and_groups_theme():
    linked_events = [
        {
            "event_id": "event-1",
            "title": "Robot policy update",
            "summary": "Policy support lands.",
            "event_time": "2026-03-18T09:00:00+00:00",
            "theme_tags": ["机器人"],
            "source_refs": ["https://example.com/a"],
            "evidence_refs": ["e1"],
            "linked_assets": [{"asset_type": "stock", "asset_id": "300024.SZ", "asset_name": "机器人样本"}],
            "catalyst_type": "policy",
            "catalyst_strength": "high",
        },
        {
            "event_id": "event-2",
            "title": "Missing time event",
            "summary": "Should not enter timeline.",
            "theme_tags": ["机器人"],
            "source_refs": ["https://example.com/b"],
            "evidence_refs": ["e2"],
        },
    ]
    theme_candidates = [
        {
            "theme_candidate_id": "theme-1",
            "cluster_id": "cluster-1",
            "theme_name": "机器人",
            "core_narrative": "Robot chain is gaining traction.",
            "latest_seen_time": "2026-03-18T10:00:00+00:00",
            "supporting_signals": [{"event_id": "event-1", "event_subject": "机器人"}],
            "source_refs": ["https://example.com/a"],
            "evidence_refs": ["e1"],
            "linked_assets": [{"asset_type": "theme", "asset_id": "机器人", "asset_name": "机器人"}],
        }
    ]

    timeline = build_event_theme_timeline(linked_events, theme_candidates)

    assert len(timeline["timeline_entries"]) == 3
    assert all(entry["event_id"] != "event-2" for entry in timeline["timeline_entries"])
    assert timeline["theme_timelines"][0]["theme_name"] == "机器人"
    assert timeline["timeline_summary"]["theme_count"] == 1


def test_relevance_scoring_and_ranked_feed_prioritize_watchlist_hits():
    feed_items = [
        {
            "theme_candidate_id": "theme-robot",
            "cluster_id": "cluster-robot",
            "theme_name": "机器人",
            "core_narrative": "Robot policy and orders are lining up.",
            "catalyst_summary": "Policy plus industry orders.",
            "fermentation_stage": "emerging",
            "fermentation_phase": "spreading",
            "theme_heat_score": 66.0,
            "top_evidence": [{"title": "Robot support"}],
            "candidate_stocks": [{"stock_code": "300024.SZ", "stock_name": "机器人样本", "candidate_purity_score": 78.0}],
            "linked_assets": [
                {"asset_type": "stock", "asset_id": "300024.SZ", "asset_name": "机器人样本"},
                {"asset_type": "theme", "asset_id": "机器人", "asset_name": "机器人"},
            ],
            "source_refs": ["https://example.com/robot"],
            "risk_notice": "research only",
        },
        {
            "theme_candidate_id": "theme-calc",
            "cluster_id": "cluster-calc",
            "theme_name": "算力",
            "core_narrative": "Compute demand is recovering.",
            "catalyst_summary": "Server demand rise.",
            "fermentation_stage": "watch-only",
            "fermentation_phase": "early",
            "theme_heat_score": 58.0,
            "top_evidence": [{"title": "Compute demand"}],
            "candidate_stocks": [{"stock_code": "000063.SZ", "stock_name": "中兴通讯", "candidate_purity_score": 60.0}],
            "linked_assets": [{"asset_type": "stock", "asset_id": "000063.SZ", "asset_name": "中兴通讯"}],
            "source_refs": ["https://example.com/calc"],
            "risk_notice": "research only",
        },
    ]
    user_profile = {
        "watchlist_symbols": ["300024.SZ"],
        "watchlist_themes": ["机器人"],
        "watchlist_sectors": [],
    }
    theme_heat_snapshots = [
        {
            "theme_candidate_id": "theme-robot",
            "theme_heat_score": 66.0,
            "source_count": 3,
            "high_strength_catalyst_count": 1,
            "fermentation_score": 72.0,
            "latest_event_time": "2099-03-18T10:00:00+00:00",
        },
        {
            "theme_candidate_id": "theme-calc",
            "theme_heat_score": 58.0,
            "source_count": 2,
            "high_strength_catalyst_count": 0,
            "fermentation_score": 51.0,
            "latest_event_time": "2099-03-17T10:00:00+00:00",
        },
    ]

    linkage = build_watchlist_asset_linkage(feed_items, user_profile)
    scored = build_relevance_scored_results(feed_items, linkage, user_profile, theme_heat_snapshots)
    ranked_feed = build_ranked_result_feed(scored)

    assert linkage["watchlist_enabled"] is True
    assert linkage["linked_results"][0]["theme_name"] == "机器人"
    assert scored[0]["relevance_score"] > scored[1]["relevance_score"]
    assert ranked_feed[0]["theme_name"] == "机器人"
    assert ranked_feed[0]["rank_position"] == 1
    assert ranked_feed[0]["watchlist_hit_count"] >= 1
