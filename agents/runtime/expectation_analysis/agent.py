from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_message_expectations


class ExpectationAnalysisAgent(BaseAgent):
    agent_name = "Expectation Analysis Agent"
    stage = "expectation_analysis"

    def build_content(self, state: GraphState) -> dict:
        valuable_messages = get_result(state, "message_processing").get("valuable_messages", [])
        theme_clusters = get_result(state, "theme_cluster").get("theme_clusters", [])
        theme_heat_snapshots = get_result(state, "theme_heat_snapshot").get("theme_heat_snapshots", [])
        low_position_opportunities = get_result(state, "low_position_discovery").get("low_position_opportunities", [])
        message_expectations = build_message_expectations(
            valuable_messages,
            theme_clusters,
            theme_heat_snapshots,
            low_position_opportunities,
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_expectations.json",
            payload=message_expectations,
            record_count=len(message_expectations),
            summary={"artifact_type": "message_expectations"},
        )
        return {
            "message_expectations": message_expectations,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "message_expectations.json")],
        }
