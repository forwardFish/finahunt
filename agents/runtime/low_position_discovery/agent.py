from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event import build_low_position_opportunities


class LowPositionDiscoveryAgent(BaseAgent):
    agent_name = "Low Position Discovery Agent"
    stage = "low_position_discovery"

    def build_content(self, state: GraphState) -> dict:
        theme_heat_snapshots = get_result(state, "theme_heat_snapshot").get("theme_heat_snapshots", [])
        structured_result_cards = get_result(state, "structured_result_cards").get("structured_result_cards", [])
        low_position_opportunities = build_low_position_opportunities(theme_heat_snapshots, structured_result_cards)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="low_position_opportunities.json",
            payload=low_position_opportunities,
            record_count=len(low_position_opportunities),
            summary={"artifact_type": "low_position_opportunities"},
        )
        return {
            "low_position_opportunities": low_position_opportunities,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "low_position_opportunities.json")],
        }
