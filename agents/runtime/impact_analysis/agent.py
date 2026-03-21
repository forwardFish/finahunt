from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_message_impact_analysis


class ImpactAnalysisAgent(BaseAgent):
    agent_name = "Impact Analysis Agent"
    stage = "impact_analysis"

    def build_content(self, state: GraphState) -> dict:
        valuable_messages = get_result(state, "message_processing").get("valuable_messages", [])
        judgements = get_result(state, "fermentation_judgement").get("message_fermentation_judgements", [])
        theme_clusters = get_result(state, "theme_cluster").get("theme_clusters", [])
        theme_heat_snapshots = get_result(state, "theme_heat_snapshot").get("theme_heat_snapshots", [])
        low_position_opportunities = get_result(state, "low_position_discovery").get("low_position_opportunities", [])
        analysis = build_message_impact_analysis(
            valuable_messages,
            judgements,
            theme_clusters,
            theme_heat_snapshots,
            low_position_opportunities,
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_impact_analysis.json",
            payload=analysis,
            record_count=len(analysis),
            summary={"artifact_type": "message_impact_analysis"},
        )
        return {
            "message_impact_analysis": analysis,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "message_impact_analysis.json")],
        }
