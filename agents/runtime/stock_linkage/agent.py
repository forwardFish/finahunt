from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from skills.event import build_candidate_stock_links


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
            candidate_stock_links = build_candidate_stock_links({**event, "linked_assets": linked_assets})
            linked_events.append(
                {
                    **event,
                    "linked_assets": linked_assets,
                    "candidate_stock_links": candidate_stock_links,
                }
            )

        return {
            "linked_events": linked_events,
            "artifact_refs": [artifact_ref("runtime", "linked_events.json")],
        }
