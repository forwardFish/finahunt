from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from skills.event.fermentation import build_structured_result_cards


class StructuredResultCardsAgent(BaseAgent):
    agent_name = "Structured Result Cards Agent"
    stage = "structured_result_cards"

    def build_content(self, state: GraphState) -> dict:
        theme_candidates = get_result(state, "theme_candidate_aggregation").get("theme_candidates", [])
        structured_result_cards = build_structured_result_cards(theme_candidates)
        return {
            "structured_result_cards": structured_result_cards,
            "card_summary": {
                "theme_candidate_count": len(theme_candidates),
                "card_count": len(structured_result_cards),
            },
            "artifact_refs": [artifact_ref("runtime", state["run_id"], "structured_result_cards.json")],
        }
