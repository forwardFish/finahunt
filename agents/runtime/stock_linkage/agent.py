from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState


class StockLinkageAgent(BaseAgent):
    agent_name = "Stock Linkage Agent"
    stage = "stock_linkage"

    def build_content(self, state: GraphState) -> dict:
        events = get_result(state, "catalyst_classification").get("catalyst_events", [])
        linked_events: list[dict] = []

        for event in events:
            linked_assets = list(event.get("linked_assets", []))
            for theme in event.get("theme_tags", []):
                linked_assets.append(
                    {
                        "asset_type": "theme",
                        "asset_id": theme,
                        "asset_name": theme,
                        "relation": "direct",
                    }
                )
            linked_events.append(
                {
                    **event,
                    "linked_assets": linked_assets,
                }
            )

        return {
            "linked_events": linked_events,
            "artifact_refs": [artifact_ref("runtime", "linked_events.json")],
        }
