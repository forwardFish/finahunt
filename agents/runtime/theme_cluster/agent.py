from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event import build_theme_clusters


class ThemeClusterAgent(BaseAgent):
    agent_name = "Theme Cluster Agent"
    stage = "theme_cluster"

    def build_content(self, state: GraphState) -> dict:
        linked_events = get_result(state, "stock_linkage").get("linked_events", [])
        theme_clusters = build_theme_clusters(linked_events)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="theme_clusters.json",
            payload=theme_clusters,
            record_count=len(theme_clusters),
            summary={"artifact_type": "theme_clusters"},
        )
        return {
            "theme_clusters": theme_clusters,
            "cluster_summary": {
                "linked_event_count": len(linked_events),
                "theme_cluster_count": len(theme_clusters),
                "new_theme_count": sum(1 for item in theme_clusters if item.get("cluster_state") == "new_theme"),
                "reignited_theme_count": sum(1 for item in theme_clusters if item.get("cluster_state") == "reignited_theme"),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "theme_clusters.json")],
        }
