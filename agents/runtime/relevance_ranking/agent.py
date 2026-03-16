from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_context, get_result
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import rank_events_for_user


class RelevanceRankingAgent(BaseAgent):
    agent_name = "Relevance Ranking Agent"
    stage = "relevance_ranking"

    def build_content(self, state: GraphState) -> dict:
        events = get_result(state, "stock_linkage").get("linked_events", [])
        default_profile = load_yaml("config/rules/standards.yaml").get("default_user_profile", {})
        user_profile = {
            **default_profile,
            **get_context(state, "user_profile", {}),
        }
        ranked_events = rank_events_for_user(events, user_profile)
        return {
            "ranked_events": ranked_events,
            "user_profile_snapshot": user_profile,
            "artifact_refs": [artifact_ref("runtime", "ranked_events.json")],
        }
