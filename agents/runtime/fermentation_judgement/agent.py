from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_message_fermentation_judgements


class FermentationJudgementAgent(BaseAgent):
    agent_name = "Fermentation Judgement Agent"
    stage = "fermentation_judgement"

    def build_content(self, state: GraphState) -> dict:
        valuable_messages = get_result(state, "message_processing").get("valuable_messages", [])
        judgements = build_message_fermentation_judgements(valuable_messages)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_fermentation_judgements.json",
            payload=judgements,
            record_count=len(judgements),
            summary={"artifact_type": "message_fermentation_judgements"},
        )
        return {
            "message_fermentation_judgements": judgements,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "message_fermentation_judgements.json")],
        }
