from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event import build_fermentation_monitors


class FermentationMonitorAgent(BaseAgent):
    agent_name = "Fermentation Monitor Agent"
    stage = "fermentation_monitor"

    def build_content(self, state: GraphState) -> dict:
        theme_candidates = get_result(state, "theme_candidate_aggregation").get("theme_candidates", [])
        monitored_themes = build_fermentation_monitors(theme_candidates)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="fermentation_monitor.json",
            payload=monitored_themes,
            record_count=len(monitored_themes),
            summary={"artifact_type": "fermentation_monitor"},
        )
        return {
            "monitored_themes": monitored_themes,
            "monitor_summary": {
                "theme_candidate_count": len(theme_candidates),
                "monitored_theme_count": len(monitored_themes),
                "spreading_count": sum(1 for item in monitored_themes if item.get("fermentation_phase") == "spreading"),
                "crowded_count": sum(1 for item in monitored_themes if item.get("fermentation_phase") == "crowded"),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "fermentation_monitor.json")],
        }
