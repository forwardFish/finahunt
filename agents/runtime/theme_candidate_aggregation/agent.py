from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from skills.event.fermentation import aggregate_theme_candidates


class ThemeCandidateAggregationAgent(BaseAgent):
    agent_name = "Theme Candidate Aggregation Agent"
    stage = "theme_candidate_aggregation"

    def build_content(self, state: GraphState) -> dict:
        linked_events = get_result(state, "stock_linkage").get("linked_events", [])
        theme_candidates = aggregate_theme_candidates(linked_events)
        return {
            "theme_candidates": theme_candidates,
            "aggregation_summary": {
                "linked_event_count": len(linked_events),
                "theme_candidate_count": len(theme_candidates),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "theme_candidates.json")],
        }
