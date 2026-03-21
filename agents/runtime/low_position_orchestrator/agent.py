from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.message_workbench import (
    build_daily_message_workbench,
    build_daily_theme_workbench,
    build_workbench_stage_statuses,
)


class LowPositionOrchestratorAgent(BaseAgent):
    agent_name = "Low-position Orchestrator Agent"
    stage = "low_position_orchestrator"

    def build_content(self, state: GraphState) -> dict:
        valuable_messages = get_result(state, "message_processing").get("valuable_messages", [])
        message_fermentation_judgements = get_result(state, "fermentation_judgement").get("message_fermentation_judgements", [])
        message_impact_analysis = get_result(state, "impact_analysis").get("message_impact_analysis", [])
        message_reasoning = get_result(state, "reasoning").get("message_reasoning", [])
        message_validation_feedback = get_result(state, "validation_calibration").get("message_validation_feedback", [])
        message_scores = get_result(state, "validation_calibration").get("message_scores", [])
        low_position_opportunities = get_result(state, "low_position_discovery").get("low_position_opportunities", [])
        fermenting_theme_feed = get_result(state, "fermenting_theme_feed").get("fermenting_theme_feed", [])
        daily_message_workbench = build_daily_message_workbench(
            valuable_messages,
            message_fermentation_judgements,
            message_impact_analysis,
            message_reasoning,
            message_validation_feedback,
            message_scores,
            run_id=state["run_id"],
        )
        daily_theme_workbench = build_daily_theme_workbench(
            daily_message_workbench,
            low_position_opportunities,
            fermenting_theme_feed,
            run_id=state["run_id"],
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="daily_message_workbench.json",
            payload=daily_message_workbench,
            summary={"artifact_type": "daily_message_workbench"},
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="daily_theme_workbench.json",
            payload=daily_theme_workbench,
            summary={"artifact_type": "daily_theme_workbench"},
        )
        orchestrator_summary = {
            "run_id": state["run_id"],
            "daily_message_workbench_ref": artifact_ref("runtime", state["run_id"], "daily_message_workbench.json"),
            "daily_theme_workbench_ref": artifact_ref("runtime", state["run_id"], "daily_theme_workbench.json"),
            "workbench_stage_statuses": build_workbench_stage_statuses(state),
        }
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="low_position_orchestrator.json",
            payload=orchestrator_summary,
            summary={"artifact_type": "low_position_orchestrator"},
        )
        return {
            "daily_message_workbench": daily_message_workbench,
            "daily_theme_workbench": daily_theme_workbench,
            "workbench_stage_statuses": orchestrator_summary["workbench_stage_statuses"],
            "artifact_refs": [
                artifact_ref("runtime", state["run_id"], "daily_message_workbench.json"),
                artifact_ref("runtime", state["run_id"], "daily_theme_workbench.json"),
                artifact_ref("runtime", state["run_id"], "low_position_orchestrator.json"),
            ],
        }
