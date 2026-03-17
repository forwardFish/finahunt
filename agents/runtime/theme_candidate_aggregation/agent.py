from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from skills.event import build_theme_candidates_from_clusters


class ThemeCandidateAggregationAgent(BaseAgent):
    agent_name = "Theme Candidate Aggregation Agent"
    stage = "theme_candidate_aggregation"

    def build_content(self, state: GraphState) -> dict:
        theme_clusters = get_result(state, "theme_cluster").get("theme_clusters", [])
        theme_candidates = build_theme_candidates_from_clusters(theme_clusters)
        return {
            "theme_candidates": theme_candidates,
            "aggregation_summary": {
                "theme_cluster_count": len(theme_clusters),
                "theme_candidate_count": len(theme_candidates),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "theme_candidates.json")],
        }
