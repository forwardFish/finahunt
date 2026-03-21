from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_message_reasoning


class ReasoningAgent(BaseAgent):
    agent_name = "Reasoning Agent"
    stage = "reasoning"

    def build_content(self, state: GraphState) -> dict:
        company_candidates = get_result(state, "company_mining").get("message_company_candidates", [])
        impact_analysis = get_result(state, "impact_analysis").get("message_impact_analysis", [])
        reasoning = build_message_reasoning(company_candidates, impact_analysis)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_reasoning.json",
            payload=reasoning,
            record_count=len(reasoning),
            summary={"artifact_type": "message_reasoning"},
        )
        return {
            "message_reasoning": reasoning,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "message_reasoning.json")],
        }
