from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import build_message_scores, build_message_validation_feedback


class ValidationCalibrationAgent(BaseAgent):
    agent_name = "Validation & Calibration Agent"
    stage = "validation_calibration"

    def build_content(self, state: GraphState) -> dict:
        valuable_messages = get_result(state, "message_processing").get("valuable_messages", [])
        judgements = get_result(state, "fermentation_judgement").get("message_fermentation_judgements", [])
        impact_analysis = get_result(state, "impact_analysis").get("message_impact_analysis", [])
        company_candidates = get_result(state, "company_mining").get("message_company_candidates", [])
        reasoning = get_result(state, "reasoning").get("message_reasoning", [])
        validation_feedback = build_message_validation_feedback(
            valuable_messages,
            judgements,
            impact_analysis,
            company_candidates,
            reasoning,
        )
        scores = build_message_scores(
            valuable_messages,
            judgements,
            impact_analysis,
            company_candidates,
            reasoning,
            validation_feedback,
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_validation_feedback.json",
            payload=validation_feedback,
            record_count=len(validation_feedback),
            summary={"artifact_type": "message_validation_feedback"},
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="message_scores.json",
            payload=scores,
            record_count=len(scores),
            summary={"artifact_type": "message_scores"},
        )
        return {
            "message_validation_feedback": validation_feedback,
            "message_scores": scores,
            "artifact_refs": [
                artifact_ref("runtime", state["run_id"], "message_validation_feedback.json"),
                artifact_ref("runtime", state["run_id"], "message_scores.json"),
            ],
        }
