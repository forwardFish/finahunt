from __future__ import annotations

from agents.base import BaseAgent
from agents.helpers import artifact_ref, get_result
from packages.schema.state import GraphState
from packages.utils import load_yaml
from skills.event import detect_themes


class ThemeDetectionAgent(BaseAgent):
    agent_name = "Theme Detection Agent"
    stage = "theme_detection"

    def build_content(self, state: GraphState) -> dict:
        canonical_events = get_result(state, "event_unify").get("canonical_events", [])
        theme_rules = load_yaml("config/rules/standards.yaml").get("theme_rules", {})
        enriched_events: list[dict] = []

        for event in canonical_events:
            content_text = event.get("metadata", {}).get("content_text", "")
            text = f"{event.get('title', '')} {event.get('summary', '')} {content_text}"
            theme_matches = detect_themes(text, theme_rules)
            theme_tags = list(dict.fromkeys([*event.get("related_themes", []), *[match["theme"] for match in theme_matches]]))
            enriched_events.append(
                {
                    **event,
                    "theme_tags": theme_tags,
                    "metadata": {
                        **event.get("metadata", {}),
                        "theme_evidence": theme_matches,
                    },
                }
            )

        return {
            "theme_enriched_events": enriched_events,
            "artifact_refs": [artifact_ref("runtime", "theme_enriched_events.json")],
        }
