from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event import (
    build_daily_review,
    build_daily_review_from_theme_feed,
    build_low_position_research_cards,
)


class DailyReviewAgent(BaseAgent):
    agent_name = "Daily Review Agent"
    stage = "daily_review"

    def build_content(self, state: GraphState) -> dict:
        theme_feed = get_result(state, "fermenting_theme_feed").get("fermenting_theme_feed", [])
        low_position_opportunities = get_result(state, "low_position_discovery").get("low_position_opportunities", [])
        similar_theme_cases = get_result(state, "similar_case").get("similar_theme_cases", [])
        if theme_feed:
            review_payload = build_daily_review_from_theme_feed(theme_feed)
        else:
            ranked_events = get_result(state, "relevance_ranking").get("ranked_events", [])
            review_payload = build_daily_review(ranked_events)
        message_workbench = get_result(state, "low_position_orchestrator").get("daily_message_workbench", {})
        theme_workbench = get_result(state, "low_position_orchestrator").get("daily_theme_workbench", {})
        low_position_research_cards = build_low_position_research_cards(low_position_opportunities, similar_theme_cases)
        review_payload["low_position_candidates"] = low_position_opportunities[:5]
        review_payload["low_position_research_cards"] = low_position_research_cards[:10]
        review_payload["message_workbench"] = message_workbench
        review_payload["theme_workbench"] = theme_workbench
        review_payload["similar_case_matches"] = sum(
            1 for item in similar_theme_cases if item.get("matching_status") == "matched"
        )
        review_payload["daily_review_report"]["research_positioning"] = "低位研究卡只用于排序研究观察优先级，不构成交易指令。"
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="daily_review.json",
            payload=review_payload,
            summary={"artifact_type": "daily_review"},
        )
        return {
            **review_payload,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "daily_review.json")],
        }
