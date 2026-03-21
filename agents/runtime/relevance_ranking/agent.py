from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import (
    build_event_theme_timeline,
    build_ranked_result_feed,
    build_relevance_scored_results,
    build_watchlist_asset_linkage,
    rank_events_for_user,
)


class RelevanceRankingAgent(BaseAgent):
    agent_name = "Relevance Ranking Agent"
    stage = "relevance_ranking"

    def build_content(self, state: GraphState) -> dict:
        events = get_result(state, "stock_linkage").get("linked_events", [])
        theme_candidates = get_result(state, "theme_candidate_aggregation").get("theme_candidates", [])
        fermenting_theme_feed = get_result(state, "fermenting_theme_feed").get("fermenting_theme_feed", [])
        theme_heat_snapshots = get_result(state, "theme_heat_snapshot").get("theme_heat_snapshots", [])
        default_profile = load_yaml("config/rules/standards.yaml").get("default_user_profile", {})
        user_profile = {
            **default_profile,
            **get_context(state, "user_profile", {}),
        }
        ranked_events = rank_events_for_user(events, user_profile)
        event_theme_timeline = build_event_theme_timeline(events, theme_candidates)
        watchlist_asset_linkage = build_watchlist_asset_linkage(fermenting_theme_feed, user_profile)
        relevance_scored_results = build_relevance_scored_results(
            fermenting_theme_feed,
            watchlist_asset_linkage,
            user_profile,
            theme_heat_snapshots,
        )
        ranked_result_feed = build_ranked_result_feed(relevance_scored_results)

        persist_runtime_json(
            state,
            stage=self.stage,
            filename="ranked_events.json",
            payload=ranked_events,
            record_count=len(ranked_events),
            summary={"artifact_type": "ranked_events"},
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="event_theme_timeline.json",
            payload=event_theme_timeline,
            record_count=len(event_theme_timeline.get("timeline_entries", [])),
            summary={"artifact_type": "event_theme_timeline"},
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="watchlist_asset_linkage.json",
            payload=watchlist_asset_linkage,
            record_count=len(watchlist_asset_linkage.get("linked_results", [])),
            summary={"artifact_type": "watchlist_asset_linkage"},
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="relevance_scored_results.json",
            payload=relevance_scored_results,
            record_count=len(relevance_scored_results),
            summary={"artifact_type": "relevance_scored_results"},
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="ranked_result_feed.json",
            payload=ranked_result_feed,
            record_count=len(ranked_result_feed),
            summary={"artifact_type": "ranked_result_feed"},
        )
        return {
            "ranked_events": ranked_events,
            "event_theme_timeline": event_theme_timeline,
            "watchlist_asset_linkage": watchlist_asset_linkage,
            "relevance_scored_results": relevance_scored_results,
            "ranked_result_feed": ranked_result_feed,
            "ranking_summary": {
                "ranked_event_count": len(ranked_events),
                "timeline_entry_count": len(event_theme_timeline.get("timeline_entries", [])),
                "watchlist_hit_count": len(watchlist_asset_linkage.get("linked_results", [])),
                "ranked_feed_count": len(ranked_result_feed),
            },
            "user_profile_snapshot": user_profile,
            "artifact_refs": [
                artifact_ref("runtime", state["run_id"], "ranked_events.json"),
                artifact_ref("runtime", state["run_id"], "event_theme_timeline.json"),
                artifact_ref("runtime", state["run_id"], "watchlist_asset_linkage.json"),
                artifact_ref("runtime", state["run_id"], "relevance_scored_results.json"),
                artifact_ref("runtime", state["run_id"], "ranked_result_feed.json"),
            ],
        }
