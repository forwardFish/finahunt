from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.fermentation import build_theme_heat_snapshots


class ThemeHeatSnapshotAgent(BaseAgent):
    agent_name = "Theme Heat Snapshot Agent"
    stage = "theme_heat_snapshot"

    def build_content(self, state: GraphState) -> dict:
        monitored_themes = get_result(state, "fermentation_monitor").get("monitored_themes", [])
        theme_heat_snapshots = build_theme_heat_snapshots(monitored_themes)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="theme_heat_snapshots.json",
            payload=theme_heat_snapshots,
            record_count=len(theme_heat_snapshots),
            summary={"artifact_type": "theme_heat_snapshots"},
        )
        return {
            "theme_heat_snapshots": theme_heat_snapshots,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "theme_heat_snapshots.json")],
        }
