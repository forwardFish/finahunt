from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.artifacts import persist_runtime_json
from packages.schema.state import GraphState
from skills.event.fermentation import build_fermenting_theme_feed


class FermentingThemeFeedAgent(BaseAgent):
    agent_name = "Fermenting Theme Feed Agent"
    stage = "fermenting_theme_feed"

    def build_content(self, state: GraphState) -> dict:
        theme_heat_snapshots = get_result(state, "theme_heat_snapshot").get("theme_heat_snapshots", [])
        structured_result_cards = get_result(state, "structured_result_cards").get("structured_result_cards", [])
        fermenting_theme_feed = build_fermenting_theme_feed(theme_heat_snapshots, structured_result_cards)
        persist_runtime_json(
            state,
            stage=self.stage,
            filename="fermenting_theme_feed.json",
            payload=fermenting_theme_feed,
            record_count=len(fermenting_theme_feed),
            summary={"artifact_type": "fermenting_theme_feed"},
        )
        return {
            "fermenting_theme_feed": fermenting_theme_feed,
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "fermenting_theme_feed.json")],
        }
