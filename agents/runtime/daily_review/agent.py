from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from skills.event import build_daily_review


class DailyReviewAgent(BaseAgent):
    agent_name = "Daily Review Agent"
    stage = "daily_review"

    def build_content(self, state: GraphState) -> dict:
        ranked_events = get_result(state, "relevance_ranking").get("ranked_events", [])
        review_payload = build_daily_review(ranked_events)
        return {
            **review_payload,
            "artifact_refs": [artifact_ref("runtime", "daily_review.json")],
        }
