from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import classify_catalyst


class CatalystClassificationAgent(BaseAgent):
    agent_name = "Catalyst Classification Agent"
    stage = "catalyst_classification"

    def build_content(self, state: GraphState) -> dict:
        events = get_result(state, "theme_detection").get("theme_enriched_events", [])
        catalyst_rules = load_yaml("config/rules/standards.yaml").get("catalyst_rules", {})
        enriched_events: list[dict] = []

        for event in events:
            text = f"{event.get('title', '')} {event.get('summary', '')}"
            catalyst = classify_catalyst(text, catalyst_rules, event.get("metadata", {}).get("source_id", "unknown"))
            enriched_events.append(
                {
                    **event,
                    "catalyst_type": catalyst["type"],
                    "catalyst_strength": catalyst["strength"],
                    "metadata": {
                        **event.get("metadata", {}),
                        "catalyst_reason": catalyst["reason"],
                    },
                }
            )

        return {
            "catalyst_events": enriched_events,
            "artifact_refs": [artifact_ref("runtime", "catalyst_events.json")],
        }
