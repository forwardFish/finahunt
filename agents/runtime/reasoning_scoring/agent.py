from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_message_impact_scores, build_message_reasoning


class ReasoningScoringAgent(BaseAgent):
    agent_name = "Reasoning and Scoring Agent"
    stage = "reasoning_scoring"

    def build_content(self, state: GraphState) -> dict:
        valuable_messages = get_result(state, "message_processing").get("valuable_messages", [])
        message_expectations = get_result(state, "expectation_analysis").get("message_expectations", [])
        message_company_candidates = get_result(state, "company_mining").get("message_company_candidates", [])
        message_reasoning = build_message_reasoning(message_company_candidates, message_expectations)
        message_impact_scores = build_message_impact_scores(
            valuable_messages,
            message_expectations,
            message_company_candidates,
            message_reasoning,
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_reasoning.json",
            payload=message_reasoning,
            record_count=len(message_reasoning),
            summary={"artifact_type": "message_reasoning"},
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_impact_scores.json",
            payload=message_impact_scores,
            record_count=len(message_impact_scores),
            summary={"artifact_type": "message_impact_scores"},
        )
        return {
            "message_reasoning": message_reasoning,
            "message_impact_scores": message_impact_scores,
            "artifact_refs": [
                artifact_ref("runtime", state["run_id"], "message_reasoning.json"),
                artifact_ref("runtime", state["run_id"], "message_impact_scores.json"),
            ],
        }
