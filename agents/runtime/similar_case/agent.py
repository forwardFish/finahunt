from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event import build_similar_theme_cases


class SimilarCaseAgent(BaseAgent):
    agent_name = "Similar Case Agent"
    stage = "similar_case"

    def build_content(self, state: GraphState) -> dict:
        low_position_opportunities = get_result(state, "low_position_discovery").get("low_position_opportunities", [])
        monitored_themes = get_result(state, "fermentation_monitor").get("monitored_themes", [])
        similar_theme_cases = build_similar_theme_cases(
            low_position_opportunities,
            monitored_themes,
            current_run_id=state["run_id"],
        )
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="similar_theme_cases.json",
            payload=similar_theme_cases,
            record_count=len(similar_theme_cases),
            summary={"artifact_type": "similar_theme_cases"},
        )
        return {
            "similar_theme_cases": similar_theme_cases,
            "similar_case_summary": {
                "theme_count": len(low_position_opportunities),
                "matched_theme_count": sum(1 for item in similar_theme_cases if item.get("matching_status") == "matched"),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "similar_theme_cases.json")],
        }
